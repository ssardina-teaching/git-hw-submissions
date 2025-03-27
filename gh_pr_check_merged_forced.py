"""
Check which repos have wrongly merged PR or forced pushed reported in the PR

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
# LOGGING_LEVEL = logging.DEBUG
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)
CSV_HEADER = ["REPO_ID", "AUTHOR", "COMMITS", "ADDITIONS", "DELETIONS"]

GH_URL_PREFIX = "https://github.com"

CSV_MERGED = "pr_merged.csv"
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
    parser.add_argument("--no", type=int, help="number of the PR to merge.")
    parser.add_argument("--title", help="title of PR to merge.")
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")

    if args.no is None and args.title is None:
        logging.error("You must provide a PR number or title to merge.")
        exit(1)

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
    except Exception:
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
    for k, r in enumerate(list_repos, start=1):
        row = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"{GH_URL_PREFIX}/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {row} ({repo_url})...")

        repo = g.get_repo(repo_name)
        prs = repo.get_pulls(state="all", direction="desc")

        pr_selected = None
        try:
            if args.no is not None:
                if prs.totalCount < args.no:
                    logging.error(
                        f"\t No PR with number {args.no} - Repo has only {prs.totalCount} PRs."
                    )
                    exit(1)
                else:
                    pr_selected = repo.get_pull(args.no)
            else:
                for pr in prs:
                    logging.debug(f"\t PR: {pr.number} - {pr.title}")
                    if args.title in pr.title:
                        pr_selected = pr
                        break
                if pr_selected is None:
                    logging.warning(f"\t No PR containing '{args.title}' in title.")
                    continue
            logging.info(f"\t Found relevant PR: {pr_selected}")

            if pr_selected.merged:
                pr_url = f"{repo_url}/pull/{pr_selected.number}"
                logging.warning(f"\t PR Feedback merged!!! {pr_selected} - URL: {pr_url}")
                merged_pr.append([row, repo_name, pr_url])

            # check for forced push
            for event in pr_selected.get_issue_events():
                if event.event == "head_ref_force_pushed":
                    pr_url = f"{repo_url}/pull/{pr_selected.number}"
                    logging.warning(f"\t PR Feedback forcec pushed!!! {pr_selected} - actor: {event.actor} - URL: {pr_url}")
                    forced_pr.append([row, repo_name, pr_url])
                    break
        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
            no_errors += 1

    logging.info(
        f"Finished! Total repos: {no_repos} - Merged/foced wrongly: {len(merged_pr)}/{len(forced_pr)} - Errors: {no_errors}."
    )

    # Finally, write data to CSV file

    logging.info(f"Repos that closed the Feedback PR: \n\t {merged_pr}.")
    backup_file(CSV_MERGED)
    merged_pr.sort()
    with open(CSV_MERGED, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID", "REPO_NAME", "PR_URL"])
        writer.writerows([row for row in merged_pr])

    logging.info(f"Repos that have forced push: \n\t {forced_pr}.")
    backup_file(CSV_FORCED_PUSH)
    forced_pr.sort()
    with open(CSV_FORCED_PUSH, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID", "REPO_NAME", "PR_URL"])
        writer.writerows([row for row in merged_pr])

    for row in forced_pr:
        print(row[2])

    logging.info(f"Merged PR data written to {CSV_MERGED}.")
