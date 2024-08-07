#!/user/bin/env python
"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python
"""
__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2019-2024"

import base64
import csv
import re
import traceback

from argparse import ArgumentParser
from github import GithubException
import logging
import util
import os
import time


CSV_GITHUB_USERNAME = "github_username"
CSV_GITHUB_IDENTIFIER = "identifier"

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%a, %d %b %Y %H:%M:%S",
)

import datetime
import pytz

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)
TIMEZONE = pytz.timezone("Australia/Melbourne")


def get_time_now():
    return datetime.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d-%H-%M-%S")


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


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Extract repos in a GitHub Classroom repositories for a given assignment into a CSV file"
        "CSV HEADERS: ORG_NAME, ASSIGNMENT, REPO_ID, REPO_NAME, REPO_GIT"
    )
    parser.add_argument("ORG_NAME", help="Organization name for GitHub Classroom")
    parser.add_argument("ASSIGNMENT_PREFIX", help="Prefix string for the assignment.")
    parser.add_argument("CSV", help="CSV file where to store the set of repo links.")
    parser.add_argument(
        "--token",
        default=os.environ.get("GHTOKEN"),
        help="File containing GitHub authorization token/password. Defaults to GHTOKEN env variable.",
    )
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument(
        "-m",
        "--student-map",
        help=f"CSV file mapping repo suffix ({CSV_GITHUB_USERNAME}) to "
        f"student ids ({CSV_GITHUB_IDENTIFIER}).",
    )
    args = parser.parse_args()
    print(args)
    print(f"Running the script on: {get_time_now()}", flush=True)

    REPO_URL_PATTERN = re.compile(
        r"^{}/{}-(.*)$".format(args.ORG_NAME, args.ASSIGNMENT_PREFIX)
    )

    ###############################################
    # Authenticate to GitHub
    ###############################################
    if not args.token_file and not args.token:
        logging.error(
            "No token or token file for authentication provided, quitting...."
        )
        exit(1)
    try:
        g = util.open_gitHub(token=args.token, token_file=args.token_file)
    except:
        logging.error(
            "Something wrong happened during GitHub authentication. Check credentials."
        )
        exit(1)

    # If --student-map is given, then it is an individual assignment and a mapping should be given
    # with columns identifier and github_username (the suffix of repos)
    user_to_id_map = dict()
    if args.student_map:
        with open(args.student_map, "r") as file:
            csv_content = csv.DictReader(file)
            for row in csv_content:
                row = dict(row)
                user_to_id_map[row[CSV_GITHUB_USERNAME]] = row[CSV_GITHUB_IDENTIFIER]
    else:
        logging.info(
            "No GitHub individual mapping provided. Team assignment; using suffix repo as identifier."
        )

    logging.info(
        "Dumping repos in organization *{}* for assignment *{}* into CSV file *{}*.".format(
            args.ORG_NAME, args.ASSIGNMENT_PREFIX, args.CSV
        )
    )

    # Get the repos of the organization and extract the ones matching the assignment prefix
    try:
        org = g.get_organization(args.ORG_NAME)
        org_repos = org.get_repos()
    except GithubException as e:
        logging.error(
            "There was an error trying to get the repos for organization {} "
            "(is the organization spelled correctly?): {}".format(args.ORG_NAME, e.data)
        )
        traceback.print_exc()
        exit(1)

    # collect all repos in the organization with the assignment prefix
    repos_select = []
    count = 0
    for repo in org_repos:
        match = re.match(REPO_URL_PATTERN, repo.full_name)
        if match:
            # repo_url = 'git@github.com:{}'.format(repo.full_name)
            count += 1
            print(f"Found repo {repo.full_name}")
            repos_select.append(
                {
                    "REPO_SUFFIX": match.group(1),
                    "REPO_NAME": repo.full_name,
                    "REPO_URL": repo.ssh_url,
                    "REPO_HTTP": repo.html_url,
                }
            )
    print(f"Number of repos found with prefix *{args.ASSIGNMENT_PREFIX}*:", count)

    # Produce CSV file output with all repos if requested via option --csv
    logging.info(f"List of repos will be saved to CSV file *{args.CSV}*.")
    with open(args.CSV, "w") as output_csv_file:
        csv_writer = csv.DictWriter(
            output_csv_file,
            fieldnames=[
                "ORG_NAME",
                "ASSIGNMENT",
                "REPO_ID",
                "REPO_NAME",
                "REPO_URL",
                "REPO_HTTP",
            ],
        )
        csv_writer.writeheader()

        # for each repo in repo_select produce a row in the CSV file, add the team name from mapping
        for row in repos_select:
            # if there is a mapping from a repo suffix to a REPO_ID, do it; otherwise use SUFFIX directly
            if args.student_map:
                if row["REPO_SUFFIX"] in user_to_id_map.keys():
                    row["REPO_SUFFIX"] = user_to_id_map[row["REPO_SUFFIX"]]
                else:
                    logging.warning(
                        f"Repo {row['REPO_NAME']} with suffix {row['REPO_SUFFIX']} has no mapping. Using suffix directly."
                    )

            row["ORG_NAME"] = args.ORG_NAME
            row["ASSIGNMENT"] = args.ASSIGNMENT_PREFIX
            row["REPO_ID"] = row.pop(
                "REPO_SUFFIX"
            ).lower()  # rename key REPO_SUFFIX to REPO_ID in the dictionary
            csv_writer.writerow(row)
