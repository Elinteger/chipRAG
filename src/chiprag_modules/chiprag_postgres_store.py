"""
Collection of functions to send data to and get data from a PostgreSQL database in the context of this 
somewhat unconventional RAG pipeline.
"""
import os
import pandas as pd
import psycopg2
import yaml
from dotenv import load_dotenv
from psycopg2 import OperationalError, DatabaseError, ProgrammingError
from psycopg2.extras import execute_values
from rapidfuzz import fuzz
from sqlalchemy import create_engine

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
    #FIXME: |-| validate that user input is properly as expected: "citrus; zoxamide; pumpkin seeds" -> use AxonIvy?
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
    get_all_query = queries["get_all_query"]

    # create cursor from connection object
    cur = conn.cursor()

    # split user input to get keywords to look for
    keywords = [item.strip() for item in user_prompt.split(';')]
    
    # fuzzy text search
    #FIXME: |-| -> CREATE EXTENSION pg_trgm; in postgresql database!
    fuzzy_res = []
    fetched_database = None
    for keyword in keywords:
        if len(keyword) == 0:
            continue
        # if keyword is a single word, do a word by word match
        if len(keyword.split()) == 1:
            fuzzy_query = fuzzy_single_query
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
        # if keyword is actually a keyphrase, fetch the database and do a fuzzy search locally
        # -> used to be a SQL-query aswell, but it sadly didn't work as well, look into query.yaml for old query
        else:
            if fetched_database == None:
                # create sqlalchemy connection as psycopg2 isn't supported by pandas anymore
                # TODO: replace all of psycopg2 to sqlalchemy in chiprag
                load_dotenv()
                password_postgre = os.getenv("POSTGRE_PASSWORD_HOME")
                POSTGRES_ADDRESS = "localhost"
                POSTGRES_PORT = "5432"
                POSTGRES_USERNAME = "postgres"
                POSTGRES_PASSWORD = password_postgre
                POSTGRES_DBNAME = "pesticide_db"
                postgres_str = ('postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'
                .format(username=POSTGRES_USERNAME,
                password=POSTGRES_PASSWORD,
                ipaddress=POSTGRES_ADDRESS,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DBNAME))

                cnx = create_engine(postgres_str)
                fetched_database = pd.read_sql_query(get_all_query, con=cnx)
            match_counter = 0
            for _, row in fetched_database.iterrows():
                text = row['text']
                match_counter += text.lower().count("liver of pig".lower())
                if _contains_keyphrase(row['text'], keyword): 
                    match_counter += 1
                    fuzzy_res.append(tuple(row)) 
            return match_counter
    cur.close()
    if close_conn_afterwards:
        conn.close()

    return list(set(fuzzy_res))


def _contains_keyphrase(
        text: str,
        keyphrase: str,
        threshhold: int = 95
) -> bool:
    """
    A small private helper-function to check if a keyphrase is inside a block of text using RapidFuzz to allow typos.

    Args:
        text (str): Text to be scanned through for keyphrase.
        keyprase (str): Keyphrase which is to be searched for.
        theshhold (int): Similarity percentage that has to be reached for a match. Defaults to 80.

    Returns
        bool: True if a fuzzy match of the keyphrase in the text could me made.
    """
    return fuzz.partial_ratio(text.lower(), keyphrase.lower()) >= threshhold 
