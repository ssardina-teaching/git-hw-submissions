"""
Check which repos have wrongly merged PR and forced pushed reported in the PR

This is useful to handle teh Feedeback PRs #1 from GitHub Classroom, where students are supposed to fix their code

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html
Other doc on PyGithub: https://www.thepythoncode.com/article/using-github-api-in-python
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import csv
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

CSV_MERGED = "pr_forced.csv"
CSV_FORCED_PUSH = "pr_forced_push.csv"


def backup_file(file_path: str):
    if os.path.exists(file_path):
        logging.info(f"Backing up {file_path}...")
        time_now = util.get_time_now()
        os.rename(file_path, f"{file_path}-{time_now}.bak")


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
    merged_pr = []
    forced_pr = []  # repos that have forced push
    for k, r in enumerate(list_repos):
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"https://github.com/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)
        try:
            pr_feedback = repo.get_pull(number=1)  # get the first PR - feedback
            if pr_feedback.merged:
                logging.info(f"\t PR Feedback merged!!! {pr_feedback}")
                merged_pr.append(repo_id)

            # check for forced push
            for event in pr_feedback.get_issue_events():
                if event.event == "head_ref_force_pushed":
                    logging.warning(f"\t PR Feedback force pushed!!! {pr_feedback}")
                    forced_pr.append(repo_id)
                    break
        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
            no_errors += 1

    logging.info(
        f"Finished! Total repos: {no_repos} - Merged/foced wrongly: {len(merged_pr)}/{len(forced_pr)} - Errors: {no_errors}."
    )
    logging.info(f"Repos that closed the Feedback PR: \n\t {merged_pr}.")
    logging.info(f"Repos that have forced push: \n\t {forced_pr}.")

    # Write merged_pr data to CSV file
    backup_file(CSV_MERGED)
    with open(CSV_MERGED, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID"])
        writer.writerows([[repo_id] for repo_id in merged_pr])

    backup_file(CSV_FORCED_PUSH)
    with open(CSV_FORCED_PUSH, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID"])
        writer.writerows([[repo_id] for repo_id in forced_pr])

    logging.info(f"Merged PR data written to {CSV_MERGED}.")
