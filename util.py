import csv
from github import Github, Repository, Organization, GithubException


def get_repos_from_csv(csv_file, team=None):
    """
    Collect list of teams with their git URL links from a csv file

    :param csv_file: file where csv data is with two fields TEAM and GIT
    :param team: the specific name of one team or None
    :return: a list of teams
    """
    teams_file = open(csv_file, 'r')
    # Get the list of teams with their GIT URL from csv file
    teams_reader = csv.DictReader(teams_file, delimiter=',')
    teams = list(teams_reader)
    teams_file.close()

    # If there was a specific team given, just keep that one in the list to clone just that
    if team is not None:
        teams = [t for t in teams if t[CSV_REPO_ID] == team]

    return teams


def open_gitHub(user=None, token_file=None, password=None):
    print(token_file)
    # Authenticate to GitHub
    if token_file:
        with open(token_file) as fh:
            token = fh.read().strip()
        g = Github(token)
    elif user and password:
        g = Github(user, password)
    return g
