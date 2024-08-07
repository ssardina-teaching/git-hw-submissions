"""
Check which repos have wrongly merged PR #1 for Feedback from GitHub Classroom

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

CSV_ERRORS = "errors_pr.csv"


def make_template(project, mapping):
    if project == "p0":
        return p0_template(mapping)


def p0_template(mapping):
    return f"""Project 0 results
===========

|                                          |                             |
|:-----------------------------------------|----------------------------:|
|**Student number:**                         | {mapping['STUDENT NO']} |
|**Student full name:**                      | {mapping['Preferred Name']} |
|**Github user:**                            | {mapping['GHU']} |
|**Git repo:**                               | {mapping['URL-REPO']} |
|**Timestamp submission:**                   | {mapping['TIMESTAMP']} |
|**Commit marked:**                          | {mapping['COMMIT']} |
|**No of commits:**                          | {mapping['NOCOM']} |
|**Commit ratio (<1 is bad)**                | {mapping['RATIO']} |
|**Days late (if any):**                     | {mapping['DYS LATE']} |
|**Certified (no certification = 0 marks)?** | {mapping['CERTIFICATION']} |
    
## Raw points
|                                       |                     |
|:--------------------------------------|--------------------:|
|**Q1:**                                | {mapping['Q1-TOT']} |
|**Q2:**                                | {mapping['Q2-TOT']} |
|**Q3:**                                | {mapping['Q3-TOT']} |
    
## Software Engineering (SE) (discount) weights
|                                       |                     |
|:--------------------------------------|--------------------:|
|**Merged feedback PR:**               | {mapping['PR-MERG']} |
|**Commits with invalid username:**    | {mapping['BAD-USR']} |
|**Commit quality:**                   | {mapping['SEPROB?']} |
    
## Summary of results
|                                       |                     |
|:--------------------------------------|--------------------:|
|**Raw points collected (out of 3):**  | {mapping['POINTS']} |
|**SE weight adjustment (1 if none):** | {mapping['WEIGHT']} |
|**Late penalty % (if any):**          | {mapping['LATE PEN']} |
|**Final marks (out of 100%):**        | {mapping['MARKS']} |
|**Grade:**                            | {mapping['GRADE']} |
|**Marking report:**                   | See comment before |
|**Notes (if any)**                    | {mapping['NOTE']} |
"""


def load_comment_dictionary(file_path: str) -> dict:
    """
    Load the comment dictionary from a CSV file
    """
    comment_dict = {}
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comment_dict[row["GHU"]] = make_template("p0", row)
    return comment_dict


if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("REPO_CSV", help="List of repositories to post comments to.")
    parser.add_argument("MARKING_CSV", help="List of student results.")
    parser.add_argument("REPORT_FOLDER", help="Folder containing student report files.")
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

    comments = load_comment_dictionary(args.MARKING_CSV)

    ###############################################
    # Authenticate to GitHub
    ###############################################
    if not args.token_file:
        logging.error("No token file for authentication provided, quitting....")
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
    errors = []
    for k, r in enumerate(list_repos):
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"https://github.com/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)
        try:
            pr_feedback = repo.get_issue(number=1)  # get the first PR - feedback

            # create a new comment with the automarker report
            with open(
                os.path.join(args.REPORT_FOLDER, f"{repo_id}.txt"), "r"
            ) as report:
                report_text = report.read()
            comment = pr_feedback.create_comment(
                f"# Full autograder report \n\n {report_text}"
            )

            # create a new comment with the final marking/feedback table results
            comment = pr_feedback.create_comment(comments[repo_id])
        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
            no_errors += 1
            errors.append(repo_id)
        except KeyError as e:
            logging.error(
                f"\t Error in repo {repo_name}: {repo_id} not found in {args.MARKING_CSV}."
            )
            no_errors += 1
            errors.append(repo_id)
        except FileNotFoundError as e:
            logging.error(
                f"\t Error in repo {repo_name}: report file {repo_id}.txt not found in {args.REPORT_FOLDER}."
            )
            no_errors += 1
            errors.append(repo_id)

    logging.info(f"Finished! Total repos: {no_repos} - Errors: {no_errors}.")

    with open(CSV_ERRORS, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows([[repo_id] for repo_id in errors])

    logging.info(f"Repos with errors written to {CSV_ERRORS}.")
