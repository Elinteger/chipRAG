import argparse

from .postgres_utils import query_database
from .chiprag_modules import extract_relevant_values

def create_comparison():
    # parse inputs
    parser = argparse.ArgumentParser("Compare maximum residue values of selected pesticides and foods. Inputs are: \"zoxamide\" \"cheese\" \"pork\" for example")
    parser.add_argument("keywords", 
                        nargs="+",
                        help="Required to know which pesticides/foods should be compared")

    args = parser.parse_args()
    keywords = args.keywords  # a list of the keywords like ['a', 'b', 'c'] from "a" "b" "c"
    # get values which are relevant for comparison
    chi_values = _get_chi_values(keywords)
    eu_values = _get_eu_values(chi_values, keywords)
    print(eu_values)


def _get_chi_values(keywords):
    list = query_database(keywords)
    return extract_relevant_values(keywords, list)


def _get_eu_values(chi_values, keywords):
    #TODO:
    pass


if __name__ == "__main__":
    create_comparison()
