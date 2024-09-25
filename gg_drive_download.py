"""
 Download files from Google drive folder using the Google Drive API: https://developers.google.com/drive/api/guides/about-sdk
 
 Uses PyDrive2 for high-level access to the drive: https://docs.iterative.ai/PyDrive2/


To change credentials:
- Go to the Google API Access Pane (https://console.developers.google.com/apis/credentials)
- Create a project
- Create an OAuth consent screen
- Create credentials of type "OAuth Client ID"
- Download the JSON file of such credentials and name it "client_secrets.json"
- Place the file in the same directory as this file
"""

import os
import re
import argparse
from collections import defaultdict, namedtuple
import glob
import iso8601

from datetime import datetime
from zoneinfo import ZoneInfo  # this should work Python 3.9+
from pytz import timezone

# https://docs.iterative.ai/PyDrive2/
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

TIMEZONE_STR = "Australia/Melbourne"
CREDENTIALS_FILE = "storage.json"


def get_path_pieces_reversed(path):
    """
    Breaks a given path into a list (of str) of components in reversed order.
    :param path: The path to be broken
    :return: The pieces of the path in reverse order
    """
    pieces_reversed = []
    cur_path, cur_file = path, None
    while cur_path != "":
        cur_path, cur_file = os.path.split(cur_path)
        pieces_reversed.append(cur_file)
    return pieces_reversed


def get_children_by_id(drive, parent_id):
    """
    Gets a list of Google Drive files that are children of the parent with the given id.
    :param parent_id: The id of the parent directory
    :return:a list of Google Drive files that are children of the parent with the given id
    """
    return drive.ListFile(
        {"q": f"'{parent_id}' in parents and trashed=false"}
    ).GetList()


def get_id_by_absolute_path(path):
    """
    Given a path as a string, retrieves the id of the innermost component.
    :param path: The path to be analysed
    :return: The id of the innermost component
    """
    pieces_reversed = get_path_pieces_reversed(path)

    cur_list = get_children_by_id("root")
    final_id = None
    while pieces_reversed:
        target = pieces_reversed.pop()
        found = False
        for f in cur_list:
            if f["title"] == target:
                found = True
                if not pieces_reversed:
                    final_id = f["id"]
                else:
                    if f["mimeType"] == "application/vnd.google-apps.folder":
                        cur_list = get_children_by_id(f["id"])
                        break
                    else:
                        raise Exception(
                            "File encountered where a directory was expected: %s"
                            % target
                        )
        if not found:
            raise Exception("Directory not found: %s" % target)
    return final_id


"""
Download latest submission files in Google Drive folder with id gdrive_id with submission extension sub_ext (e.g., zip) 
to directory dir_destination. 
    If overwrite is true just replace ANY local copy. 
    If report_skip is true, do not report submissions that are skipped (because they already exist).
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script downloads all submission zip files in a directory in Google Drive.\n"
        "Notice that authentication on Google is required: the user will interactively\n"
        'be prompted to login. Credentials will be saved in the file "credentials.json".\n'
        "\n\n"
        "Example usage: python download_submissions.py --gdrive-path 'assessments/submissions/AI17 Submission - Project 0: Python Warmup (File responses)/Your submission package (File responses)' --csv-path 'p0-responses.csv'",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "FOLDER_ID",
        help="The folder in Google Drive where all submissions are located.",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        default=GoogleAuth.DEFAULT_SETTINGS["client_config_file"],
        help="File containing Google credentials (Default: %(default)s).",
    )
    parser.add_argument(
        "--webserver",
        action="store_true",
        help="Flag to enable webserver functionality for Google authentication (otherwise console-based).",
    )
    parser.add_argument(
        "--folder-path",
        type=str,
        default=None,
        help="The full path of the directory containing all the zip files in Google Drive.",
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

    args = parser.parse_args()
    print(args)

    output_dir = args.output

    # check output path exists
    if os.path.exists(output_dir):
        if not os.path.isdir(output_dir):
            raise Exception(f"Output path is not a directory: {output_dir}")
    else:
        raise Exception(f"Output path does not exists: {output_dir}")

    # if args.reset_credentials and os.path.exists(args.credentials):
    #     os.remove(args.credentials)

    GoogleAuth.DEFAULT_SETTINGS["client_config_file"] = args.credentials
    gauth = GoogleAuth()

    gauth.LoadCredentialsFile(CREDENTIALS_FILE)
    if gauth.credentials is None:
        if args.webserver:
            gauth.LocalWebserverAuth()  # Creates local web-server and auto handles authentication.
        else:
            gauth.CommandLineAuth()  # No webserver, use console
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile(CREDENTIALS_FILE)

    # Create GoogleDrive instance with authenticated GoogleAuth instance
    drive = GoogleDrive(gauth)

    # if a gdrive folder path is given, use that instead of the id (rare case)
    if args.folder_path is not None:
        # An absolute GDrive path was given, get the GDrive ID
        if args.folder_path.endswith("/"):
            args.folder_path = args.folder_path[:-1]
        folder_id = get_id_by_absolute_path(args.folder_path)
    else:
        folder_id = args.FOLDER_ID

    submission_entry = namedtuple("submission_entry", ["timestamp", "gdrive_id"])

    # Iterate thought all submitted files in the GDrive and extract the latest submission for each student
    #   Store that into latest_submissions
    files_in_submission_folder = get_children_by_id(drive, folder_id)

    # TODO: rename to latest_submissions
    latest_submissions = defaultdict(submission_entry)
    for f in files_in_submission_folder:
        email = f["lastModifyingUser"]["emailAddress"]
        submission_timestamp = iso8601.parse_date(f["createdDate"]).astimezone(
            timezone(TIMEZONE_STR)
        )
        # convert timestamp to melbourne time zone
        # see: http://www.saltycrane.com/blog/2009/05/converting-time-zones-datetime-objects-python/

        if (
            email not in latest_submissions
            or latest_submissions[email].timestamp < submission_timestamp
        ):
            latest_submissions[email] = submission_entry(
                timestamp=submission_timestamp, gdrive_id=f["id"]
            )
    no_submissions = len(latest_submissions)
    print(f"Number of submissions identified: {no_submissions}")
    # print(latest_submissions.keys())

    # Next, we download everything in latest_submissions form Gdrive
    for i, email in enumerate(
        latest_submissions
    ):  # i is 0,1,2,3... and student_id is "s3844647"
        # get submission timestamp and Google Drive id to the document
        latest_submission_timestamp, gdrive_id = latest_submissions[email]

        gdrive_file = drive.CreateFile({"id": latest_submissions[email].gdrive_id})
        destination_folder = os.path.join(output_dir, email)
        file_name = (
            args.file_name if args.file_name is not None else gdrive_file["title"]
        )
        destination_file = os.path.join(destination_folder, file_name)

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        print(
            f"Downloading submission {i}/{no_submissions} for {email} to {destination_file}: https://drive.google.com/open?id={gdrive_id}"
        )
        gdrive_file.GetContentFile(destination_file)
