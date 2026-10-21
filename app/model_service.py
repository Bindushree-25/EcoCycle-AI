"""E-waste image inference with first-run download of a public community model.

The downloaded model is third-party work. Its exact class order and preprocessing are
checked at runtime for shape compatibility; prediction quality is not independently
validated by this application.
"""
import os
import shutil
from pathlib import Path
from threading import Lock

import numpy as np
from PIL import Image, UnidentifiedImageError

CLASS_LABELS = [
    "Battery", "Keyboard", "Microwave", "Mobile", "Mouse",
    "PCB", "Player", "Printer", "Television", "Washing Machine"
]
MODEL_REPO_ID = os.getenv("ECOCYCLE_HF_MODEL", "sanchita144/e-waste-mobilenetv2")
MODEL_FILENAME = "ewaste_mobilenet.keras"
_model = None
_model_path = None
_lock = Lock()

class ModelUnavailable(RuntimeError):
    pass

def _configured_path(model_path=None):
    if model_path:
        path = Path(model_path).expanduser()
        # The default path is eligible for auto-download. An explicitly configured
        # non-default path is treated as an intentional local-model override.
        default = Path(__file__).resolve().parent.parent / "models" / "ewaste_mobilenet.h5"
        if path.resolve() != default.resolve():
            return path
        return Path(__file__).resolve().parent.parent / "models" / MODEL_FILENAME
    override = os.getenv("ECOCYCLE_MODEL_PATH")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parent.parent / "models" / MODEL_FILENAME

def _download_public_model(destination: Path) -> Path:
    """Fetch a public 10-class Keras artifact automatically; no API key is required."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    cache_dir = destination.parent / "hf_model_cache"
    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id=MODEL_REPO_ID,
            filename="e_waste_mobilenetv2.keras",
            repo_type="model",
            local_dir=cache_dir,
        )
        downloaded_path = Path(downloaded)
        if not downloaded_path.is_file() or downloaded_path.stat().st_size < 1_000_000:
            raise RuntimeError("The downloaded model artifact is missing or unexpectedly small.")
        shutil.copy2(downloaded_path, destination)
        return destination
    except Exception as exc:
        raise ModelUnavailable(
            "EcoCycle could not download its public e-waste model automatically. "
            "Check your internet connection and try again. No prediction was fabricated. "
            f"Model source: https://huggingface.co/{MODEL_REPO_ID}. Details: {type(exc).__name__}."
        ) from exc

def load_model(model_path=None):
    global _model, _model_path
    path = _configured_path(model_path)
    with _lock:
        if _model is not None and _model_path == str(path.resolve()):
            return _model
        if not path.is_file():
            # An explicit custom model path must never silently fall back to another model.
            explicit_override = bool(os.getenv("ECOCYCLE_MODEL_PATH")) or (
                model_path and Path(model_path).name not in {"ewaste_mobilenet.h5", MODEL_FILENAME}
            )
            if explicit_override:
                raise ModelUnavailable(f"Configured model file was not found: {path}")
            path = _download_public_model(path)
        try:
            os.environ.setdefault("KERAS_BACKEND", "tensorflow")
            import keras
            candidate = keras.saving.load_model(str(path), compile=False)
        except Exception as exc:
            raise ModelUnavailable(
                "The model file was downloaded, but this Python/TensorFlow/Keras setup could not load it. "
                "Use Python 3.11 and reinstall the packaged requirements. "
                f"Details: {type(exc).__name__}."
            ) from exc
        try:
            output_shape = candidate.output_shape
            output_count = int(output_shape[-1])
        except Exception as exc:
            raise ModelUnavailable("The downloaded model does not expose a compatible classification output.") from exc
        if output_count != len(CLASS_LABELS):
            raise ModelUnavailable(
                f"The downloaded model returns {output_count} outputs, but this app expects {len(CLASS_LABELS)} labels. "
                "The model and label mapping must be reconciled before predictions can be used."
            )
        _model, _model_path = candidate, str(path.resolve())
        return _model

def preprocess_image(file_stream):
    try:
        image = Image.open(file_stream)
        image.verify()
        file_stream.seek(0)
        image = Image.open(file_stream).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc
    if image.width < 32 or image.height < 32:
        raise ValueError("Image is too small. Upload an image at least 32 × 32 pixels.")
    if image.width > 6000 or image.height > 6000:
        raise ValueError("Image dimensions are too large. Maximum dimension is 6000 pixels.")
    image = image.resize((224, 224))
    array = np.asarray(image, dtype=np.float32)
    # The public model is named MobileNetV2; scale to [-1, 1], the standard MobileNetV2 convention.
    return (array / 127.5 - 1.0)[None, ...]

def predict(file_stream, model_path=None):
    model = load_model(model_path)
    batch = preprocess_image(file_stream)
    try:
        scores = np.asarray(model.predict(batch, verbose=0)).reshape(-1)
    except Exception as exc:
        raise RuntimeError("The model failed during inference.") from exc
    if len(scores) != len(CLASS_LABELS):
        raise RuntimeError(f"Model output has {len(scores)} classes; expected {len(CLASS_LABELS)}.")
    if not np.all(np.isfinite(scores)):
        raise RuntimeError("The model returned invalid scores.")
    if np.any(scores < 0) or not np.isclose(float(scores.sum()), 1.0, atol=0.05):
        exp = np.exp(scores - np.max(scores))
        scores = exp / exp.sum()
    else:
        scores = scores / max(float(scores.sum()), 1e-12)
    order = np.argsort(scores)[::-1][:3]
    idx = int(order[0])
    confidence = float(scores[idx])
    return {
        "prediction": CLASS_LABELS[idx],
        "confidence": round(confidence, 4),
        "low_confidence": confidence < 0.55,
        "top_k": [{"label": CLASS_LABELS[int(i)], "confidence": round(float(scores[i]), 4)} for i in order],
        "model_source": f"Hugging Face: {MODEL_REPO_ID}",
        "model_limitations": "Community model with no published model card. Class order and accuracy have not been independently validated in this app. Treat results as provisional and confirm the item manually."
    }
