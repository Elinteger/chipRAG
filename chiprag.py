"""
Entrypoint of chipRAG.
"""
from chiprag.document_uploader import upload_document
from chiprag.comparison_creater import create_comparison
from chiprag.eu_data_updater import update_eu_data


if __name__ == "__main__":
    a, b = create_comparison()
    print(a)
    print("----------------------------------")
    print(b)
   
