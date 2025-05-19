"""
Collection of functions to send data to and get data from a PostgreSQL database in the context of this 
somewhat-RAG pipeline.
"""
import openai
import os
import pandas as pd
import psycopg2
import yaml
from dotenv import load_dotenv
from psycopg2.extras import execute_values


def establish_connection(
    #FIXME: remove errors
    database: str, #pesticide_db
    user: str, #postgres
    password: str,
    host: str = 'localhost',
    port: int = 5432
):
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
        A psycopg2 connection object.
    """ 
    ## faulty argument handling
    # check input types
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
    # check if port is valid
    if not (1 <= port <= 65535):
        raise ValueError("'port' must be in range 1–65535")
    
    ## connect to database
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )

    return conn


def upload_dataframe(
    df: pd.DataFrame,
    conn,
    close_conn_afterwards: bool = True
) -> None:
    """
    Uploads a given DataFrame using a query to a postgreSQL Database. This only works properly with a
    Pandas DataFrame with the columns [pesticide, text].

    Args:
        df (pd.DataFrame): The Pandas DataFrame which is to be uploaded.
        conn (psycopg2 Connection Object): Connection Object to perform actions with the database.
        close_conn_afterwards (bool): Variable to decide if Connection Object is to be closed after closed
                                      after use. Defaults to True.
    """
    # load queries
    with open("config/query.yaml", "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_query"]

    # create cursor from connect
    cur = conn.cursor()

    # turn dataframe into list
    data = [(row['pesticide'], row['text']) for _, row in df.iterrows()]

    # run SQL with data on database
    execute_values(cur, insert_query, data)
    conn.commit()

    cur.close()
    if close_conn_afterwards:
        conn.close()


def query_database(
    user_prompt: str,
    conn,
    close_conn_afterwards: bool = True
)->list[str]:
    '''
    #FIXME: add comment
    '''
    ## faulty argument handling
    if not isinstance(user_prompt, str):
        raise TypeError(f"'database' must be a string, got {type(user_prompt).__name__}")

    ## setup
    with open("config/query.yaml", "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    fuzzy_single_query = queries["fuzzy_single_query"]
    fuzzy_window_query = queries["fuzzy_window_query"]

    # Kipitz
    load_dotenv()
    KIPITZ_API_TOKEN = os.getenv("KIPITZ_API_TOKEN")
    openai_client = openai.OpenAI(
***REMOVED***
        api_key=KIPITZ_API_TOKEN
    )

    # Postgresql 
    cur = conn.cursor()

    # we expect the user to only give keywords like "citrus; zoxamide; pumpkin seeds" split with ; as a prompt
    # TODO: Validate user input prompt in Axon Ivy(?)
    keywords = [item.strip() for item in user_prompt.split(';')]

    ## Fuzzy text search
    # -> CREATE EXTENSION pg_trgm;
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
            # insert window size in {window_size} in prompt
            #TODO: check if there are no duplicates this way, or if there is an easier/faster way!
            fuzzy_query = fuzzy_window_query.format(window_size=window_size)

        cur.execute(fuzzy_query, (keyword,))
        fuzzy_res.extend(cur.fetchall())

    # should already be distinct due to the queries, but as a failsafe
    # in case the queries change in the future and this has been forgotten
    prompt_context = list(set(fuzzy_res))
    
    cur.close()
    if close_conn_afterwards:
        conn.close()

    return prompt_context
