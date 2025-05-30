"""
FIXME: Finish this and add comments, return types and so on everywhere afterwards!
"""
import argparse
import logging
import pandas as pd
from .postgres_utils import query_database
from .chiprag_modules import extract_relevant_values, get_fitting_pesticides, compare_values
from .postgres_utils import get_pesticide_data

def create_comparison():
    # parse inputs
    parser = argparse.ArgumentParser("Compare maximum residue values of selected pesticides and foods. Inputs are: \"zoxamide\" \"wheat\" \"olive oil\" for example")
    parser.add_argument("keywords", 
                        nargs="+",
                        help="Required to know which pesticides/foods should be compared")

    args = parser.parse_args()
    # is a list of the keywords like ['a', 'b', 'c'] from input like "a" "b" "c"
    keywords = args.keywords 

    # get values which are relevant for comparison
    chi_values = _get_chi_values(keywords)
    if chi_values.empty:
        return chi_values
    eu_values, bridge_dict = _get_eu_values(chi_values, keywords)
    # compare
    comparison = compare_values(chi_values, eu_values, bridge_dict)
    return comparison


def _get_chi_values(keywords):
    list = query_database(keywords)
    if len(list) == 0:
         logging.warning("Couldn't find any values in the database fitting the users request. Check request and database accordingly.")
         return pd.DataFrame(list)
    
    return extract_relevant_values(keywords, list)


def _get_eu_values(chi_values, keywords):
    # get fitting eu_pesticides, dict that acts as a bridge between chi_values and eu_values
    eu_pesticide_dict = get_fitting_pesticides(chi_values)
    # get all data regarding those pesticides
    eu_pesticides_list = [item for sublist in eu_pesticide_dict.values() for item in sublist]
    eu_values = get_pesticide_data(eu_pesticides_list)
    # build dataframe
    rows = []
    for key, tuples_list in eu_values.items():
        for tup in tuples_list:
            # tup is like ('Zoxamide', 'wheat', '0.02')
            rows.append({
                'chi_pesticide': key,
                'eu_pesticide': tup[0],
                'food': tup[1],
                'mrl': tup[2]
            })
    eu_df = pd.DataFrame(rows)
    return eu_df, eu_pesticide_dict


if __name__ == "__main__":
    create_comparison()
