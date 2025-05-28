"""
Utility functions for PostgreSQL in Python, including connecting to the database and querying data.
"""
import psycopg2
from config.load_config import settings
from psycopg2 import OperationalError, DatabaseError, ProgrammingError


def establish_connection() -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    """
    Establishes a connection with a configured PostgreSQL database. 

    Returns:
        psycopg2.extensions.connection: A psycopg2 connection object.
        psycopg2.extensions.cursor: A psycopg2 cursor object.
    """ 
    try:
        conn = psycopg2.connect(
            host=settings.postgre_host,
            database=settings.postgre_database_name,
            user=settings.postgre_username,
            password=settings.postgre_password,
            port=settings.postgre_port
        )
    except OperationalError as e:
        print(f"operational error while trying to connect to postgre database: {e}")
        raise
    except Exception as e:
        print(f"unexpected error: {e}")
        raise
    
    cur = conn.cursor()

    return conn, cur


def get_data(
        query: str
) -> list:
    """
    Executes a simple SQL query without additional parameters.

    Args:
        query (str): The SQL query to execute.

    Returns:
        list: Results returned by the query.
    """
    conn, cur = establish_connection()

    try: 
        cur.execute(query)
        conn.commit()
        res = cur.fetchall()
        return res
    except DatabaseError as e:
        print(f"database error while trying to run SQL on postgre database: {e}")
        conn.rollback()
        raise
    except ProgrammingError as e:
        print(f"programming error while trying to run SQL on postgre database: {e}")
        conn.rollback()
        raise
    except Exception as e:
        print(f"unexpected error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
