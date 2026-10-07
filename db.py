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

def query_db(query, params=None, fetch=True, fetchone=False):

    connection = get_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:

        # Execute query
        cursor.execute(
            query,
            params or ()
        )

        # ---------------------------------------------
        # SELECT ONE ROW
        # ---------------------------------------------

        if fetchone:

            result = cursor.fetchone()

            return result

        # ---------------------------------------------
        # SELECT MULTIPLE ROWS
        # ---------------------------------------------

        if fetch:

            result = cursor.fetchall()

            return result

        # ---------------------------------------------
        # INSERT / UPDATE / DELETE
        # ---------------------------------------------

        connection.commit()

        return True

    except mysql.connector.Error as err:

        print("Database query error:", err)

        connection.rollback()

        return None

    finally:

        cursor.close()
        connection.close()