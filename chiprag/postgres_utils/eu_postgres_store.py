"""
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
    Gets all EU-info needed about pesticides for a list of pesticides
    """
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    query = queries["get_relevant_applicable_entries_eu"]
    conn, cur = establish_connection()

    pesticide_dict = {}
    try:
        for pesticide in pesticide_list:
            try: 
                cur.execute(query)
                conn.commit()
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


def store_pesticide_data(
        applicable_data: pd.DataFrame,
        not_yet_applicable_data: pd.DataFrame,
) -> None:
    """
    Store european pesticide data in database
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
            data = [(row['pesticide_residue_name'], row['product_name'], row['mrl_value_only'], row["applicability_text"], row["application_date"]) for _, row in df.iterrows()]
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


def get_all_pesticides():
    """
    FIXME:
    """
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    get_query = queries["get_unique_pesticides_eu"]

    raw_data = get_data(get_query)

    return raw_data
