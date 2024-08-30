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
CSV_ISSUES = "issues_pr.csv"


MESSAGE_PR = """
:wave:! GitHub Classroom created this pull request as a place for your teacher to leave feedback on your work. It will update automatically. **Don’t close or merge this pull request**, unless you’re instructed to do so by your teacher.
 In this pull request, your teacher can leave comments and feedback on your code. Click the **Subscribe** button to be notified if that happens.
 Click the **Files changed** or **Commits** tab to see all of the changes pushed to `main` since the assignment started. Your teacher can see this too.
<details>
<summary>
<strong>Notes for teachers</strong>
</summary>

 Use this PR to leave feedback. Here are some tips:
 - Click the **Files changed** tab to see all of the changes pushed to `main` since the assignment started. To leave comments on specific lines of code, put your cursor over a line of code and click the blue **+** (plus sign). To learn more about comments, read “[Commenting on a pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/commenting-on-a-pull-request)”.
- Click the **Commits** tab to see the commits pushed to `main`. Click a commit to see specific changes.
- If you turned on autograding, then click the **Checks** tab to see the results.
- This page is an overview. It shows commits, line comments, and general comments. You can leave a general comment below.
 For more information about this pull request, read “[Leaving assignment feedback in GitHub](https://docs.github.com/education/manage-coursework-with-github-classroom/leave-feedback-with-pull-requests)”.
</details>


Subscribed: @{GH_USERNAME}
"""


# BASE_SHA = "a7b3d7aee55d00d55ee29b8a505d17fc8283e9f8"

if __name__ == "__main__":
    parser = ArgumentParser(description="Merge PRs in multiple repos")
    parser.add_argument("REPO_CSV", help="List of repositories to get data from.")
    parser.add_argument("BASE_SHA", help="Base SHA to create feedback branch from.")
    parser.add_argument(
        "--repos", nargs="+", help="if given, only the teams specified will be parsed."
    )
    parser.add_argument(
        "-t",
        "--token-file",
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not push to repos, just report on console %(default)s.",
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
    merged_pr = []
    errors_repo = []
    for k, r in enumerate(list_repos):
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"https://github.com/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)
        try:
            pr_feedback_not_found = True
            pr_feedback = repo.get_pull(number=1)  # get the first PR - feedback
            if pr_feedback.merged:
                logging.info(f"\t PR Feedback merged!!! {pr_feedback}")
                merged_pr.append(repo_id)
                continue
        except GithubException as e:
            if e.status == 404:
                logging.error(f"\t No Feedback PR #1 found in repo {repo_name}: {e}")
            missing_pr.append(repo_id)
            if args.dry_run:
                logging.info(
                    f"\t Dry run: Would create feedback branch at SHA {args.BASE_SHA} and Feedback PR with body: \n \t {MESSAGE_PR.format(GH_USERNAME=repo_id)}."
                )
                continue
            # create a feedback branch from the base SHA
            try:
                repo.create_git_ref("refs/heads/feedback", args.BASE_SHA)
            except GithubException as e:
                if e.data["message"] == "Reference already exists":
                    logging.info(f"\t Branch feedback already exists.")
                else:
                    logging.error(f"\t Error creating branch feedback: {e}")
                    errors_repo.append(repo)
                    break

            # create a PR for feedback
            try:
                repo.create_pull(
                    title="Feedback",
                    body=MESSAGE_PR.format(GH_USERNAME=repo.owner.login),
                    head="main",
                    base="feedback",
                )
            except GithubException as e:
                if e.data["message"] == "Validation Failed":
                    logging.error(f"\t Perhaps no commits exist in repo.")
                    errors_repo.append(repo)
                else:
                    logging.error(f"\t Error creating PR Feedback: {e}")
                    errors_repo.append(repo)
                    break

    logging.info(
        f"Finished! Total repos: {no_repos} - Merged PR: {len(merged_pr)} - Missing PR: {len(missing_pr)} - Errors: {no_errors}."
    )
    logging.info(f"Repos without the Feedback PR: \n\t {missing_pr}.")

    # Write merged_pr data to CSV file
    with open(CSV_ISSUES, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["REPO_ID", "ISSUE"])
        writer.writerows([[repo_id, "merged"] for repo_id in merged_pr])
        writer.writerows([[repo_id, "errors"] for repo_id in errors_repo])
        writer.writerows([[repo_id, "missing"] for repo_id in missing_pr])

    logging.info(f"Merged PR data written to {CSV_ISSUES}.")
