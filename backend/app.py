"""CommunityConnect AI - Flask backend (Snowflake Cortex Search + Cortex AI).

Serves the frontend and the API from one origin:
    http://127.0.0.1:5050/?mode=live
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from markupsafe import escape
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Load .env from the project root before importing the Snowflake service.
load_dotenv(BASE_DIR.parent / ".env")

from services.snowflake_service import answer_question  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
# Trust one proxy hop (Render, etc.) so request.host_url reports https.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Public origin used in link-preview metadata, e.g. https://communityconnect-ai.onrender.com
PUBLIC_SITE_URL = (os.getenv("PUBLIC_SITE_URL") or "").rstrip("/")

VALID_CATEGORIES = {"veterans", "food", "employment"}
MAX_MESSAGE_LENGTH = 1000


# ----------------------------------------
# FRONTEND
# ----------------------------------------

@app.get("/")
def index():
    """Serve the homepage with absolute URLs filled into link-preview tags."""
    site_url = PUBLIC_SITE_URL or request.host_url.rstrip("/")
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace("__SITE_URL__", str(escape(site_url)))
    return Response(html, mimetype="text/html")


# ----------------------------------------
# HEALTH CHECK
# ----------------------------------------

@app.get("/api/health")
def health():
    """Verify that Flask is running."""
    return jsonify({"status": "ok", "service": "CommunityConnect AI backend"}), 200


# ----------------------------------------
# CHATBOT API
# ----------------------------------------

@app.post("/api/chat")
def chat():
    """Answer a user question with Cortex Search + Cortex AI."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON object is required."}), 400

    message = data.get("message")
    category = data.get("category")
    location = data.get("location")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "A message is required."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer."}), 400
    if category is not None and category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category."}), 400
    if location is not None and not isinstance(location, str):
        return jsonify({"error": "Invalid location."}), 400

    try:
        result = answer_question(message.strip(), category)
    except Exception:
        app.logger.exception("Snowflake request failed")
        return jsonify({"error": "Unable to retrieve community resources right now."}), 503

    return jsonify(result), 200


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return index(), 404


# ----------------------------------------
# RUN FLASK SERVER (local development)
# Production: gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT
# ----------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=False)
