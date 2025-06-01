"""
Entrypoint of chipRAG.

Provides a command-line interface (CLI) with three subcommands:
- 'comp': Generate a comparison between Chinese and European MRLs.
- 'doc': Upload a Chinese pesticide residue document.
- 'eu' : Update pesticide data from the European DataLake.

Each subcommand accepts its own set of arguments, as described in the help output.
"""

__author__ = "Elias Schubert"
__email__ = "eschubert.mail@gmail.com"
__version__ = "1.0.0"

import argparse
from chiprag.document_uploader import upload_document
from chiprag.comparison_creater import create_comparison
from chiprag.eu_data_updater import update_eu_data


def main():
    parser = argparse.ArgumentParser(description="chipRAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Choose a command to run")

    # comparison creation sub-command
    comp_parser = subparsers.add_parser("comp", help="Create comparison between Chinese and EU MRLs")
    comp_parser.add_argument("keywords", nargs="+", help="Keywords like pesticide/food names to compare")
    comp_parser.add_argument("--output_path", default="output.xlsx", help="Path where the excel output should be saved to. Defaults to \"output.xlsx\" in the working directory")

    # chinese document upload sub-command
    cu_parser = subparsers.add_parser("doc", help="Upload Chinese pesticide document")
    cu_parser.add_argument("document", type=str, help="Path to PDF document which is to be scanned in")
    cu_parser.add_argument("document_version", type=str, help="Version of the document, following the style of \"GB2021-001\", \"GB2021-002\", \"GB2022-001\"...")
    cu_parser.add_argument("begin_outline", type=int, help="First page where the outline in which pesticides are listed begins")
    cu_parser.add_argument("end_outline", type=int, help="Last page which holds the outline in which the pesticides are listed")
    cu_parser.add_argument("begin_tables", type=int, help="First page which holds information/tables relevant to you")
    cu_parser.add_argument("end_tables", type=int, help="Last page which holds information/tables relevant to you.")
    cu_parser.add_argument("pest_chapter_number", type=int, help="Chapter number with which pesticide sections begin. For example 4 for \"4.15 Zo\"")

    # EU data update sub-command
    subparsers.add_parser("eu", help="Update EU pesticide data")

    args = parser.parse_args()

    if args.command == "comp":
        create_comparison(keywords=args.keywords, output_path=args.output_path)

    elif args.command == "doc":
        upload_document(
            document=args.document,
            document_version=args.document_version,
            begin_outline=args.begin_outline,
            end_outline=args.end_outline,
            begin_tables=args.begin_tables,
            end_tables=args.end_tables,
            pest_chapter_number=args.pest_chapter_number
        )

    elif args.command == "eu":
        update_eu_data()


if __name__ == "__main__":
    main()
