"""
This module provides a single function that splits the chapters of a document into rows of a Pandas DataFrame, 
based on its text content/headers.

It is tailored to the English translations of the Chinese report titled "Translation of Maximum Residue Limits 
for Pesticides in Foods," published by the United States Department of Agriculture. Specifically, it targets 
the translation of document `GB 2763-2021`, but it should work similarly for related reports of the same kind.
"""
import logging
import pandas as pd
import re


def chunk_report_by_sections(
    text: str,
    pesticide_list: list[str]  
) -> pd.DataFrame:
    """
    Splits a given text into chapters by identifying pesticide-related headings,
    which are matched against a provided list of pesticide names. These pesticide
    names are extracted from the same source documents outline/table of content.

    Each identified chapter is paired with the corresponding pesticide name and returned
    as a row in a Pandas DataFrame.

    Args:
        text (str): The full text content of a PDF document.
        pesticide_list (list[str]): A list of pesticide names to be matched against headings in the text.

    Returns:
        pd.DataFrame: A DataFrame with columns "pesticide" and "text", where each row contains
                      a pesticide name and the corresponding chapter text.
    """
    ## faulty argument handling
    if not isinstance(text, str):
        raise TypeError(f"'text' must be a string, got {type(text).__name__}")

    if not isinstance(pesticide_list, list) or not all(isinstance(p, str) for p in pesticide_list):
        raise TypeError("'pesticide_list' must be a list of strings")

    ## chunking text into sections
    # these serve as the "heading" of a certain chapter
    pesticides = []  
    # heading, general informations, maximum residue tables
    chapter_content = []  
    remaining_text = text

    for pesticide in pesticide_list:
        # building regex pattern
        escaped_pesticide = [re.escape(c) for c in pesticide if not c.isspace()]
        pattern = r'\s*'.join(escaped_pesticide)
        regex = re.compile(pattern)
        # match current regex pattern made out of pesticide against the text
        match = regex.search(remaining_text)
        if match:
            chapter_start_idx = match.start()
            # extract text
            text_before_idx = remaining_text[:chapter_start_idx]
            # adapt remaining text
            remaining_text = remaining_text[chapter_start_idx:]
            # add to text column
            chapter_content.append(text_before_idx)

            # clean pesticide before adding from parantheses, brackets and chapter numbers
            pesticide_str = re.search(r'([\(\[].*?[\)\]])\s*$', pesticide).group(1) 
            if pesticide_str[-1]==')':
                idx = pesticide_str.rfind('(')
            elif pesticide_str[-1]==']':
                idx = pesticide_str.rfind('[')
            else: 
               logging.warning(
                    "Elements in 'pesticide_list' are expected to contain either parentheses or brackets. "
                    "Check the current document to determine whether this expectation is outdated or if the regex used is incorrect."
                )
            # add to pesticide column
            pesticides.append(pesticide_str[idx+1:-1])
        else:  
            # no match with current pesticide
            continue
    # FIXME: check logic for if the first chapter_content entry can always be deleted 
    # and how to figure out if it has to be + how to handle edge cases
    chapter_content.append(remaining_text)
    del chapter_content[0]

    ## creating DataFrame
    df = pd.DataFrame({
        "pesticide": pesticides,
        "text": chapter_content
    })
    
    return df 
