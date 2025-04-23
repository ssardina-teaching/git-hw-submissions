"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html

Library uses REST API: https://docs.github.com/en/rest

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2019-2023"

import base64
import csv
from pathlib import Path
import re
import traceback
import os

from argparse import ArgumentParser
from typing import List

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException
from more_itertools import collapse

# local utilities
import util
from util import (
    GH_GIT_URL_PREFIX,
    TIMEZONE,
    UTC,
    NOW,
    NOW_ISO,
    NOW_TXT,
    LOGGING_DATE,
    LOGGING_FMT,
    GH_HTTP_URL_PREFIX,
    DATE_FORMAT,
)

import logging
import coloredlogs

LOGGING_LEVEL = logging.INFO
# LOGGING_LEVEL = logger.DEBUG
# logger.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
logger = logging.getLogger(__name__)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)


CSV_HEADER = ["REPO", "AUTHOR", "SHA", "DATE", "MESSAGE", "ADDITIONS", "DELETIONS", "URL"]
CSV_HEADER_STATS = ["REPO", "AUTHOR", "COMMITS", "ADDITIONS", "DELETIONS"]
GH_URL_PREFIX = "https://github.com/"
IGNORE_USERS = [
    # "ssardina",
    "web-flow",
    "github-classroom[bot]",
    "axelahmer",
    "AndrewPaulChester",
    "gourdoni",
]


def get_contributions(repo: Repository):
    """Use GH contribution API to get the contributions of each author
    Also return total number of contributions in repo

    Args:
        repo (Repository): handle to GitHub repository

    Returns:
        number of commits in repo
        dict author -> number of commits
        dict author -> number of additions
        dict author -> number of deletions
    """
    author_total = {}
    author_add = {}
    author_del = {}

    for contribution in repo.get_stats_contributors():
        if contribution.author.login in IGNORE_USERS:
            continue
        # get the author of the contribution stat
        author_id = contribution.author.login

        author_total[author_id] = contribution.total
        author_add[author_id] = -1
        author_del[author_id] = -1

    # get all commits in the repo
    no_commits = sum([author_total[author_id] for author_id in author_total])

    return no_commits, author_total, author_add, author_del


