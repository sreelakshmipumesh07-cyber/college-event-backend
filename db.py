
import mysql.connector
from config import DB_CONFIG


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"]
        )

        return connection

    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None


# ---------------------------------------------------------
# DATABASE QUERY
# ---------------------------------------------------------

def query_db(
    query,
    params=None,
    fetch=True,
    fetchone=False,
    commit=False
):
    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, params or ())

        # SELECT queries return rows
        if cursor.with_rows:

            if fetchone:
                return cursor.fetchone()

            if fetch:
                return cursor.fetchall()

            return True

        # INSERT, UPDATE and DELETE queries
        connection.commit()

        # Return the new ID for INSERT queries
        if cursor.lastrowid:
            return cursor.lastrowid

        return True

    except mysql.connector.Error as err:
        print("Database query error:", err)

        connection.rollback()
        return None

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()
