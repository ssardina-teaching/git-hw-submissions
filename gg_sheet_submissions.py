"""Get the worksheet of a Google Sheet

This is done using GSHEETS package: https://gsheets.readthedocs.io/en/stable/index.html

    this package provides an easier access to the Google Sheet API:

    https://developers.google.com/sheets/api/guides/concepts


    Google API: https://developers.google.com/drive/api/guides/about-sdk

Example to download the MARKING sheet from the Google Sheet with ID 16wc.....:

$ python git-hw-submissions.git/gg_get_worksheet.py 16wcDonn15ak88kCbOUGfyWimciD7zCSRLJdbVBP0uGs MARKING -c ~/.ssh/keys/credentials.json -o marking.csv


====================================================
Example of how to get a worksheet from a Google Sheet.
    https://developers.google.com/sheets/api/quickstart/python

Google API: https://developers.google.com/drive/api/guides/about-sdk

Python Client:
    https://github.com/googleapis/google-api-python-client
    https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/index.html

Google Sheet API:
    https://developers.google.com/sheets/api/guides/concepts

    Set-up for Google Sheets: https://developers.google.com/sheets/api/quickstart/python

    In the end you should get a credentials.json

Google Google Workspace API: https://developers.google.com/drive/api/quickstart/python

    $ pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
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
try:
    TIMEZONE = ZoneInfo(TIMEZONE_STR)
except:
    # otherwise fall back to pytz
    import pytz

    TIMEZONE = pytz.timezone(TIMEZONE_STR)


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
    parser.add_argument("OUTPUT", help="Output folder to place submission files.")
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
    parser.add_argument(
        "--csv",
        type=str,
        default="submissions.csv",
        help="CSV submission file %(default)s.",
    )

    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")
    logging.info(args)

    spreadsheet_id = args.SPREADSHEET
    sheet_name = args.SHEET
    google_credentials = args.credentials
    csv_file = args.csv

    # sheets = Sheets.from_files("~/client_secrets.json", "~/storage.json")
    gg_sheets = Sheets.from_files(
        google_credentials, "storage.json", no_webserver=not args.webserver
    )

    sheet = gg_sheets[spreadsheet_id].find(sheet_name)
    sheet.to_csv(csv_file, encoding="utf-8", dialect="excel")
    logging.info(f"Sheet saved to {csv_file}")

    no_rows = sheet.nrows
    print(f"Number of rows in sheet {sheet_name}: ", no_rows)

    for i in range(2, no_rows + 1):
        timestamp = sheet[f"A{i}"]
        email = sheet[f"B{i}"]
        student_no = sheet[f"D{i}"]

        print(f"Row {i}:", timestamp, email, student_no)

    logging.info(f"Finished...")
