import csv
from github import Github, Repository, Organization, GithubException

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
