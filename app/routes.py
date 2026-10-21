from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename
from .model_service import predict, ModelUnavailable
from .recommendations import get_guidance

bp = Blueprint("main", __name__)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024

@bp.get("/")
def index():
    return render_template("index.html")

@bp.get("/api/health")
def health():
    from pathlib import Path
    model_path = Path(current_app.config["MODEL_PATH"])
    local_present = model_path.is_file()
    return jsonify({
        "status": "ok",
        "inference_ready": local_present,
        "model_file_present": local_present,
        "model_download_on_first_scan": not local_present,
        "model_source": "Hugging Face community model (automatic first-run download)",
        "message": "Local model file found." if local_present else "Ready. The public model will download automatically on the first scan; internet is required."
    })

@bp.post("/api/predict")
def api_predict():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Choose an image file to analyze."}), 400
    file = request.files["image"]
    if not file.filename:
        return jsonify({"success": False, "error": "Choose an image file to analyze."}), 400
    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": "Unsupported file type. Use JPG, PNG, or WebP."}), 415
    # Read one byte beyond the limit to enforce the cap without trusting Content-Length.
    payload = file.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        return jsonify({"success": False, "error": "Image is too large. Maximum upload size is 8 MB."}), 413
    import io
    try:
        result = predict(io.BytesIO(payload), current_app.config["MODEL_PATH"])
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ModelUnavailable as exc:
        return jsonify({"success": False, "error": str(exc), "code": "model_unavailable"}), 503
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "inference_error"}), 500
    guidance = get_guidance(result["prediction"])
    result["guidance"] = guidance
    result["success"] = True
    result["filename"] = filename
    return jsonify(result)

@bp.get("/api/guidance/<category>")
def api_guidance(category):
    return jsonify(get_guidance(category))
