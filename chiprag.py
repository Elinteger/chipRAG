from chiprag.document_uploader import upload_document
from chiprag.comparison_creater import create_comparison
from chiprag.eu_data_updater import update_eu_data

#FIXME: added verisonnumber to chunks now, now I got to change the query to get it into the DB and there update accordingly
# have a first versin in the chi_postgresstore and in the query.yaml but can't test it right now-> TEST!
import pandas as pd 
if __name__ == "__main__":
    liste: pd.DataFrame = upload_document()
    liste.to_csv("testest.csv")
