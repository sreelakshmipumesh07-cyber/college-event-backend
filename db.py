import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def get_connection():
    """Return a new MySQL connection using DB_CONFIG."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"MySQL connection failed: {e}")


def query_db(sql, params=None, fetchone=False, commit=False):
    """
    Execute a SQL statement and return results.

    Args:
        sql      : SQL query string (use %s placeholders).
        params   : Tuple of query parameters.
        fetchone : If True, return a single row dict; else a list of dicts.
        commit   : If True, commit the transaction (INSERT/UPDATE/DELETE).

    Returns:
        dict | list[dict] | int (lastrowid on INSERT/UPDATE)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if commit:
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        if fetchone:
            return cursor.fetchone()
        return cursor.fetchall()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
