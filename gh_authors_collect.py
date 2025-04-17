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
import re
import traceback
import os

from argparse import ArgumentParser

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException

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
    DATE_FORMAT
)

import logging
import coloredlogs
LOGGING_LEVEL = logging.INFO
# LOGGING_LEVEL = logger.DEBUG
# logger.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
logger = logging.getLogger(__name__)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)


CSV_HEADER = ["REPO_ID_SUFFIX", "AUTHOR", "COMMITS", "ADDITIONS", "DELETIONS"]
GH_URL_PREFIX = "https://github.com/"
IGNORE_USERS = [
    "ssardina",
    "web-flow",
    "github-classroom[bot]",
    "axelahmer",
    "AndrewPaulChester",
    "gourdoni",
]


def print_repo_info(repo):
    # repository full name
    print("Full name:", repo.full_name)
    # repository description
    print("Description:", repo.description)
    # the date of when the repo was created
    print("Date created:", repo.created_at)
    # the date of the last git push
    print("Date of last push:", repo.pushed_at)
    # home website (if available)
    print("Home Page:", repo.homepage)
    # programming language
    print("Language:", repo.language)
    # number of forks
    print("Number of forks:", repo.forks)
    # number of stars
    print("Number of stars:", repo.stargazers_count)
    print("-" * 50)
    # repository content (files & directories)
    print("Contents:")
    for content in repo.get_contents(""):
        print(content)
    try:
        # repo license
        print(
            "License:", base64.b64decode(repo.get_license().content.encode()).decode()
        )
    except:
        pass


def traverse_commit(c):
    set_c = set([c.sha])
    for c2 in c.parents:
        # print(c2.sha)
        set_2 = traverse_commit(c2)
        set_c = set_c.union(set_2)
    return set_c


def get_stats_contrib_repo(g: Github, repo_name, sha=None, gh_contributions=False):
    """
    Extracts commit stats for a repo up to some sha/tag by inspecting each commit
    This will even parse commits that have no author login as it will extract base git commit email info

    Note: we need to traverse each branch to get all commits of various contributors.
        this is because using repo.get_stats_contributors() will only give us the contributions to the main branch!

    :param g: handle to GitHub
    :param repo_name: name of the repository (owner + name)
    :param sha: if given, up to that commit; otherwise parse all branches
    :return: stats: no of total commits and dicts per author: no of commits, no of additions, no of deletions
    """
    # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=tag#github.Repository.Repository.get_git_tag
    repo = g.get_repo(repo_name)

    # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository.get_commit
    # first, collect ALL commits from ALL branches (if sha) for the contributors
    contributors = [
        x.login for x in repo.get_collaborators() if not x.login in IGNORE_USERS
    ]

    # now count each author contribution
    author_commits = {}
    author_additions = {}
    author_deletions = {}

    # method 1: use GH contributions to MAIN
    if gh_contributions:
        for contribution in repo.get_stats_contributors():
            if contribution.author.login in IGNORE_USERS:
                continue
            author_id = contribution.author.login

            author_commits[author_id] = contribution.total
            author_additions[author_id] = -1
            author_deletions[author_id] = -1
    else:
        # method 2: go over each commit in every branch
        #   this wil NOT get missconfigured usernames not correctly linked to GH accounts
        #   also will not get commits that are not in the main branch
        repo_commits = set()
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

        # c is <class 'github.Commit.Commit'> https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html
        for c in repo_commits:
            try:
                # c.author is a github.NamedUser.NamedUser - https://pygithub.readthedocs.io/en/latest/github_objects/NamedUser.html#github.NamedUser.NamedUser
                author_id = c.author.login
            except Exception as e:
                # Commits is not attached to a GitHub account, just get whatever text name was used
                author_id = f"name({c.commit.author.name})"

            if author_id in IGNORE_USERS:
                continue

            author_commits[author_id] = author_commits.get(author_id, 0) + 1
            author_additions[author_id] = (
                author_additions.get(author_id, 0) + c.stats.additions
            )
            author_deletions[author_id] = (
                author_deletions.get(author_id, 0) + c.stats.deletions
            )

    no_commits = sum([author_commits[author_id] for author_id in author_commits])

    return no_commits, author_commits, author_additions, author_deletions


