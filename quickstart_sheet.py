"""
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

$ python gg_get_worksheet.py 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms sasa
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import os
from argparse import ArgumentParser
from datetime import datetime
from zoneinfo import ZoneInfo  # this should work Python 3.9+

import logging
import coloredlogs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


# get the TIMEZONE to be used - works with Python < 3.9 via pytz and 3.9 via ZoneInfo
TIMEZONE_STR = "Australia/Melbourne"
TIMEZONE = ZoneInfo(TIMEZONE_STR)


LOGGING_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE = "%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL = logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)


def auth_google(credentials_file="credentials.json", scopes=None):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def quickstart_test(creds):
    """Example of how to get a worksheet from a Google Sheet.
    https://developers.google.com/sheets/api/quickstart/python
    """
    # The ID and range of a sample spreadsheet.
    SAMPLE_RANGE_NAME = "Class Data!A2:E"

    try:
        # get a sheet service
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            exit(0)

        print("Name, Major:")
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print(f"{row[0]}, {row[4]}")
    except HttpError as err:
        print(err)


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
    google_credentials = args.credentials

    # RUN QUICKSTART TEST
    creds = auth_google(google_credentials, SCOPES)
    quickstart_test(creds)

    logging.info(f"Finished...")
