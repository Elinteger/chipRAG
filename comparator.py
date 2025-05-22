import os
import sys
# needed so that python can find our modules
#FIXME: "Use setup.py or pyproject.toml with package_dir={"": "src"}"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  

from eu_data_tools import update_eu_data
import chiprag
import pandas as pd


def main():
    update_eu = True
    if update_eu:
        update_eu_data()
    # get chipragdata from prompt
    # chiprag.main(prompt)
    # get all distinct pesticides
    # see (somehow) if pesticide exists in eu data (fetch all pesticides for that, then either fuzzy or LLM) -> dataframe that keeps track of chinese and possible eu
    # get data for all possible pesticides, ask LLM if there is a value for row from chinese in any of the EU  
    # get everything into one big dataframe -> thats a different "result dataframe"
    # dataframe to excel
    print("done")


if __name__ == "__main__":
    main()
