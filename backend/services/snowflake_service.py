"""Snowflake data access for CommunityConnect AI.

Retrieval: Snowflake Cortex Search (RESOURCE_SEARCH) with a SQL fallback.
Generation: Snowflake Cortex AI_COMPLETE, grounded only in retrieved rows.
"""

import json
import logging
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

# .env lives in the project root (one level above backend/).
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

log = logging.getLogger(__name__)


def _placeholder(value):
    """True for unset values or untouched .env.example placeholders."""
    return not value or value.startswith("your_")


def _setting(name, default):
    value = os.getenv(name)
    return default if _placeholder(value) else value


DATABASE = _setting("SNOWFLAKE_DATABASE", "COMMUNITYCONNECT_DB")
SCHEMA = _setting("SNOWFLAKE_SCHEMA", "PUBLIC")
RESOURCES_TABLE = f"{DATABASE}.{SCHEMA}.RESOURCES"
SEARCH_SERVICE = f"{DATABASE}.{SCHEMA}.RESOURCE_SEARCH"
AI_MODEL = _setting("CORTEX_MODEL", "llama3.3-70b")

SERVICE_AREA = "Miami-Dade County"
MAX_RESULTS = 6

# Frontend category value <-> Snowflake CATEGORY value
CATEGORY_TO_DB = {
    "veterans": "Veteran Support",
    "food": "Food Assistance",
    "employment": "Employment",
}
DB_TO_CATEGORY = {v: k for k, v in CATEGORY_TO_DB.items()}

RESULT_COLUMNS = ["NAME", "CATEGORY", "DESCRIPTION", "CITY", "PHONE", "WEBSITE"]


# ----------------------------------------
# CONNECTION
# ----------------------------------------

def get_snowflake_connection():
    """Open a Snowflake connection.

    Preferred: SNOWFLAKE_CONNECTION_NAME, a named connection from
    ~/.snowflake/connections.toml (keeps credentials out of the project).
    Fallback: SNOWFLAKE_ACCOUNT / USER / PASSWORD (+ optional AUTHENTICATOR).
    """
    common = {
        "warehouse": None if _placeholder(os.getenv("SNOWFLAKE_WAREHOUSE")) else os.getenv("SNOWFLAKE_WAREHOUSE"),
        "role": None if _placeholder(os.getenv("SNOWFLAKE_ROLE")) else os.getenv("SNOWFLAKE_ROLE"),
        "login_timeout": 60,
        "enable_server_session_keep_alive_auto_detection": False,
    }
    common = {k: v for k, v in common.items() if v is not None}

    connection_name = os.getenv("SNOWFLAKE_CONNECTION_NAME")
    if connection_name:
        return snowflake.connector.connect(connection_name=connection_name, **common)

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing = [name for name in required if _placeholder(os.getenv(name))]
    if missing:
        raise RuntimeError(
            "Snowflake is not configured. Set SNOWFLAKE_CONNECTION_NAME or "
            + ", ".join(missing) + " in .env"
        )

    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        authenticator="snowflake" if _placeholder(authenticator) else authenticator,
        **common,
    )


# ----------------------------------------
# RETRIEVAL
# ----------------------------------------

def _to_resource(row):
    """Convert a Snowflake row dict to the frontend resource format."""
    return {
        "name": row.get("NAME"),
        "category": DB_TO_CATEGORY.get(row.get("CATEGORY"), row.get("CATEGORY")),
        "description": row.get("DESCRIPTION"),
        "location": row.get("CITY"),
        "phone": row.get("PHONE"),
        "website": row.get("WEBSITE"),
    }


def _search_filter(category):
    area = {"@eq": {"SERVICE_AREA": SERVICE_AREA}}
    if category not in CATEGORY_TO_DB:
        return area
    db_value = CATEGORY_TO_DB[category]
    return {
        "@and": [
            area,
            {"@or": [
                {"@eq": {"CATEGORY": db_value}},
                {"@eq": {"SECONDARY_CATEGORY": db_value}},
            ]},
        ]
    }


