"""
Check which repos are missing PR #1 for Feedback from GitHub Classroom; create PR if needed

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html
Other doc on PyGithub: https://www.thepythoncode.com/article/using-github-api-in-python
"""

__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2024"

import csv

from argparse import ArgumentParser
import util
from typing import List

# https://pygithub.readthedocs.io/en/latest/introduction.html
from github import Github, Repository, Organization, GithubException

import logging
import coloredlogs

from datetime import datetime
from zoneinfo import ZoneInfo  # this should work Python 3.9+

TIMEZONE_STR = "Australia/Melbourne"
TIMEZONE = ZoneInfo(TIMEZONE_STR)


LOGGING_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE = "%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL = logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)

GH_URL_PREFIX = "https://github.com/"
CSV_ISSUES = "pr_errors.csv"
CSV_MISSING = "pr_missing.csv"


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
        required=True,
        help="File containing GitHub authorization token/password.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not push to repos, just report on console (Default: %(default)s.)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        default=False,
        help="Dump results into CSV files (Default: %(default)s.)",
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
    missing_pr = []
    errors = []
    for k, r in enumerate(list_repos):
        repo_id = r["REPO_ID"]
        repo_name = r["REPO_NAME"]
        repo_url = f"https://github.com/{repo_name}"
        logging.info(f"Processing repo {k}/{no_repos}: {repo_id} ({repo_url})...")

        repo = g.get_repo(repo_name)

        # first check that no force-pushed has over-written main branch
        commits = repo.get_commits("main")
        first_commit_main = commits[commits.totalCount - 1]
        if first_commit_main.sha != args.BASE_SHA:
            logging.error(f"\t First commit is different from expected, forced pushed?")
            errors.append([repo_id, repo_url, "forced", first_commit_main.sha])
            continue

        # OK first commit in main exists, let's check if the PR exists and create it if not
        try:
            pr_feedback = repo.get_pull(number=1)  # get the first PR - feedback

            if pr_feedback.title != "Feedback":
                logging.error(f"\t PR with different title {pr_feedback.title}")
                errors.append([repo_id, repo_url, "title", pr_feedback.title])
                continue

            if pr_feedback.merged:
                logging.info(f"\t PR Feedback merged!!! {pr_feedback}")
                errors.append([repo_id, repo_url, "merged", ""])
                continue
        except GithubException as e:
            if e.status == 404:
                logging.error(
                    f"\t No Feedback PR #1 found in repo {repo_name}. We will create it..."
                )
            else:
                logging.error(f"\t Unknown getting PR Feedback: {e}")
                errors.append([repo_id, repo_url, "get-PR", e])
                continue

            # we know PR is missing, so we will create it
            if args.dry_run:
                # logging.info(
                #     f"\t Dry run!!!: Would create feedback branch at SHA {args.BASE_SHA} and Feedback PR with body: \n \t {MESSAGE_PR.format(GH_USERNAME=repo_id)}."
                # )
                logging.info(
                    f"\t Dry run!!!: Would create feedback branch at SHA {args.BASE_SHA} and Feedback PR."
                )
                missing_pr.append([repo_id, repo_url, "dry-run", ""])
                continue

            # first, create a feedback branch from the base SHA
            try:
                repo.create_git_ref("refs/heads/feedback", args.BASE_SHA)
            except GithubException as e:
                if e.data["message"] == "Reference already exists":
                    logging.info(f"\t Branch feedback already exists.")
                else:
                    logging.error(f"\t Error creating branch feedback: {e}")
                    errors.append([repo_id, repo_url, "create-branch", e])
                    continue

            # second, create a PR for feedback branch
            try:
                repo.create_pull(
                    title="Feedback",
                    body=MESSAGE_PR.format(GH_USERNAME=repo_id),
                    head="main",
                    base="feedback",
                )
            except GithubException as e:
                logging.error(f"\t Exception when creating PR in repo {repo_name}: {e}")
                missing_pr.append([repo_id, repo_url, "pr-create", e])
                if e.data["message"] == "Validation Failed":
                    logging.error(f"\t Perhaps no commits exist in repo.")
                    errors.append([repo_id, repo_url, "validation-pr", e])
                else:
                    errors.append([repo_id, repo_url, "create-pr", e])
                    break
                continue

                # all good!
            missing_pr.append([repo_id, repo_url, "created", ""])

    # print summary stats
    no_merged = len([x for x in errors if x[2] == "merged"])
    logging.info(
        f"Finished! Total repos: {no_repos} - Merged PR: {no_merged} - Missing PR: {len(missing_pr)} - Errors: {len(errors)}."
    )
    if missing_pr:
        logging.info(
            f"Repos without the Feedback PR: {' '.join([x[0] for x in missing_pr])}"
        )
        for r in missing_pr:
            print(r)
    else:
        logging.info(f"All repos have their Feedback PRs!")

    if args.csv:
        # Write error CSV file
        with open(CSV_ISSUES, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["REPO_ID", "REPO_URL", "ISSUE", "DETAILS"])
            writer.writerows(errors)
        logging.info(f"Errors written to {CSV_ISSUES}.")

        # Write error CSV file
        with open(CSV_MISSING, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["REPO_ID", "REPO_URL", "ISSUE", "DETAILS"])
            writer.writerows(errors)
        logging.info(f"Missing PR repos written to {CSV_MISSING}.")
