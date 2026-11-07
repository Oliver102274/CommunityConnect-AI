
from services.snowflake_service import get_snowflake_connection

try:
    with get_snowflake_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT CURRENT_VERSION()")
            result = cursor.fetchone()
            print("Connected to Snowflake!")
            print("Snowflake version:", result[0])

except Exception as error:
    print("Connection failed:", error)