def get_commits(repo: Repository, sha: str = None) -> List[dict]:
    """
    Extracts all commits from a repo
    This will even parse commits that have no author login as it will extract base git commit email info

    Note: we need to traverse each branch to get all commits of various contributors.
        this is because using repo.get_stats_contributors() will only give us the contributions to the main branch!

    :param repo: handle to Repository
    :param sha: if given, up to that commit; otherwise parse all branches
    :return: list of dictionaries, each representing a commit data
    """
    repo_commits = set()

    # first we get all the commits from all branches we care about
    if sha is not None:  # a particular branch/sha has been given
        repo_commits = set(repo.get_commits(sha=sha))
    else:
        repo_branches = repo.get_branches()
        for branch in repo_branches:
            name_branch = branch.name
            logger.debug("Processing branch: ", name_branch)
            branch_commits = list(repo.get_commits(sha=name_branch))
            repo_commits = repo_commits.union(
                branch_commits
            )  # union bc there will be same shared sha commits

    # Now we have all commits in repo_commits, extract relevant data
    # we will collect all the commits in the repo here
    commits_data: List[dict] = []

    # c is <class 'github.Commit.Commit'> https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html
    for c in repo_commits:
        author = c.author.login if c.author else f"name({c.commit.author.name})"

        if author in IGNORE_USERS:
            continue

        sha = c.sha
        message = c.commit.message.strip().replace("\n", " ")
        url = c.html_url
        try:
            # commit_details = repo.get_commit(sha)
            commit_details = c
            additions = commit_details.stats.additions
            deletions = commit_details.stats.deletions
            date = commit_details.commit.author.date
            date = date.replace(tzinfo=UTC).astimezone(TIMEZONE)
        except Exception as e:
            logger.debug(f"Error getting commit details: {e}")
            additions = deletions = 0  # Fallback if details aren't available

        commits_data.append(
            {
                "AUTHOR": author,
                "SHA": sha,
                "DATE": date,
                "MESSAGE": message,
                "ADDITIONS": additions,
                "DELETIONS": deletions,
                "URL": url,
            }
        )

    return commits_data


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Extract no of commits per author in a collection of repositories given as a CSV file"
        "CSV HEADERS: ORG_NAME, REPO_ID_PREFIX, REPO_ID_SUFFIX, REPO_ID, REPO_GIT"
    )
    parser.add_argument("REPO_CSV", help="List of repositories to get data from.")
    parser.add_argument("CSV_OUT", help="File to output the stats of authors.")
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="if given, only the teams specified will be parsed.",
    )
    parser.add_argument(
        "--tag", help="if given, check up to a given tag (otherwise all repo)."
    )
    parser.add_argument(
        "--ignore",
        nargs="+",
        metavar="<list names>",
        help="ignore these authors GH usernames (teachers).",
    )
    parser.add_argument(
        "--gh-contributions",
        "-ghc",
        action="store_true",
        help="Use GitHub contribution to main stats (Default: %(default)s).",
    )
    args = parser.parse_args()
    logger.info(f"Starting on {TIMEZONE}: {NOW_ISO} - {args}")

    csv_file = Path(args.CSV_OUT)

    ###############################################
    # Filter repos as desired
    ###############################################
    repos = util.get_repos_from_csv(args.REPO_CSV, args.repos)
    if len(repos) == 0:
        logger.warning(
            f'No repos found in the mapping file "{args.REPO_CSV}". Stopping.'
        )
        exit(0)

    ###############################################
    # Authenticate to GitHub
    ###############################################
    if not args.token_file and not (args.user or args.password):
        logger.error("No authentication provided, quitting....")
        exit(1)
    try:
        g = util.open_gitHub(token_file=args.token_file)
    except:
        logger.error(
            "Something wrong happened during GitHub authentication. Check credentials."
        )
        exit(1)

    if args.ignore is not None:
        # add the ignore users to the list of ignored users
        IGNORE_USERS.extend(args.ignore)

    logger.info(f"Will ignore the following users: {', '.join(IGNORE_USERS)}")

    # if the output csv exists, extend it with the new commits
    # for each repo get the latest commit done
    commits_previous_csv = []
    latest_commit = dict()
    if os.path.exists(csv_file):
        logger.info(
            f"Author file *{args.CSV_OUT}* exists. Extending it with the new commits: "
        )
        with open(args.CSV_OUT, "r") as f:
            csv_reader = csv.DictReader(f, fieldnames=CSV_HEADER)
            next(csv_reader)  # skip header
            commits_previous_csv = list(csv_reader)

        


    # Process each repo in repos - collect in list author_stats
    repos_commits = dict()
    no_repos = len(repos)
    # repos.sort(key=lambda tup: tup["REPO_ID_SUFFIX"].lower())
    for k, row in enumerate(repos, start=1):
        repo_no = row["NO"]
        repo_id = row["REPO_ID"]  # RMIT-COSC2978/ssardina
        repo_suffix = row["REPO_ID_SUFFIX"]  # ssardina
        repo_http_url = row["REPO_HTTP"]
        logger.info(f"Processing repo {repo_suffix} ({repo_http_url})...")

        logger.info(
            f"Processing {k}/{no_repos} repo {repo_no}:{repo_suffix} at {repo_http_url}"
        )

        try:
            repo = g.get_repo(repo_id)
            repos_commits[repo_suffix] = get_commits(repo, sha=args.tag)
        except Exception as e:
            logger.info(f"\t Exception repo {repo_suffix}: {e}")
            continue

        no_commits = len(repos_commits[repo_suffix])
        authors = set([c["AUTHOR"] for c in repos_commits[repo_suffix]])
        logger.info(
            f"\t Repo {repo_suffix} has {no_commits} commits from {len(authors)} authors: {authors}."
        )

    # repos_commits has all commits of all repos.
    #   key is repo suffix id
    #   value is a list of dictionaries with commit data

    # First, we add the repo id to each commit to prepare for CSV file
    author_stats_cvs = []
    for repo_id in repos_commits:
        # all the commits of the repo
        commits_repo = repos_commits[repo_id]

        # add the repo id to each commit
        for commit_data in commits_repo:
            commit_data["REPO"] = repo_id

        # build aggregated stats for the repo:
        #   repo, author, no_commits, no_additions, no_deletions
        authors = set([c["AUTHOR"] for c in commits_repo])
        for a in authors:
            # get all the commits of this author in this repo
            author_commits = [c for c in commits_repo if c["AUTHOR"] == a]
            # get the total number of commits
            no_commits = len(author_commits)
            # get the total number of additions and deletions
            no_additions = sum([c["ADDITIONS"] for c in author_commits])
            no_deletions = sum([c["DELETIONS"] for c in author_commits])
            # add to the list of authors stats
            author_stats_cvs.append(
                {
                    "REPO": repo_id,
                    "AUTHOR": a,
                    "COMMITS": no_commits,
                    "ADDITIONS": no_additions,
                    "DELETIONS": no_deletions,
                }
            )

    # flatten the commit data into a list of commits (each will carry its repo id now)
    commits_csv = commits_previous_csv
    for x in repos_commits.values():  # list containing lists of commits
        commits_csv.extend(x)  # flatten the list of lists

    # sort by repo id first, then author
    commits_csv.sort(key=lambda x: (x["REPO"], x["AUTHOR"]))

    # OK at this point we have two lists
    #   - commits_csv: all commits of all repos
    #   - author_stats_cvs: all authors stats of all repos

    # done

    # finally, write to csv the whole pack of rows (old and updated)
    with open(csv_file, "w") as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=CSV_HEADER)
        csv_writer.writeheader()
        csv_writer.writerows(commits_csv)

    csv_stat_file = csv_file.with_name(csv_file.stem + "_stats").with_suffix(".csv")
    with open(csv_stat_file, "w") as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=CSV_HEADER_STATS)
        csv_writer.writeheader()
        csv_writer.writerows(author_stats_cvs)
