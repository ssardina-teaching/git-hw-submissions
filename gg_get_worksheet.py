"""Get the worksheet of a Google Sheet

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

Example:

$ python gh_pr_feedback_comment.py repos.csv marking-p0.csv reports  -t ~/.ssh/keys/gh-token-ssardina.txt --repos s3975993 |& tee -a pr_feedback_remark.log
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import csv
import os
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
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")
    logging.info(args)

    spreadsheet_id = args.SPREADSHEET
    sheet_name = args.SHEET
    google_credentials = args.credentials
    csv_file = args.output

    # sheets = Sheets.from_files("~/client_secrets.json", "~/storage.json")
    sheets = Sheets.from_files(google_credentials, "storage.json")

    marking = sheets[spreadsheet_id].find(sheet_name)

    marking.to_csv(csv_file, encoding="utf-8", dialect="excel")

    logging.info(f"Finished...")
