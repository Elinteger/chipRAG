"""
Collection of functions to send data to and get data from a PostgreSQL database in the context of this 
somewhat unconventional RAG pipeline.
"""
import pandas as pd
import psycopg2
import yaml
from config.load_config import settings
from psycopg2 import OperationalError, DatabaseError, ProgrammingError
from psycopg2.extras import execute_values

def establish_connection() -> psycopg2.extensions.connection:
    """
    Establishes a connection with a configured PostgreSQL database. 

    Returns:
        psycopg2.extensions.connection: A psycopg2 connection object.
    """ 
    ## connect to database
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
    
    return conn


def upload_dataframe(
    df: pd.DataFrame,
    conn: psycopg2.extensions.connection,
    close_conn_afterwards: bool = True
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
    if not isinstance(close_conn_afterwards, bool):
        raise TypeError(f"'close_conn_afterwards' must be a bool, got {type(close_conn_afterwards).__name__}")
    if conn == None:
        raise ValueError(f"conn is 'None', connecting to Database either failed or hasn't been performed")
    
    ## upload DataFrame
    # load SQL-queries
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_chinese_query"]

    # create cursor from connection object
    cur = conn.cursor()

    # turn dataframe into list, dataframe must have the two specified columns!
    data = [(row['pesticide'], row['text']) for _, row in df.iterrows()]

    # run SQL with data on database
    try:
        execute_values(cur, insert_query, data)
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

    conn.commit()

    cur.close()
    if close_conn_afterwards:
        conn.close()


def query_database(
    user_prompt: str,
    conn: psycopg2.extensions.connection,
    close_conn_afterwards: bool = True
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
    #FIXME: |-| validate that user input is properly as expected: "citrus; zoxamide; pumpkin seeds" -> use AxonIvy?
    if not isinstance(user_prompt, str):
        raise TypeError(f"'user_prompt' must be a string, got {type(user_prompt).__name__}")
    if not isinstance(close_conn_afterwards, bool):
        raise TypeError(f"'close_conn_afterwards' must be a bool, got {type(close_conn_afterwards).__name__}")
    if conn == None:
        raise ValueError(f"conn is 'None', connecting to Database either failed or hasn't been performed")

    ## querying
    # load SQL-queries
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    fuzzy_single_query = queries["fuzzy_single_query"]
    multiple_query = queries["multiple_query"]

    # create cursor from connection object
    cur = conn.cursor()

    # split user input to get keywords to look for
    keywords = [item.strip() for item in user_prompt.split(';')]
    
    # fuzzy text search
    #FIXME: |-| -> CREATE EXTENSION pg_trgm; in postgresql database!
    fuzzy_res = []
    is_phrase = False
    for keyword in keywords:
        if len(keyword) == 0:
            continue
        # if keyword is a single word, do a fuzzy word by word match
        if len(keyword.split()) == 1:
            sql_query = fuzzy_single_query
            is_phrase = False 
        # if keyword is a keyphrase, do an exact case-insensitive keyphrase match 
        else:
            sql_query = multiple_query
            is_phrase = True
        # query database  
        try:
            if is_phrase:
                cur.execute(sql_query, (f"%{keyword}%",))
            else:    
                cur.execute(sql_query, (keyword,))
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
    
    cur.close()
    if close_conn_afterwards:
        conn.close()

    return fuzzy_res
