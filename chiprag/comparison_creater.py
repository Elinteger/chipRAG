"""
FIXME: Finish this and add comments, return types and so on everywhere afterwards!
"""
import argparse
import logging
import pandas as pd
from .postgres_utils import query_database
from .chiprag_modules import extract_relevant_values, get_fitting_pesticides
from .postgres_utils import get_all_pesticides

def create_comparison():
    # parse inputs
    parser = argparse.ArgumentParser("Compare maximum residue values of selected pesticides and foods. Inputs are: \"zoxamide\" \"wheat\" \"olive oil\" for example")
    parser.add_argument("keywords", 
                        nargs="+",
                        help="Required to know which pesticides/foods should be compared")

    args = parser.parse_args()
    keywords = args.keywords  # is a list of the keywords like ['a', 'b', 'c'] from input like "a" "b" "c"
  
    # get values which are relevant for comparison
    chi_values = _get_chi_values(keywords)
    if chi_values.empty:
        return chi_values
    eu_values = _get_eu_values(chi_values, keywords)
    
    return chi_values["pesticide"].unique().tolist(), eu_values


def _get_chi_values(keywords):
    list = query_database(keywords)
    if len(list) == 0:
         logging.warning("Couldn't find any values in the database fitting the users request. Check request and database accordingly.")
         return pd.DataFrame(list)
    
    return extract_relevant_values(keywords, list)


def _get_eu_values(chi_values, keywords):
    # get fitting eu_pesticides
    eu_pesticides = get_fitting_pesticides(chi_values)
    return eu_pesticides

if __name__ == "__main__":
    create_comparison()
