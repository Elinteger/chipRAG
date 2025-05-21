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
    print("done")


if __name__ == "__main__":
    main()

# plan for SQL
# saver for eu data 
# comparison
    # fuzzy search (vielleicht auf ganze liste an llm?)
    # llm frage (wenn nicht ganze liste)
    # pestizide rausholen
    # für jede reihe querien ob was passendes dabei ist