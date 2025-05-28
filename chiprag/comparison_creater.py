"""
FIXME: Finish this and add comments, return types and so on everywhere afterwards!
"""
import argparse
import logging
from .postgres_utils import query_database
from .chiprag_modules import extract_relevant_values
from .postgres_utils import get_all_pesticides

def create_comparison():
    # parse inputs
    parser = argparse.ArgumentParser("Compare maximum residue values of selected pesticides and foods. Inputs are: \"zoxamide\" \"cheese\" \"pork\" for example")
    parser.add_argument("keywords", 
                        nargs="+",
                        help="Required to know which pesticides/foods should be compared")

    args = parser.parse_args()
    keywords = args.keywords  # is a list of the keywords like ['a', 'b', 'c'] from input like "a" "b" "c"
  
    # get values which are relevant for comparison
    chi_values = _get_chi_values(keywords)
    if len(chi_values == None):
        return chi_values
    eu_values = _get_eu_values(chi_values, keywords)
    
    return chi_values


def _get_chi_values(keywords):
    list = query_database(keywords)
    if len(list) == 0:
         logging.warning("Couldn't find any values in the database fitting the users request. Check request and database accordingly.")
         return None
    return list
    # return extract_relevant_values(keywords, list)


def _get_eu_values(chi_values, keywords):
    #TODO:
    raw_data = get_all_pesticides()
    eu_pesticides = [row[0].strip() for row in raw_data]


if __name__ == "__main__":
    create_comparison()
