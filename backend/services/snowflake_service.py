

import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv


# ----------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ----------------------------------------

# Locate the .env file inside backend/
env_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(env_path, override=True)


# ----------------------------------------
# SNOWFLAKE CONNECTION
# ----------------------------------------

def get_snowflake_connection():
    """
    Create a connection to Snowflake using
    credentials stored in the .env file.
    """

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        authenticator="snowflake",
        login_timeout=30,
        enable_server_session_keep_alive_auto_detection=False
    )


# ----------------------------------------
# GET COMMUNITY RESOURCES
# ----------------------------------------

def get_resources(category=None):
    """
    Retrieve community resources from Snowflake.

    category can be:
    - veterans
    - food
    - employment
    - None (all categories)
    """

    connection = get_snowflake_connection()
    cursor = None

    # Map frontend categories to Snowflake values
    category_mapping = {
        "veterans": "Veteran Support",
        "food": "Food Assistance",
        "employment": "Employment"
    }

    # Convert Snowflake categories to frontend values
    reverse_category_mapping = {
        value: key
        for key, value in category_mapping.items()
    }

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                NAME,
                CATEGORY,
                DESCRIPTION,
                CITY,
                PHONE,
                WEBSITE
            FROM COMMUNITYCONNECT_DB.PUBLIC.RESOURCES
        """

        # Filter by category if one was selected
        if category in category_mapping:
            query += " WHERE CATEGORY = %s"

            cursor.execute(
                query,
                (category_mapping[category],)
            )

        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        resources = []

        # Convert SQL rows into dictionaries
        for row in rows:

            resource = {
                "name": row[0],
                "category": reverse_category_mapping.get(
                    row[1], row[1]
                ),
                "description": row[2],
                "location": row[3],
                "phone": row[4],
                "website": row[5]
            }

            resources.append(resource)

        return resources

    finally:
        # Close cursor and database connection
        if cursor is not None:
            cursor.close()

        connection.close()

    
import json


def generate_ai_response(message, resources):
    """
    Generate an AI response grounded in Snowflake resources.
    """

    if not resources:
        return (
            "I couldn't find verified matching resources "
            "in our database. Please try another category."
        )

    # Convert resources into JSON for the AI model
    resources_json = json.dumps(
        resources,
        ensure_ascii=False
    )

    prompt = f"""
You are CommunityConnect AI, a helpful community resource assistant.

Your task is to help users find support services.

IMPORTANT RULES:
- Only recommend organizations provided in the RESOURCE DATA.
- Never invent organizations, addresses, phone numbers, or websites.
- Do not claim an organization offers a service unless the data supports it.
- Keep your response friendly, concise, and helpful.
- Do not include fictional or demo organizations.
- If information is missing, explain that it is unavailable.

RESOURCE DATA:
{resources_json}

USER QUESTION:
{message}

Provide a helpful answer based only on the resources above.
"""

    connection = get_snowflake_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            SELECT AI_COMPLETE(
                'llama3.3-70b',
                %s
            )
        """

        cursor.execute(query, (prompt,))

        result = cursor.fetchone()

        if result and result[0]:
            return result[0]

        return "I couldn't generate a response at this time."

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

