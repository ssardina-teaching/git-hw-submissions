"""Get the worksheet of a Google Sheet

This is done using GSHEETS package: https://gsheets.readthedocs.io/en/stable/index.html

    this package provides an easier access to the Google Sheet API:

    https://developers.google.com/sheets/api/guides/concepts


    Google API: https://developers.google.com/drive/api/guides/about-sdk

Example to download the MARKING sheet from the Google Sheet with ID 16wcDonn15ak88kCbOUGfyWimciD7zCSRLJdbVBP0uGs:

$ python git-hw-submissions.git/gg_get_worksheet.py 16wcDonn15ak88kCbOUGfyWimciD7zCSRLJdbVBP0uGs MARKING -c ../git-hw-submissions.git/credentials.json -o marking.csv
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

from argparse import ArgumentParser
from datetime import datetime
from zoneinfo import ZoneInfo  # this should work Python 3.9+

import logging
import coloredlogs

from gsheets import Sheets


# get the TIMEZONE to be used - works with Python < 3.9 via pytz and 3.9 via ZoneInfo
TIMEZONE_STR = "Australia/Melbourne"
TIMEZONE = ZoneInfo(TIMEZONE_STR)


LOGGING_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE = "%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL = logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)


if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("SPREADSHEET", help="List of repositories to post comments to.")
    parser.add_argument("SHEET", help="List of student results.")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output.csv",
        help="CSV output file %(default)s.",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        default="credentials.json",
        help="File containing Google credentials %(default)s.",
    )
    parser.add_argument(
        "--webserver",
        action="store_true",
        help="Flag to enable webserver functionality for Google authentication (otherwise console-based).",
    )
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")
    logging.info(args)

    spreadsheet_id = args.SPREADSHEET
    sheet_name = args.SHEET
    google_credentials = args.credentials
    csv_file = args.output

    # sheets = Sheets.from_files("~/client_secrets.json", "~/storage.json")
    sheets = Sheets.from_files(
        google_credentials, "storage.json", no_webserver=args.webserver
    )

    marking = sheets[spreadsheet_id].find(sheet_name)

    marking.to_csv(csv_file, encoding="utf-8", dialect="excel")

    logging.info(f"Finished...")
