from flask import Flask, jsonify
from pathlib import Path
from werkzeug.exceptions import RequestEntityTooLarge
import os
from .routes import bp

def _load_local_env():
    """Load simple KEY=VALUE entries from project .env without extra dependencies."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\\\"'")
        if key and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)

_load_local_env()

def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        MODEL_PATH=str(Path(os.getenv(
            "ECOCYCLE_MODEL_PATH",
            Path(__file__).resolve().parent.parent / "models" / "ewaste_mobilenet.keras"
        )).expanduser().resolve()),
    )
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(bp)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_error):
        return jsonify({
            "success": False,
            "error": "Upload is too large. Maximum request size is 8 MB."
        }), 413

    return app
