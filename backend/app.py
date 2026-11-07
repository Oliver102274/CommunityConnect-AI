


"""CommunityConnect AI - Flask Backend with Snowflake Cortex AI."""

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from services.snowflake_service import (
    get_resources,
    generate_ai_response
)


# ----------------------------------------
# CONFIGURATION
# ----------------------------------------

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Load Snowflake credentials
load_dotenv(BASE_DIR / ".env")

# Initialize Flask and serve frontend files
app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

VALID_CATEGORIES = {"veterans", "food", "employment"}


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

    return jsonify({
        "status": "ok",
        "service": "CommunityConnect AI backend"
    }), 200


# ----------------------------------------
# CHATBOT API - SNOWFLAKE + CORTEX AI
# ----------------------------------------

@app.post("/api/chat")
def chat():
    """Process chatbot requests using Snowflake Cortex AI."""

    # Read request from frontend
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A valid JSON object is required."
        }), 400

    message = data.get("message")
    category = data.get("category")
    location = data.get("location")

    # Validate message
    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "A message is required."
        }), 400

    # Validate category
    if category is not None and category not in VALID_CATEGORIES:
        return jsonify({
            "error": "Invalid category."
        }), 400

    # Validate location
    if location is not None and not isinstance(location, str):
        return jsonify({
            "error": "Invalid location."
        }), 400

    # ----------------------------------------
    # GET RESOURCES FROM SNOWFLAKE
    # ----------------------------------------

    try:
        resources = get_resources(category)

    except Exception:
        app.logger.exception("Snowflake resource lookup failed")

        return jsonify({
            "error": "Unable to retrieve community resources."
        }), 503

    # Exclude fictional test organization
    resources = [
        resource for resource in resources
        if resource.get("name") != "Demo Community Food Center"
    ]

    # ----------------------------------------
    # GENERATE AI RESPONSE WITH CORTEX
    # ----------------------------------------

    if resources:
        try:
            reply = generate_ai_response(
                message,
                resources
            )

        except Exception:
            app.logger.exception("Snowflake Cortex AI failed")

            reply = (
                "I found some community resources that may "
                "help you. Please review the organizations below."
            )

    else:
        reply = (
            "I couldn't find verified matching resources "
            "in our database yet. Please try another category."
        )

    # ----------------------------------------
    # RETURN RESPONSE TO FRONTEND
    # ----------------------------------------

    return jsonify({
        "reply": reply,
        "resources": resources
    }), 200


# ----------------------------------------
# RUN FLASK SERVER
# ----------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5050,
        debug=True
    )

