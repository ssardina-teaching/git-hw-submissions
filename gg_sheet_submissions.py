"""Get the worksheet of a Google Sheet

This is done using GSHEETS package: https://gsheets.readthedocs.io/en/stable/index.html

    this package provides an easier access to the Google Sheet API:

    https://developers.google.com/sheets/api/guides/concepts


    Google API: https://developers.google.com/drive/api/guides/about-sdk

Example to download the MARKING sheet from the Google Sheet with ID 16wc.....:

$ python ~/git/courses/tools/git-hw-submissions.git/gg_sheet_submissions.py -c ~/.ssh/keys/credentials.json \
    1L69aPjMKa7rx1gtQYJXAs2V0TG71-cVZzL0dSpNFXGQ MATH24 submissions \
    --column-id D --column-file J


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
import os
from zoneinfo import ZoneInfo  # this should work Python 3.9+

import logging
import coloredlogs

from gsheets import Sheets

# https://docs.iterative.ai/PyDrive2/
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

CREDENTIALS_FILE = "storage.json"


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
    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="Directory where the submissions should be downloaded (Default: %(default)s).",
    )
    parser.add_argument(
        "--file-name",
        type=str,
        help="Rename the downloaded name to this",
    )
    parser.add_argument(
        "--column-id",
        type=str,
        default="D",
        help="Column where the submission id is recorded (e.g., student number) (Default: %(default)s).",
    )
    parser.add_argument(
        "--column-file",
        type=str,
        default="G",
        help="Column where the link to the file to download is located (Default: %(default)s).",
    )

    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")
    logging.info(args)

    spreadsheet_id = args.SPREADSHEET
    sheet_name = args.SHEET
    google_credentials = args.credentials
    csv_file = args.csv
    output_dir = args.OUTPUT

    # check output path exists
    if os.path.exists(output_dir):
        if not os.path.isdir(output_dir):
            raise Exception(f"Output path is not a directory: {output_dir}")
    else:
        raise Exception(f"Output path does not exists: {output_dir}")

    # get a handle to google sheets via authenticate gsheets
    gg_sheets = Sheets.from_files(
        google_credentials, CREDENTIALS_FILE, no_webserver=not args.webserver
    )

    # get a handle to google drive via authenticate PyDrive2
    GoogleAuth.DEFAULT_SETTINGS["client_config_file"] = args.credentials
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(CREDENTIALS_FILE)
    gg_drive = GoogleDrive(gauth)

    sheet = gg_sheets[spreadsheet_id].find(sheet_name)
    sheet.to_csv(csv_file, encoding="utf-8", dialect="excel")
    logging.info(f"Sheet saved to {csv_file}")

    no_rows = sheet.nrows
    print(f"Number of rows in sheet {sheet_name}: ", no_rows)

    for i in range(2, no_rows + 1):
        timestamp = sheet[f"A{i}"]
        email = sheet[f"B{i}"]
        student_no = str(sheet[f"{args.column_id}{i}"])
        file_link = sheet[
            f"{args.column_file}{i}"
        ]  # https://drive.google.com/open?id=1D8TPBz3o9Klu2wwlKKxCpvxNFSCaPPhb
        file_id = file_link.split("=")[
            1
        ]  # extract the id 1D8TPBz3o9Klu2wwlKKxCpvxNFSCaPPhb
        # print(f"Row {i}:", timestamp, email, student_no, file_id)

        gdrive_file = gg_drive.CreateFile({"id": file_id})
        file_title = gdrive_file["title"]

        destination_folder = os.path.join(output_dir, student_no)
        file_name = args.file_name if args.file_name is not None else file_title
        destination_file = os.path.join(destination_folder, file_name)

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        print(
            f"Downloading submission {i}/{no_rows} for {email} ({student_no}) to {destination_file}: {file_link}"
        )
        gdrive_file.GetContentFile(destination_file)

    logging.info(f"Finished...")