def get_stats_contrib_repo_all(g: Github, repo_name):
    """
    Extracts commit stats for a whole repo (not commit per commit)
    This will ignore commits done by non registered authors

    :param g: handle to GitHub
    :param repo_name: name of the repository (owner + name)
    :return: stats: no of total commits and dicts per author: no of commits, no of additions, no of deletions
    """
    repo = g.get_repo(repo_name)

    no_commits = 0
    author_commits = {}
    author_additions = {}
    author_deletions = {}
    for contrib in repo.get_stats_contributors():
        no_commits += contrib.total
        author_id = contrib.author.login
        author_commits[author_id] = contrib.total
        author_additions[author_id] = sum([w.a for w in contrib.weeks])
        author_deletions[author_id] = sum([w.d for w in contrib.weeks])
    return no_commits, author_commits, author_additions, author_deletions


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

    logger.info(
        f"Will ignore the following users: {', '.join(IGNORE_USERS)}"
    )

    # Process each repo in list_repos
    authors_stats = []
    no_repos = len(repos)
    # repos.sort(key=lambda tup: tup["REPO_ID_SUFFIX"].lower())
    for k, row in enumerate(repos, start=1):
        repo_no = row["NO"]
        repo_id = row["REPO_ID_SUFFIX"] # ssardina
        repo_http_url = row["REPO_HTTP"]
        logger.info(f"Processing repo {repo_id} ({repo_http_url})...")

        logger.info(
            f"Processing {k}/{no_repos} repo {repo_no}:{repo_id} at {repo_http_url}"
        )

        try:
            no_commits, author_commits, author_add, author_del = get_stats_contrib_repo(
                g, row["REPO_ID"], sha=args.tag, gh_contributions=args.gh_contributions
            )
        except Exception as e:
            logger.info(f"\t Exception repo {repo_id}: {e}")
            continue
        logger.info(
            f"\t Repo {repo_id} has {no_commits} commits from {len(author_commits)} authors."
        )
        authors_stats.append((repo_id, author_commits, author_add, author_del))

    # Produce/Update CSV file output with all repos if requested via option --csv
    # first check if we are updating a file
    rows_to_csv = []
    if os.path.exists(args.CSV_OUT):
        logger.info(f"Updating teams in existing CSV file *{args.CSV_OUT}*.")
        with open(args.CSV_OUT, "r") as f:
            csv_reader = csv.DictReader(f, fieldnames=CSV_HEADER)

            next(csv_reader)  # skip header
            for row in csv_reader:
                if args.repos is not None and row["REPO_ID_SUFFIX"] not in args.repos:
                    rows_to_csv.append(row)
    else:
        logger.info(
            f"List of author stats will be saved to CSV file *{args.CSV_OUT}*."
        )

    # next build the rows for the repo inspected for update
    for x in authors_stats:  # x = (repo_name, dict_authors_commits)
        for author in x[1]:
            row = {}
            row["REPO_ID_SUFFIX"] = x[0]
            row["AUTHOR"] = author
            row["COMMITS"] = x[1][author]
            row["ADDITIONS"] = x[2][author]
            row["DELETIONS"] = x[3][author]
            rows_to_csv.append(row)

    # sort by repo id first, then author
    rows_to_csv.sort(key=lambda x: (x["REPO_ID_SUFFIX"], x["AUTHOR"]))

    # finally, write to csv the whole pack of rows (old and updated)
    with open(args.CSV_OUT, "w") as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=CSV_HEADER)
        csv_writer.writeheader()
        csv_writer.writerows(rows_to_csv)
