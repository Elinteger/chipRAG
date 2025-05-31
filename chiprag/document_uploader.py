"""
Pipeline to read in a PDF, chunk it accordingly and upload it into a PostgreSQL database.
"""
import argparse
import logging
from .chiprag_modules import load_pesticide_chapters, load_pesticide_names_from_outline, chunk_report_by_sections
from .postgres_utils import upload_dataframe


def upload_document() -> None:
    """
    Uploads a document containing Chinese pesticide residue values.
    Intended to be called only via the CLI entry point.
    Although the function itself takes no arguments, the following documentation serves informational purposes for 
    the arguments of the CLI.

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

    # parse inputs
    parser = argparse.ArgumentParser("Upload a document holding Chinese pesticide residue values")
    parser.add_argument("document",
                        type=str,
                        help="Path to PDF document which is to be scanned in.")
    parser.add_argument("document_version",
                        type=str,
                        help="Version of the document, following the style of \"GB2021-001\", \"GB2021-002\", \"GB2022-001\"...")
    parser.add_argument("begin_outline",
                        type=int,
                        help="First page where the outline in which pesticides are listed begins.")
    parser.add_argument("end_outline",
                        type=int,
                        help="Last page which holds the outline in which the pesticides are listed.")
    parser.add_argument("begin_tables",
                        type=int,
                        help="First page which holds information/tables relevant to you.")
    parser.add_argument("end_tables",
                        type=int,
                        help="Last page which holds information/tables relevant to you.")
    parser.add_argument("pest_chapter_number",
                        type=int,
                        help="Chapter number with which pesticide sections begin. For example 4 for \"4.15 Zo\"")
    args = parser.parse_args()
    document = args.document
    document_version = args.document_version
    begin_outline = args.begin_outline
    end_outline = args.end_outline
    begin_tables = args.begin_tables
    end_tables = args.end_tables
    chapter_number = args.pest_chapter_number

    # load pdf
    pdf_text = load_pesticide_chapters(document, begin_tables, end_tables)
    pdf_outline = load_pesticide_names_from_outline(document, begin_outline, end_outline, chapter_number)
    logging.info("Read in PDF.")
    
    # chunk loaded pdf into its sections
    chunk_df = chunk_report_by_sections(pdf_text, pdf_outline, document_version)
    logging.info("Chunked PDF.")

    # upload chunks
    upload_dataframe(chunk_df)
    logging.info("Upload complete.")


if __name__ == "__main__":
    upload_document() 
    