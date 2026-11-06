"""CommunityConnect AI - minimal Flask backend."""

from dotenv import load_dotenv
from flask import Flask, jsonify

# Load variables from .env (Snowflake settings will be used in later stages).
load_dotenv()

app = Flask(__name__)


@app.get("/api/health")
def health():
    """Simple health check to verify the server is running."""
    return jsonify(status="ok", service="CommunityConnect AI backend")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