def cortex_search(cursor, message, category, limit=MAX_RESULTS):
    """Retrieve relevant resources with Snowflake Cortex Search."""
    request = {
        "query": message,
        "columns": RESULT_COLUMNS,
        "filter": _search_filter(category),
        "limit": limit,
    }
    cursor.execute(
        "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(%s, %s)",
        (SEARCH_SERVICE, json.dumps(request)),
    )
    row = cursor.fetchone()
    results = json.loads(row[0]).get("results", []) if row and row[0] else []
    return [_to_resource(r) for r in results]


def sql_search(cursor, category, limit=MAX_RESULTS):
    """Fallback retrieval with parameterized SQL (no ranking)."""
    query = (
        f"SELECT NAME, CATEGORY, DESCRIPTION, CITY, PHONE, WEBSITE FROM {RESOURCES_TABLE} "
        "WHERE IS_DEMO = FALSE AND SERVICE_AREA = %s"
    )
    params = [SERVICE_AREA]
    if category in CATEGORY_TO_DB:
        query += " AND (CATEGORY = %s OR SECONDARY_CATEGORY = %s)"
        params += [CATEGORY_TO_DB[category]] * 2
    query += " ORDER BY ID LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    columns = [c[0] for c in cursor.description]
    return [_to_resource(dict(zip(columns, r))) for r in cursor.fetchall()]


def retrieve_resources(cursor, message, category):
    """Cortex Search first; SQL only if the search service is unavailable.

    Returns (resources, retrieval_method).
    """
    try:
        return cortex_search(cursor, message, category), "cortex_search"
    except Exception:
        log.exception("Cortex Search failed; falling back to SQL retrieval")
        return sql_search(cursor, category), "sql_fallback"


# ----------------------------------------
# GENERATION
# ----------------------------------------

def generate_ai_response(cursor, message, resources):
    """Generate a reply with Cortex AI_COMPLETE, grounded in `resources`."""
    context = [
        {
            "name": r["name"],
            "category": r["category"],
            "description": r["description"],
            "location": r["location"],
        }
        for r in resources
    ]

    prompt = f"""You are CommunityConnect AI, a friendly assistant that helps people in Miami-Dade County find community assistance programs.

RULES:
- Recommend ONLY organizations listed in RESOURCE DATA. Never invent organizations.
- Do NOT write phone numbers, addresses, websites, eligibility rules, or hours. The user sees verified contact details on resource cards below your reply.
- Do not claim a service is offered unless the description supports it.
- Do not claim an organization is near the user.
- If the user has several needs (for example veteran support, a job, and food), address each need with the matching organizations.
- If no listed organization fits a need, say so honestly.
- Keep the reply under 150 words, plain text, no markdown.

RESOURCE DATA (JSON):
{json.dumps(context, ensure_ascii=False)}

USER MESSAGE:
{message}
"""

    cursor.execute("SELECT AI_COMPLETE(%s, %s)", (AI_MODEL, prompt))
    row = cursor.fetchone()
    reply = row[0].strip() if row and row[0] else ""
    # AI_COMPLETE may return a JSON-quoted string.
    if reply.startswith('"') and reply.endswith('"'):
        try:
            reply = json.loads(reply)
        except ValueError:
            pass
    return reply


# ----------------------------------------
# REQUEST PIPELINE (one connection per request)
# ----------------------------------------

def answer_question(message, category):
    """Retrieve resources and generate a grounded reply using one connection.

    Raises on Snowflake connection/retrieval failure (the caller returns an
    error; no fictional fallback data is ever used).
    """
    connection = get_snowflake_connection()
    try:
        with connection.cursor() as cursor:
            resources, retrieval = retrieve_resources(cursor, message, category)

            if not resources:
                return {
                    "reply": (
                        "I couldn't find matching resources in our Miami-Dade database for that request. "
                        "Try another category or describe your need differently."
                    ),
                    "resources": [],
                    "source": {"retrieval": retrieval, "generation": None},
                }

            try:
                reply = generate_ai_response(cursor, message, resources)
                generation = AI_MODEL if reply else None
            except Exception:
                log.exception("Cortex AI_COMPLETE failed")
                reply, generation = "", None

            if not reply:
                reply = "I found some community resources that may help. Please review the organizations below."

            return {
                "reply": reply,
                "resources": resources,
                "source": {"retrieval": retrieval, "generation": generation},
            }
    finally:
        connection.close()
