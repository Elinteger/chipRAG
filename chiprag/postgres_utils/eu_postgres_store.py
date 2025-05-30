"""
Functions for saving, updating, and retrieving EU DataLake data in a PostgreSQL database.
"""
import pandas as pd
import yaml
from config.load_config import settings
from psycopg2 import DatabaseError, ProgrammingError
from psycopg2.extras import execute_values
from .util_postgres_store import establish_connection, get_data


def get_pesticide_data(
        pesticide_list: list[str]
) -> dict:
    """
    Fetches all data from the EU DataLake database for specified pesticides.

    Args:
        pesticide_list (list[str]): List of pesticide names to retrieve data for.

    Returns:
        dict: Mapping of pesticide names to their full database records.
    """
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    query = queries["get_relevant_applicable_entries_eu"]
    conn, cur = establish_connection()

    pesticide_dict = {}
    try:
        for pesticide in pesticide_list:
            try: 
                cur.execute(query, (pesticide.strip(),))
                res = cur.fetchall()
                pesticide_dict[pesticide] = res
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
    
    # remove empty values
    filtered_pesticide_dict = {k: v for k, v in pesticide_dict.items() if v}
    return filtered_pesticide_dict


def store_pesticide_data(
        applicable_data: pd.DataFrame,
        not_yet_applicable_data: pd.DataFrame,
) -> None:
    """
    Stores cleaned EU DataLake data in a PostgreSQL database.

    First clears existing entries and resets the ID sequence, then inserts the new applicable data.

    Args:
        applicable_data (pd.DataFrame): DataFrame with applicable entries. 
        Must include: pesticide_residue_name, product_name, mrl_value_only, applicability_text, application_date.
        not_yet_applicable_data (pd.DataFrame): DataFrame with not yet applicable entries. 
        Must include: pesticide_residue_name, product_name, mrl_value_only, applicability_text, application_date.

    Returns:
        None
    """
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_eu_query"]
    truncate_query = queries["truncate_eu_query"]
    conn, cur = establish_connection()

    # clear database of old data and reset the sequence for the automated id's
    try: 
        cur.execute(truncate_query)
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

    try:
        for df in [applicable_data, not_yet_applicable_data]:
            # turn dataframe into list, dataframe must have the specified columns!
            data = [(row['pesticide_residue_name'].strip(), row['product_name'].strip(), row['mrl_value_only'], row["applicability_text"].strip(), row["application_date"]) for _, row in df.iterrows()]
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


def get_all_pesticides() -> list:
    """
    Retrieves a list of all unique pesticides from the PostgreSQL database.

    Returns:
        list: All unique pesticide names.
    """
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    get_query = queries["get_unique_pesticides_eu"]

    raw_data = get_data(get_query)

    return raw_data
