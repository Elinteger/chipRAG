import os
import sys
# needed so that python can find our modules
#FIXME: "Use setup.py or pyproject.toml with package_dir={"": "src"}"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  

from eu_data_tools import fetch_data_from_eu_api, store_data_from_eu_api
import chiprag
import pandas as pd
from chiprag_modules import ( 
    load_pesticide_chapters, 
    load_pesticide_names_from_outline, 
    chunk_report_by_sections,
    establish_connection,
    upload_dataframe,
    query_database,
    extract_relevant_values
    )

def main():
    conn = establish_connection()
    df1 = pd.read_csv("eudata.csv")
    df2 = pd.read_csv("eudata2.csv")
    store_data_from_eu_api(df1, df2, conn)
    print("Done")
    # df = chiprag.main()
    # print(df)


def get_eu_data():
    applicable_data, not_yet_applicable_data = fetch_data_from_eu_api()
    applicable_data.to_csv("eudata.csv")
    not_yet_applicable_data.to_csv("eudata2.csv")


if __name__ == "__main__":
    main()

# plan for SQL
# saver for eu data 
# comparison
    # fuzzy search (vielleicht auf ganze liste an llm?)
    # llm frage (wenn nicht ganze liste)
    # pestizide rausholen
    # für jede reihe querien ob was passendes dabei ist