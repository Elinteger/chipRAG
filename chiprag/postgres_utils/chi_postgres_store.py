"""
Collection of functions to send data to and get data from a PostgreSQL database in the context of this 
somewhat unconventional RAG pipeline.
"""
import pandas as pd
import yaml
from config.load_config import settings
from psycopg2 import DatabaseError, ProgrammingError
from psycopg2.extras import execute_values
from .util_postgres_store import establish_connection


def upload_dataframe(
    df: pd.DataFrame
) -> None:
    """
    Uploads a given DataFrame using a query to a postgreSQL Database. This function is tailored to a 
    Pandas DataFrame with the columns [pesticide, text].

    Args:
        df (pd.DataFrame): The Pandas DataFrame which is to be uploaded.
        conn (psycopg2 Connection Object): Connection Object to perform actions with the database.
        close_conn_afterwards (bool): Variable to decide whether to close the Connection Object after use. Defaults to True.
    """
    ## faulty argument handling
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"'df' must be a pd.DataFrame, got {type(df).__name__}")
    
    ## upload DataFrame
    # load SQL-queries
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_chinese_query"]

    # connect to database
    conn, cur = establish_connection()

    # turn dataframe into list, dataframe must have the two specified columns!
    data = [(row['pesticide'], row['text'], row['version']) for _, row in df.iterrows()]

    # run SQL with data on database
    try:
        execute_values(cur, insert_query, data)
        conn.commit()
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


def query_database(
    keywords: list[str],
) -> list[str]:
    '''
    Queries the database using the provided Connection object.  
    Performs a fuzzy word match for single keywords and an exact 'ILIKE' match for keyphrases.

    Args:
        user_prompt (str): Keywords given by the user, split by ';'. This is not enforced by code, but is a requirement.
        conn (Psycopg2 Connection Object): Connection Object to perform actions with the database.
        close_conn_afterwards (bool): Variable to decide whether to close the Connection Object after use. Defaults to True.

    Returns:
        list[str]: List of all rows matching the SQL-query.
    '''
    ## faulty argument handling
    if not isinstance(keywords, list):
        raise TypeError(f"'keywords' must be a list of strings, got {type(keywords).__name__}")

    ## querying
    # load SQL-queries
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    get_query = queries["multiple_query"]

    conn, cur = establish_connection()
   
    # fuzzy text search
    fuzzy_res = []
    try:
        for keyword in keywords:
            if len(keyword) == 0:
                continue
            try:
                cur.execute(get_query, (f"%{keyword}%",))
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
            results = cur.fetchall()
            fuzzy_res.extend([row + (keyword,) for row in results])
    finally:
        cur.close()
        conn.close()
    
    return fuzzy_res
