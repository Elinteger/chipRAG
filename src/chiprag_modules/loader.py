"""
This module provides functions to read specified parts of a PDF document and split it accordingly.
It is tailored to the English translations of the Chinese report "Translation of Maximum Residue Limits 
for Pesticides in Foods" by the United States Department of Agriculture. 
"""

import logging
import pymupdf 
import re
from pathlib import Path


#TODO: add multipage support
def load_pesticide_chapters(
    pdf_path: str,    
    start_page: int,
    end_page: int 
) -> str:
    """
    Extracts all the text from the specified PDF in range of the specified pages. 
    Expects the content of the pages to be the document mentioned above. Specified
    to extract subsections of pesticides and their maximum residue value tables of
    the translation of `GB 2763-2021` by the USDA.

    Args:
        pdf_path (str): System path to the PDF document.
        start_page (int): First page to load (otherwise inclusive). 
                        Typically the first page containing pesticide data.
        end_page (int): Last page to load (inclusive). Usually the last page with a relevant table, 
                        excluding those about "Extraneous Maximum Residue Values."

    Returns:
        str: A String containing the text content of the document.
    """
    ## faulty argument handling
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError(f"Provided path must be a valid pdf path: {pdf_path}")
    
    for name, value in {"start_page": start_page, "end_page": end_page}.items():
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{name} must be a non-negative integer, got {value}")
    if end_page > start_page:
        raise ValueError(f"`end_page` ({end_page}) must be greater than `start_page` ({start_page}).")

    ## load document and delete unwanted pages
    doc = pymupdf.open(pdf_path)
    last_page = doc.page_count
    if end_page <= last_page:
        doc.delete_pages(from_page=end_page)
    else:
        logging.warning(f"end_page ({end_page}) is outside of the document (max page {last_page}), no pages deleted.")
    #FIXME: logic doesn't work for "1", generally not fully thought through
    if start_page > 0:
        doc.delete_pages(from_page=0, to_page=start_page-2)  # -2 because index starts at 0 and start_page is inclusive

    ## extract text
    text = ""
    for page in doc:
        """
        TODO: adapt the cropbox to the current document(s)
        cropbox is set to cut out the page number at the bottom, this is based on the translation of `GB 2763-2021` by the USDA.

        for more information have a look at the documentation: https://pymupdf.readthedocs.io/en/latest/page.html#Page.set_cropbox
        """
        cropbox_width = 600  # x1
        cropbox_height = 750  # y1
        page.set_cropbox(pymupdf.Rect(0, 0, cropbox_width, cropbox_height))
        tmp_text = page.get_text(sort=True)
        # remove multiple spaces and characters after newlines
        text += re.sub(r'\n +', '\n', re.sub(r' {2,}', ' ', tmp_text) + '\n')
    
    return text


def load_pesticide_names_from_outline(
    pdf_path: str,
    start_outline: int,
    end_outline: int, 
    pesticide_chapter_number: int
) -> list[str]:
    """
    Extracts all the pesticide names out of the outline.
    Expects the content of the pages to be the document mentioned above. Specified
    to the outline of the translation of `GB 2763-2021` by the USDA.
    """
    ## faulty argument handling
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError(f"Provided path must be a valid pdf path: {pdf_path}")
    
    for name, value in {"start_outline": start_outline, "end_outline": end_outline, "pesticide_chapter_number": pesticide_chapter_number}.items():
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{name} must be a non-negative integer, got {value}")
    if end_outline > start_outline:
        raise ValueError(f"`end_outline`({end_outline}) must be greater than `start_outline` ({start_outline}).")
    
    ## load document and delete unwanted pages
    doc = pymupdf.open(pdf_path)
    last_page = doc.page_count
    if end_outline <= last_page:
        doc.delete_pages(from_page=end_outline)
    else:
        logging.warning(f"end_outline ({end_outline}) is outside of the document (max page {last_page}), no pages deleted.")
    #FIXME: logic doesn't work for "1", generally not fully thought through
    if start_outline > 0:
        doc.delete_pages(from_page=0, to_page=start_outline-2)  # -2 because index starts at 0 and start_page is inclusive

    ## extract text
    text = ""
    for page in doc:
        """
        TODO: adapt the cropbox to the current document(s)
        cropbox is set to cut out the page number at the bottom, this is based on the translation of `GB 2763-2021` by the USDA.

        for more information have a look at the documentation: https://pymupdf.readthedocs.io/en/latest/page.html#Page.set_cropbox
        """
        cropbox_width = 600  # x1
        cropbox_height = 750  # y1
        page.set_cropbox(pymupdf.Rect(0, 0, cropbox_width, cropbox_height))

    ## filter out pesticide names
    """
    TODO: adapt regex to the layout of the current document(s)
    regex is currently set to the section numbers of the translation of `GB 2763-2021` by the USDA, which 
    look like this: 4.1, 4.10, 4.100 ...
    """
    regex = re.compile(rf'{pesticide_chapter_number}\.\d+[^\.]+')
    pesticide_list = regex.findall(text)

    return pesticide_list
