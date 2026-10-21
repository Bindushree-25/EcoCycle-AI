# Original source audit

Archive inspected: `eco(3).zip` (user-provided; preserved outside this rebuilt package).

## Archive inventory
- 3,228 ZIP entries; approximately 61.1 MB uncompressed and 17.3 MiB compressed.
- Root application files included `index.html`, `ai-sorter.html`, `analyze.html`, `result.html`, `dashboard.php`, login/register/logout pages, `style.css`, `script.js`, `chat_api.py`, and `responses.json`.
- PHP backend included `config.php`, `login.php`, `register.php`, `predict.php`, and `process.php`.
- An embedded Windows virtual environment under `backend/venv310/` accounted for the vast majority of entries and included interpreter binaries, TensorFlow packages, native libraries, caches, and distribution metadata.
- A logo asset was present under `images/logo.png`.

## Findings
- The original `index.html` referenced a remote Lottie animation; the release no longer depends on that external animation.
- `analyze.html` called `http://127.0.0.1:5000/predict`, but no working prediction server was included in the root application files.
- `backend/predict.php` and `backend/process.php` were empty.
- The original PHP registration query interpolated form fields into SQL, and login query interpolated email into SQL. The PHP auth workflow was not carried forward because the new release uses a local-first, no-account architecture and does not need to collect account data.
- `backend/config.php` assumed the default local MySQL root account and an `e_waste_db` database.
- `chat_api.py` was a small canned-response service rather than an LLM integration.
- No trained model file (`.h5`, `.keras`, ONNX, SavedModel, or TFLite) or dataset files were present outside the bundled environment. Therefore model weights and training data could not be preserved from this ZIP.
- `This PC - Shortcut.lnk`, caches, and the bundled machine-specific virtual environment were not included in the release.

## Rebuild decisions
The useful product concept and intended ten-category classification workflow were retained. The disconnected PHP account/database scaffolding and canned chatbot were replaced by a coherent Flask API and a focused client-side experience. The trained model integration is modular but deliberately reports unavailable until a compatible model is supplied. No model metrics or fake inference results are included.
