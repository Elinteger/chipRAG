#FIXME: add description
import json
import pandas as pd
import psycopg2
import requests
import yaml
from config.load_config import settings
from psycopg2 import DatabaseError, ProgrammingError
from psycopg2.extras import execute_values

def fetch_data_from_eu_api() -> tuple[pd.DataFrame, pd.DataFrame]:
#FIXME: description
    ## setup/config
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    format = "json"
    language = "EN"

    response = requests.get(f"https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/pesticide_residues_mrls/download?format={format}&language={language}&api-version=v2.0", headers=headers)
    data = response.json()
    return _clean_data_from_eu_api(data)


def store_data_from_eu_api(
        applicable_data: pd.DataFrame,
        not_yet_applicable_data: pd.DataFrame,
        conn: psycopg2.extensions.connection,
        close_conn_afterwards: bool = True
) -> None:
    """
    #FIXME: add description
    """
     ## faulty argument handling
    if not isinstance(applicable_data, pd.DataFrame):
        raise TypeError(f"'applicable_data' must be a pd.DataFrame, got {type(applicable_data).__name__}")
    if not isinstance(not_yet_applicable_data, pd.DataFrame):
        raise TypeError(f"'not_yet_applicable_data' must be a pd.DataFrame, got {type(not_yet_applicable_data).__name__}")
    if not isinstance(close_conn_afterwards, bool):
        raise TypeError(f"'close_conn_afterwards' must be a bool, got {type(close_conn_afterwards).__name__}")
    if conn == None:
        raise ValueError(f"conn is 'None', connecting to Database either failed or hasn't been performed")
    
    with open(settings.query_path, "r", encoding="utf-8") as f:
        queries = yaml.safe_load(f)
    insert_query = queries["insert_eu_query"]

    # create cursor from connection object
    cur = conn.cursor()

    #FIXME: check what Unnamed:0 is about
    for df in [applicable_data, not_yet_applicable_data]:
        df.drop(labels=["Unnamed: 0", "product_code"], axis=1)

        # turn dataframe into list, dataframe must have the specified columns!
        data = [(row['pesticide_residue_name'], row['product_name'], row['mrl_value_only'], row["applicability_text"], row["application_date"]) for _, row in df.iterrows()]

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
    

def _clean_data_from_eu_api(
    data: json
) -> tuple[pd.DataFrame, pd.DataFrame]:
    #FIXME: description
    
    df = pd.DataFrame(data)
    # only get columns of importance
    filtered_df = df[["pesticide_residue_name", "product_code", "product_name", "mrl_value_only", "applicability_text", "application_date"]]
    # remove duplicates
    filtered_df = filtered_df.drop_duplicates()
    # remove non-applicable values
    filtered_df = filtered_df[~filtered_df["applicability_text"].str.contains("No longer applicable")]
    # put not yet applicable values without a date in their own table and sort them
    not_yet_applicable_data = filtered_df[filtered_df["applicability_text"].str.contains("Not yet applicable") & filtered_df["application_date"].isna()]
    not_yet_applicable_data = not_yet_applicable_data.sort_values(by="pesticide_residue_name")
    # drop not yet applicable values from filtered_df
    applicable_data = filtered_df.drop(not_yet_applicable_data.index)
    # sort according to pesticide residue names and then their product code
    applicable_data = filtered_df.sort_values(by=["pesticide_residue_name", "product_code"])

    return applicable_data, not_yet_applicable_data


