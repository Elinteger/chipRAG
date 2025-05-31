"""
Fetches pesticide data from the EU API, cleans it, and stores it in a PostgreSQL database.
"""
import logging
from .chiprag_modules import eu_fetch_api
from .postgres_utils import store_pesticide_data


def update_eu_data() -> None:
    """
    Retrieves pesticide and Maximum Residue Limit (MRL) data from the EU DataLake.
    Cleans the data and uploads it to a PostgreSQL database.    

    Returns:
        None
    """
    logging.info("-- Fetching and uploading new data from EU-Database --")
    applicable, ny_applicable = eu_fetch_api()
    print("Got Data from EU-API.")
    store_pesticide_data(
        applicable_data=applicable,
        not_yet_applicable_data=ny_applicable)
    print("Stored EU Data. Upload/Update complete.")
    

if __name__ == "__main__":
    update_eu_data()   
