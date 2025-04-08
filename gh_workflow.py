"""
Script to manage automarking/feedback workflows, like the ones used in GH Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html

Library uses REST API: https://docs.github.com/en/rest

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python
"""
__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024-2025"
import csv
import os
from argparse import ArgumentParser
import util

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException

# get the TIMEZONE to be used - ZoneInfo requires Python 3.9+
TIMEZONE_STR = "Australia/Melbourne"    # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
from datetime import datetime
from zoneinfo import ZoneInfo # Python 3.9+
TIMEZONE = ZoneInfo(TIMEZONE_STR)
UTC = ZoneInfo("UTC")


import logging
import coloredlogs
LOGGING_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE = "%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL = logging.INFO
LOGGING_LEVEL = logging.DEBUG
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)
CSV_HEADER = ["REPO_ID", "AUTHOR", "COMMITS", "ADDITIONS", "DELETIONS"]

GH_URL_PREFIX = "https://github.com"

CSV_OUTPUT = "workflows.csv"


def backup_file(file_path: str):
    if os.path.exists(file_path):
        logging.info(f"Backing up {file_path}...")
        time_now = util.get_time_now()
        os.rename(file_path, f"{file_path}-{time_now}.bak")


if __name__ == "__main__":
    parser = ArgumentParser(description="Start automarking workflows")
    parser.add_argument("REPO_CSV", help="List of repositories to get data from.")
    parser.add_argument(
        "--repos", 
        nargs="+", 
        help="if given, only the teams specified will be parsed."
    )
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument("--name", help="title of workflow to start.")
    parser.add_argument("--commit",
                        default="main",
                        help="commit or branch to execute it on %(default)s.")
    parser.add_argument("--until", 
                        help="Last commit before this date. Datetime in ISO format, e.g., 2025-04-09T15:30. Overrides --commit.")
    args = parser.parse_args()

    now = datetime.now(TIMEZONE).isoformat()
    logging.info(f"Starting on {TIMEZONE}: {now}\n")

    if args.name is None:
        logging.error("You must provide a name for the workflow to run.")
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
    until_dt = None
    if args.until is not None:
        until_dt = datetime.fromisoformat(args.until)
        print(until_dt.tzinfo)
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=TIMEZONE)
        logging.info(f"Will run workflow on last commit before date: {until_dt.isoformat()} - UTC: {until_dt.astimezone(UTC).isoformat()}")
    
    commit = args.commit
    authors_stats = []
    no_repos = len(list_repos)
    workflows_csv = []
    no_errors = 0
    for k, r in enumerate(list_repos, start=1):
        row = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"{GH_URL_PREFIX}/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {row} ({repo_url})...")

        try:
            repo = g.get_repo(repo_name)

            # override commit if --until is given: get latest commit before until_dt
            if until_dt is not None:
                commits = repo.get_commits(until=until_dt.astimezone(UTC))
                if commits.totalCount == 0:
                    logging.info(f"\t No commits found before {until_dt.isoformat()}.")
                    continue
                commit = commits[0].sha # last commit before until_dt
                logging.debug(f"\t Commit SHA to run workflow: {commit} - {commits[0].commit.author.date.astimezone(until_dt.tzinfo).isoformat()}")

            # get all workshops and find the one we are looking for (contains args.name)
            workflows = repo.get_workflows()
            workflow_selected = None
            print(workflows)
            for w in workflows:
                    logging.info(
                        f"\t Found workflow ({w}) - Starting it on commit {commit}"
                    )
                    workflow_selected = w
                    break

            if workflow_selected is None:
                logging.info(f"\t Workflow *{args.name}* not in {repo_name} - {repo_url}.")
                continue

            # we found the workflow, now run it on commit sha   !
            result = None
            if workflow_selected is not None:
                # https://pygithub.readthedocs.io/en/latest/github_objects/Workflow.html
                result = workflow_selected.create_dispatch(commit)
                if not result:
                    logging.error(
                        f"\t Workflow *{workflow_selected.name}* failed to start."
                    )
                    no_errors += 1
            else:
                no_errors += 1
            workflows_csv.append([row, repo_name, repo_url, result])
        except GithubException as e:
            logging.error(f"\t Error in repo {repo_name}: {e}")
            no_errors += 1

    logging.info(f"Finished! Total repos: {no_repos} - Errors: {no_errors}")

    workflows_csv.sort()
    with open(CSV_OUTPUT, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID", "REPO_NAME", "REPO_URL", "RESULT"])
        writer.writerows([row for row in workflows_csv])

    for row in workflows_csv:
        print(row)

    logging.info(f"Workflow results data written to {CSV_OUTPUT}.")
