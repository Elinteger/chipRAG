"""
Pipeline to read in a PDF, chunk it accordingly and upload it into a PostgreSQL database.
"""
import logging
from .chiprag_modules import load_pesticide_chapters, load_pesticide_names_from_outline, chunk_report_by_sections
from .postgres_utils import upload_dataframe


def upload_document(
        document: str,
        document_version: str,
        begin_outline: int,
        end_outline: int,
        begin_tables: int,
        end_tables: int,
        pest_chapter_number: int
) -> None:
    """
    Uploads a document containing Chinese pesticide residue values.

    Args:
        document (str): Path to PDF document which is to be scanned in.
        document_version (str): Version of the document, following the style of \"GB2021-001\", \"GB2021-002\", \"GB2022-001\"...
        begin_outline (int): First page where the outline in which pesticides are listed begins.
        end_outline (int): Last page which holds the outline in which the pesticides are listed.
        begin_tables (int): First page which holds information/tables relevant to you.
        end_tables (int): ast page which holds information/tables relevant to you.
        pest_chapter_number (int): Chapter number with which pesticide sections begin. For example 4 for \"4.15 Zo\"

    Returns:
        None
    """
    logging.info("-- Uploading new document to database --")
    # load pdf
    pdf_text = load_pesticide_chapters(document, begin_tables, end_tables)
    pdf_outline = load_pesticide_names_from_outline(document, begin_outline, end_outline, pest_chapter_number)
    logging.info("Read in PDF.")
    
    # chunk loaded pdf into its sections
    chunk_df = chunk_report_by_sections(pdf_text, pdf_outline, document_version)
    logging.info("Chunked PDF.")

    # upload chunks
    upload_dataframe(chunk_df)
    logging.info("Upload complete.")


if __name__ == "__main__":
    upload_document() 
    