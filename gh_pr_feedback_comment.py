"""
Issue marking comments to the Feedback PR of a student repo

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html
Other doc on PyGithub: https://www.thepythoncode.com/article/using-github-api-in-python

Example:

$ python gh_pr_feedback_comment.py repos.csv marking-p0.csv reports  -t ~/.ssh/keys/gh-token-ssardina.txt --repos s3975993 |& tee -a pr_feedback_remark.log
"""

__author__ = "Sebastian Sardina & Andrew Chester - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import csv
import os
from argparse import ArgumentParser
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo  # this should work Python 3.9+
from github import GithubException
import importlib.util
import sys

import util


import logging
import coloredlogs

# get the TIMEZONE to be used - works with Python < 3.9 via pytz and 3.9 via ZoneInfo
TIMEZONE_STR = "Australia/Melbourne"
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


FEEDBACK_MESSAGE = FEEDBACK_MESSAGE_P0


def load_marking_dict(file_path: str) -> dict:
    """
    Load the marking dictionary from a CSV file; keys are GH username
    """
    comment_dict = {}
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comment_dict[row["GHU"].lower()] = row
    return comment_dict


def issue_feedback_comment(pull, message, dry_run=False):
    if dry_run:
        print(message)
    else:
        return pull.create_comment(message)


if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("REPO_CSV", help="List of repositories to post comments to.")
    parser.add_argument("MARKING_CSV", help="List of student results.")
    parser.add_argument("REPORT_FOLDER", help="Folder containing student report files.")
    parser.add_argument(
        "CONFIG", help="Python file with the specific config for for assessment."
    )
    parser.add_argument(
        "--repos", nargs="+", help="if given, only the teams specified will be parsed."
    )
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument(
        "--start", "-s", type=int, help="repo no to start processing from."
    )
    parser.add_argument("--end", "-e", type=int, help="repo no to end processing.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not push to repos, just report on console %(default)s.",
    )
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")

    # Now load the report feedback module for the specific assessment being used
    # Load the module from the given path
    # https://medium.com/@Doug-Creates/dynamically-import-a-module-by-full-path-in-python-bbdf4815153e
    spec = importlib.util.spec_from_file_location("module_name", args.CONFIG)
    module_feedback = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_feedback)
    # Add the module to sys.modules
    sys.modules["module_name"] = module_feedback

    FEEDBACK_MESSAGE = getattr(module_feedback, "FEEDBACK_MESSAGE")
    report_feedback = getattr(module_feedback, "report_feedback")

    # Get the list of relevant repos from the CSV file
    list_repos = util.get_repos_from_csv(args.REPO_CSV, args.repos)
    if args.repos is None:
        start_no = args.start if args.start is not None else 0
        end_no = (args.end if args.end is not None else len(list_repos)) + 1
        list_repos = list_repos[start_no:end_no]

    logging.info(args)

    if len(list_repos) == 0:
        logging.error(
            f'No repos found in the mapping file "{args.REPO_CSV}". Stopping.'
        )
        exit(0)

    marking_dict = load_marking_dict(args.MARKING_CSV)

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
        repo_id = r["REPO_ID"].lower()
        repo_name = r["REPO_NAME"]
        # repo_url = f"https://github.com/{repo_name}"
        repo_url = r["REPO_HTTP"]
        logging.info(f"Processing repo {k+1}/{no_repos}: {repo_id} ({repo_url})...")

        if repo_id not in marking_dict:
            logging.error(f"\t Repo {repo_name} not found in {args.MARKING_CSV}.")
            no_errors += 1
            errors.append(repo_id)
            continue

        repo = g.get_repo(repo_name)
        try:
            # get the first PR - feedback
            #   see we cannot use .get_pull(1) bc it involves reviewing the PRs!
            pr_feedback = repo.get_issue(number=1)

            # get the marking data for the student/repo
            marking_repo = marking_dict[repo_id]
            if not marking_repo["COMMIT"]:
                logging.warning(f"\t Repo {repo_name} has no tag submission.")
                message = f"Dear @{repo_id}: no submission tag found; no marking as per spec. :cry:"
                issue_feedback_comment(pr_feedback, message, args.dry_run)
                continue
            elif marking_repo["CERTIFICATION"] != "Yes":
                logging.warning(f"\t Repo {repo_name} has no certification.")
                message = f"Dear @{repo_id}: no certification found; no marking as per spec. :cry:"
                issue_feedback_comment(pr_feedback, message, args.dry_run)
                continue

            # Now there is a proper submission; issue the autograder report & feedback summary
            # create a new comment with the automarker report
            file_report = f"{repo_id}.txt"  # default report filename
            if "REPORT" in marking_repo:
                file_report = marking_repo["REPORT"]
            with open(os.path.join(args.REPORT_FOLDER, file_report), "r") as report:
                report_text = report.read()

            message = (
                f"# Full autograder report \n\n ```{report_text}```\n{FEEDBACK_MESSAGE}"
            )
            issue_feedback_comment(pr_feedback, message, args.dry_run)

            # create a new comment with the final marking/feedback table results
            feedback_text = report_feedback(marking_repo)
            message = f"Dear @{repo_id}: find here the FEEDBACK & RESULTS for the project. \n\n {feedback_text}"
            issue_feedback_comment(pr_feedback, message, args.dry_run)
        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
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
