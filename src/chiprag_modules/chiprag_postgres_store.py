"""
Collection of functions to send data to and get data from a PostgreSQL database in the context of this 
somewhat unconventional RAG pipeline.
"""
import pandas as pd
import psycopg2
import yaml
from psycopg2 import OperationalError, DatabaseError, ProgrammingError
from psycopg2.extras import execute_values

def establish_connection(
    database: str, #pesticide_db
    user: str, #postgres
    password: str,
    host: str = 'localhost',
    port: int = 5432
) -> psycopg2.extensions.connection:
    """
    Establishes a connection with a specified PostgreSQL. 
    Default is a local database on localhost port 5432.

    Args:
        database (str): Name of the database that is to be connected to.
        user (str): Username of the user accessing the database.
        password (str): Password of the user accessing the database.
        host (str): URL where the Database-API is hosted. Defaults to localhost.
        port (int): Portnumber over which Database-API can be accessed. Defaults to 5432

    Returns:
        psycopg2.extensions.connection: A psycopg2 connection object.
    """ 
    ## faulty argument handling
    if not isinstance(database, str):
        raise TypeError(f"'database' must be a string, got {type(database).__name__}")
    if not isinstance(user, str):
        raise TypeError(f"'user' must be a string, got {type(user).__name__}")
    if not isinstance(password, str):
        raise TypeError(f"'password' must be a string, got {type(password).__name__}")
    if not isinstance(host, str):
        raise TypeError(f"'host' must be a string, got {type(host).__name__}")
    if not isinstance(port, int):
        raise TypeError(f"'port' must be an integer, got {type(port).__name__}")
    if not (1 <= port <= 65535):
        raise ValueError("'port' must be in range 1–65535")
    
    ## connect to database
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
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
    with open("config/query.yaml", "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_query"]

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
    Performs a fuzzy word match for single keywords and a fuzzy window search for keyphrases.

    Args:
        user_prompt (str): Keywords given by the user, split by ';'. This is not enforced by code, but is a requirement.
        conn (Psycopg2 Connection Object): Connection Object to perform actions with the database.
        close_conn_afterwards (bool): Variable to decide whether to close the Connection Object after use. Defaults to True.

    Returns:
        list[str]: List of all rows matching the SQL-query.
    '''
    ## faulty argument handling
    #FIXME: validate that user input is properly as expected: "citrus; zoxamide; pumpkin seeds" -> use AxonIvy?
    if not isinstance(user_prompt, str):
        raise TypeError(f"'user_prompt' must be a string, got {type(user_prompt).__name__}")
    if not isinstance(close_conn_afterwards, bool):
        raise TypeError(f"'close_conn_afterwards' must be a bool, got {type(close_conn_afterwards).__name__}")
    if conn == None:
        raise ValueError(f"conn is 'None', connecting to Database either failed or hasn't been performed")

    ## querying
    # load SQL-queries
    with open("config/query.yaml", "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    fuzzy_single_query = queries["fuzzy_single_query"]
    fuzzy_window_query = queries["fuzzy_window_query"]

    # create cursor from connection object
    cur = conn.cursor()

    # split user input to get keywords to look for
    keywords = [item.strip() for item in user_prompt.split(';')]

    # fuzzy text search
    #FIXME: -> CREATE EXTENSION pg_trgm; in postgresql database!
    fuzzy_res = []
    for keyword in keywords:
        if len(keyword) == 0:
            continue
        # if keyword is a single word, do a word by word match
        if len(keyword.split()) == 1:
            fuzzy_query = fuzzy_single_query
        # if keyword is actually a keyphrase, do a window match
        else:
            window_size = len(keyword.split())
            #FIXME:: check if there are no duplicates this way, or if there is an easier/faster way!
            fuzzy_query = fuzzy_window_query.format(window_size=window_size)

        try:
            cur.execute(fuzzy_query, (keyword,))
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

        # cur.execute(fuzzy_query, (keyword,)) #FIXME: check if its still working!
        fuzzy_res.extend(cur.fetchall())

    # should already be distinct due to the queries, but as a failsafe
    # in case the queries change in the future and this has been forgotten
    prompt_context = list(set(fuzzy_res))
    
    cur.close()
    if close_conn_afterwards:
        conn.close()

    return prompt_context
