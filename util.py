import csv
from github import Github, Repository, Organization, GithubException

import git


import datetime
import pytz
DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)
DATE_FORMAT = '%d/%m/%Y %H:%M:%S' 
TIMEZONE = pytz.timezone('Australia/Melbourne')


CSV_REPO_GIT = 'REPO_URL'
CSV_REPO_ID = 'REPO_ID'

def get_repos_from_csv(csv_file, team_ids=None):
    """
    Collect list of teams with their git URL links from a csv file

    :param csv_file: file where csv data is with two fields TEAM and GIT
    :param team_ids: list of specific names or None
    :return: a list of teams, each team is a dictionary with info (name, url, etc)
    """

    # Get the list of ALL teams with their GIT URL from the CSV file
    with open(csv_file, 'r') as f:
        teams_reader = csv.DictReader(f, delimiter=',')
        teams = list(teams_reader)

    # If specific team ids given, just keep those them only
    if team_ids is not None:
        teams = [t for t in teams if t[CSV_REPO_ID] in team_ids]

    return teams


def open_gitHub(user=None, token_file=None, password=None):
    # Authenticate to GitHub
    if token_file:
        with open(token_file) as fh:
            token = fh.read().strip()
        g = Github(token)
    elif user and password:
        g = Github(user, password)
    return g



def get_tag_info(repo:git.Repo, tag_str="head"):
    """
    Returns the information of a tag in a repo. By default the head

    :param repo: the repository to search for a tag
    :param tag_str: the tag in the repo
    :return: the tag's commit time, the tag's commit, the time it was tagged
    """
    if tag_str == "head":
        commit = repo.commit()
        commit_time = datetime.datetime.fromtimestamp(commit.committed_date, tz=TIMEZONE)
        tagged_time = commit_time
    else:
        tag = next((tag for tag in repo.tags if tag.name == tag_str), None)
        # tag_commit = next((tag.commit for tag in repo.tags if tag.name == tag_str), None)
        if tag is None:
            return None, None, None
        commit = tag.commit

        commit_time = datetime.datetime.fromtimestamp(commit.committed_date, tz=TIMEZONE)
        try:
            tagged_time = datetime.datetime.fromtimestamp(tag.object.tagged_date, tz=TIMEZONE)  # if it is an annotated tag
        except:
            tagged_time = commit_time  # if it is a lightweight tag (no date stored; https://git-scm.com/book/en/v2/Git-Basics-Tagging)
        # logging.error("\t Repo {} does not have tag {}".format(repo, tag_str))

    return commit_time, commit, tagged_time
    # return commit_time.strftime(DATE_FORMAT), commit, tagged_time.strftime(DATE_FORMAT)


def get_time_now():
    return datetime.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d-%H-%M-%S")


