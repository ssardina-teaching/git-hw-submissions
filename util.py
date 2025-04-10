import csv
from github import Github, Repository, Organization, GithubException, Auth

import git


import datetime
import pytz

DATE_FORMAT = "%-d/%-m/%Y %-H:%-M:%-S"  # RMIT Uni (Australia)
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
TIMEZONE = pytz.timezone("Australia/Melbourne")


CSV_REPO_GIT = "REPO_URL"
CSV_REPO_ID = "REPO_ID"


def get_repos_from_csv(csv_file, repos_ids=None) -> list[dict]:
    """
    Collect list of teams with their git URL links from a CSV file.
    Case insensitive search for the repo ids.

    :param csv_file: file where csv data is with two fields TEAM and GIT
    :param repos_ids: list of specific repo names or None
    :return: a list of dictionaries for each repo (name, url, etc)
            e.g., {'ORG_NAME': 'RMIT-COSC1127-1125-AI24', 'ASSIGNMENT': 'p0-warmup', 'REPO_ID': 'msardina', 'REPO_NAME': 'RMIT-COSC1127-1125-AI24/p0-warmup-msardina', 'REPO_URL': 'git@github.com:RMIT-COSC1127-1125-AI24/p0-warmup-msardina.git'}
    """

    # Get the list of ALL teams with their GIT URL from the CSV file
    with open(csv_file, "r") as f:
        repos = list(csv.DictReader(f, delimiter=","))

    # Add enumeration as new field NO
    for i, t in enumerate(repos):
        t["NO"] = i + 1

    # If specific team ids given, just keep those them only
    if repos_ids is not None:
        repos = [
            t
            for t in repos
            if t[CSV_REPO_ID].lower() in list(map(str.lower, repos_ids))
        ]
    return repos


def open_gitHub(token_file=None, token=None, user=None, password=None):
    # Authenticate to GitHub
    if token:
        auth = Auth.Token(token)
        g = Github(auth=auth)
    if token_file:
        with open(token_file) as fh:
            token = fh.read().strip()
        g = Github(token)
    elif user and password:
        g = Github(user, password)
    return g


def get_tag_info(repo: git.Repo, tag_str="head"):
    """
    Returns the information of a tag in a repo. By default the head

    :param repo: the repository to search for a tag
    :param tag_str: the tag in the repo
    :return: the tag's commit time, the tag's commit, the time it was tagged
    """
    if tag_str == "head":
        commit = repo.commit()
        commit_time = datetime.datetime.fromtimestamp(
            commit.committed_date, tz=TIMEZONE
        )
        tagged_time = commit_time
    else:
        tag = next((tag for tag in repo.tags if tag.name == tag_str), None)
        # tag_commit = next((tag.commit for tag in repo.tags if tag.name == tag_str), None)
        if tag is None:
            return None, None, None
        commit = tag.commit

        commit_time = datetime.datetime.fromtimestamp(
            commit.committed_date, tz=TIMEZONE
        )
        try:
            tagged_time = datetime.datetime.fromtimestamp(
                tag.object.tagged_date, tz=TIMEZONE
            )  # if it is an annotated tag
        except:
            tagged_time = commit_time  # if it is a lightweight tag (no date stored; https://git-scm.com/book/en/v2/Git-Basics-Tagging)
        # logging.error("\t Repo {} does not have tag {}".format(repo, tag_str))

    return commit_time, commit, tagged_time
    # return commit_time.strftime(DATE_FORMAT), commit, tagged_time.strftime(DATE_FORMAT)


def get_time_now():
    return datetime.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d-%H-%M-%S")
