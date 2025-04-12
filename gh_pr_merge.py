"""
Script to merge a PR in all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html

Library uses REST API: https://docs.github.com/en/rest

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python
"""
__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2019-2023"

from argparse import ArgumentParser
from typing import List

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException

from util import (
    TIMEZONE,
    UTC,
    NOW,
    NOW_TXT,
    NOW_ISO,
    LOGGING_DATE,
    LOGGING_FMT,
    GH_URL_PREFIX,
)
from datetime import datetime

import logging
import coloredlogs
LOGGING_LEVEL = logging.INFO
# logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)


if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("REPO_CSV", help="List of repositories to get data from.")
    parser.add_argument(
        "--repos", nargs="+", help="if given, only the teams specified will be parsed."
    )
    parser.add_argument("--start", type=int, help="repo no to start processing from.")
    parser.add_argument("--end", type=int, help="repo no to end processing.")
    parser.add_argument("--no", type=int, help="number of the PR to merge.")
    parser.add_argument("--title", help="title of PR to merge.")
    parser.add_argument(
        "-t",
        "--token-file",
        required=True,
        help="File containing GitHub authorization token/password.",
    )
    args = parser.parse_args()

    logging.info(f"Starting on {TIMEZONE}: {NOW_ISO}\n")

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
    if args.end is not None and args.end < len(list_repos):
        list_repos = list_repos[: args.end]

    ###############################################
    # Authenticate to GitHub
    ###############################################
    if not args.token_file and not (args.user or args.password):
        logging.error("No authentication provided, quitting....")
        exit(1)
    try:
        g = util.open_gitHub(token_file=args.token_file)
    except Exception as e:
        logging.error(
            f"Something wrong happened during GitHub authentication. Check credentials. Exception: {e}"
        )
        exit(1)

    ###############################################
    # Process each repo in list_repos
    ###############################################
    authors_stats = []
    no_repos = len(list_repos)
    no_merged = 0
    no_errors = 0
    for k, r in enumerate(list_repos, start=1):
        if args.start is not None and k < args.start:
            continue
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"{GH_URL_PREFIX}/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)
        prs = repo.get_pulls(state="all", direction="desc")

        pr_selected = None
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
                if args.title in pr.title:
                    pr_selected = pr
                    break
            if pr_selected is None:
                logging.warning(f"\t No PR containing '{args.title}' in title.")
                continue

        logging.info(f"\t Found relevant PR: {pr_selected}")

        if pr_selected.merged:
            logging.info("\t PR already merged.")
            continue

        logging.info(f"\t PR is still not merged - will try to merge it: {pr_selected}")
        try:
            status = pr_selected.merge(merge_method="merge")
            if status.merged:
                logging.info("\t Successful merging...")
                no_merged += 1
            else:
                logging.error(f"\t MERGING DIDN'T WORK - STATUS: {status}")
                no_errors += 1
        except GithubException as e:
            logging.error(f"\t MERGING FAILED WITH EXCEPTION: {e}")
            no_errors += 1

    logging.info(
        f"Finished! Total repos: {no_repos} - Merged successfully: {no_merged} - Failed to merge: {no_errors}."
    )
