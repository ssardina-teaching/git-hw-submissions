"""
Check which repos are missing PR #1 for Feedback from GitHub Classroom, and create it

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html
Other doc on PyGithub: https://www.thepythoncode.com/article/using-github-api-in-python
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import base64
import csv
import re
import traceback
import os

from argparse import ArgumentParser
import util
from typing import List

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException

import logging
import coloredlogs

# get the TIMEZONE to be used - works with Python < 3.9 via pytz and 3.9 via ZoneInfo
TIMEZONE_STR = "Australia/Melbourne"
from datetime import datetime

# this should work Python 3.9+
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo(TIMEZONE_STR)


LOGGING_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE = "%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL = logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)
CSV_HEADER = ["REPO_ID", "AUTHOR", "COMMITS", "ADDITIONS", "DELETIONS"]

GH_URL_PREFIX = "https://github.com/"

CSV_MERGED = "missing_pr.csv"

BASE_SHA = "a7b3d7aee55d00d55ee29b8a505d17fc8283e9f8"

if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("REPO_CSV", help="List of repositories to get data from.")
    parser.add_argument(
        "--repos", nargs="+", help="if given, only the teams specified will be parsed."
    )
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")

    # Get the list of TEAM + GIT REPO links from csv file
    list_repos = util.get_repos_from_csv(args.REPO_CSV, args.repos)

    if len(list_repos) == 0:
        logging.error(
            f'No repos found in the mapping file "{args.REPO_CSV}". Stopping.'
        )
        exit(0)

    ###############################################
    # Authenticate to GitHub
    ###############################################
    if not args.token_file and not (args.user or args.password):
        logging.error("No authentication provided, quitting....")
        exit(1)
    try:
        g = util.open_gitHub(token_file=args.token_file)
    except:
        logging.error(
            "Something wrong happened during GitHub authentication. Check credentials."
        )
        exit(1)

    ###############################################
    # Process each repo in list_repos
    ###############################################
    authors_stats = []
    no_repos = len(list_repos)
    no_merged = 0
    no_errors = 0
    missing_pr = []
    for k, r in enumerate(list_repos):
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"https://github.com/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)
        try:
            pr_feedback_not_found = True
            prs = repo.get_pulls(sort='created')  # get the first PR - feedback
            for pr in prs:
                if pr.title == "Feedback":
                    pr_feedback_not_found = False
                    break
            

            if pr_feedback_not_found:
                logging.info(f"\t PR Feedback missing!!! Creating it...")
                missing_pr.append(repo_id)

                try:
                    repo.create_git_ref('refs/heads/feedback', BASE_SHA)
                except GithubException as e:
                    if e.data["message"] == "Reference already exists":
                        logging.info(f"\t Branch feedback already exists.")
                    else:
                        logging.error(f"\t Error creating branch feedback: {e}")
                        no_errors += 1
                        break
                        
                try:
                    repo.create_pull(
                        title="Feedback",
                        body="This is the PR for feedback.",
                        head="main",
                        base="feedback",
                    )
                except GithubException as e:
                    if e.data["message"] == "Validation Failed":
                        logging.error(f"\t Perhaps no commits exist in repo.")
                        no_errors += 1
                    else:
                        logging.error(f"\t Error creating PR Feedback: {e}")
                        no_errors += 1
                        break


                prs = repo.get_pulls(sort='created')  # get the first PR - feedback
                for pr in prs:
                    if pr.title == "Feedback" and pr.number != 1:
                        logging.info(f"\t PR Feedback not number 1. Watch out in autograding!!!")
                    

        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
            no_errors += 1

    logging.info(
        f"Finished! Total repos: {no_repos} - Missing PR: {len(missing_pr)} - Errors: {no_errors}."
    )
    logging.info(f"Repos without the Feedback PR: \n\t {missing_pr}.")

    # Write merged_pr data to CSV file
    with open(CSV_MERGED, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID"])
        writer.writerows([[repo_id] for repo_id in missing_pr])

    logging.info(f"Merged PR data written to {CSV_MERGED}.")
