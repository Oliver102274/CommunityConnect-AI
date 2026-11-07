"""CommunityConnect AI - Flask backend (Snowflake Cortex Search + Cortex AI).

Serves the frontend and the API from one origin:
    http://127.0.0.1:5050/?mode=live
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Load .env from the project root before importing the Snowflake service.
load_dotenv(BASE_DIR.parent / ".env")

from services.snowflake_service import answer_question  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

VALID_CATEGORIES = {"veterans", "food", "employment"}
MAX_MESSAGE_LENGTH = 1000


# ----------------------------------------
# FRONTEND
# ----------------------------------------

@app.get("/")
def index():
    """Serve the frontend homepage."""
    return send_from_directory(FRONTEND_DIR, "index.html")


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
    return send_from_directory(FRONTEND_DIR, "index.html"), 404


# ----------------------------------------
# RUN FLASK SERVER
# ----------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
