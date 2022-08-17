"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

PyGithub documentation: https://pygithub.readthedocs.io/en/latest/introduction.html

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python
"""
__author__      = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__   = "Copyright 2020"

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
LOGGING_FMT="%(asctime)s %(levelname)-8s %(message)s"
LOGGING_DATE="%a, %d %b %Y %H:%M:%S"
LOGGING_LEVEL=logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)
CSV_HEADER = ['REPO_ID', 'AUTHOR', 'COMMITS', 'ADDITIONS', "DELETIONS"]

GH_URL_PREFIX="https://github.com/"

IGNORE_USERS=["ssardina","web-flow", "github-classroom[bot]", "axelahmer", "AndrewPaulChester"]

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
    print("-"*50)
    # repository content (files & directories)
    print("Contents:")
    for content in repo.get_contents(""):
        print(content)
    try:
        # repo license
        print("License:", base64.b64decode(repo.get_license().content.encode()).decode())
    except:
        pass

def traverse_commit(c):
    set_c = set([c.sha])
    for c2 in c.parents:
        # print(c2.sha)
        set_2 = traverse_commit(c2)
        set_c = set_c.union(set_2)
    return set_c

def get_stats_contrib_repo(g : Github, repo_name, sha=None):
    '''
    Extracts commit stats for a repo up to some sha/tag by inspecting each commit
    This will even parse commits that have no author login as it will extract base git commit email info

    :param g: handle to GitHub
    :param repo_name: name of the repository (owner + name)
    :param sha: if given, up to that commit; otherwise parse all branches
    :return: stats: no of total commits and dicts per author: no of commits, no of additions, no of deletions
    '''
    # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html?highlight=tag#github.Repository.Repository.get_git_tag
    repo = g.get_repo(repo_name)
    
    # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository.get_commit
    # repo_commits = repo.get_commits(sha=sha) if sha is not None else repo.get_commits()
    if sha is not None:
        repo_commits = repo.get_commits(sha=sha)
    else:
        repo_branches = repo.get_branches()
        repo_commits = []
        for branch in repo_branches:
            name_branch = branch.name
            print(name_branch)
            commits_branch = repo.get_commits(sha=name_branch)
            for c in commits_branch:
                print(c)
            print(commits_branch.totalCount)
            repo_branches.append(commits_branch)
        
    
    
    no_commits = repo_commits.totalCount

    author_commits = {}
    author_additions = {}
    author_deletions = {}
    for c in repo_commits:
        try:
            author_id = c.author.login
        except:
            author_id = f'name({c.commit.author.name})'
            
        if author_id in IGNORE_USERS:
            continue

        author_commits[author_id] = author_commits.get(author_id, 0) + 1
        author_additions[author_id] = author_additions.get(author_id, 0) + c.stats.additions
        author_deletions[author_id] = author_deletions.get(author_id, 0) + c.stats.deletions

    return no_commits, author_commits, author_additions, author_deletions

def get_stats_contrib_repo_all(g: Github, repo_name):
    '''
    Extracts commit stats for a whole repo (not commit per commit)
    This will ignore commits done by non registered authors

    :param g: handle to GitHub
    :param repo_name: name of the repository (owner + name)
    :return: stats: no of total commits and dicts per author: no of commits, no of additions, no of deletions
    '''
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


if __name__ == '__main__':
    parser = ArgumentParser(
        description="Extract no of commits per author in a collection of repositories given as a CSV file"
                    "CSV HEADERS: ORG_NAME, ASSIGNMENT, REPO_ID, REPO_NAME, REPO_GIT")
    parser.add_argument('REPO_CSV', help="List of repositories to get data from.")
    parser.add_argument('CSV_OUT', help="File to output the stats of authors.")
    parser.add_argument('--teams', 
        nargs='+',
        help='if given, only the teams specified will be parsed.')
    parser.add_argument('--tag', help='if given, check up to a given tag.')
    parser.add_argument('-u', '--user', help="GitHub username.")
    parser.add_argument('-t', '--token-file', help="File containing GitHub authorization token/password.")
    parser.add_argument('-p', '--password', help="GitHub username's password.")
    args = parser.parse_args()

    # Get the list of TEAM + GIT REPO links from csv file
    list_repos = util.get_repos_from_csv(args.REPO_CSV, args.teams)

    if len(list_repos) == 0:
        logging.warning(f'No repos found in the mapping file "{args.REPO_CSV}". Stopping.')
        exit(0)

    # Authenticate to GitHub
    if not args.token_file and not (args.user or args.password):
        logging.error('No authentication provided, quitting....')
        exit(1)
    try:
        g = util.open_gitHub(user=args.user, token_file=args.token_file, password=args.password)
    except:
        logging.error("Something wrong happened during GitHub authentication. Check credentials.")
        exit(1)

    # Process each repo in list_repos
    authors_stats = []
    for r in list_repos:
        repo_id = r["REPO_ID"]
        repo_url = f"https://github.com/{repo_id}"
        logging.info(f'Processing repo {repo_id} ({repo_url})...')
        try:
            no_commits, author_commits, author_add, author_del = get_stats_contrib_repo(g, r["REPO_NAME"], sha=args.tag)
        except Exception as e:
            logging.info(f'\t Exception repo {repo_id}: {e}')
            continue
        logging.info(f'\t Repo {repo_id} has {no_commits} commits by {len(author_commits)} authors.')
        authors_stats.append((repo_id, author_commits, author_add, author_del))


    # Produce/Update CSV file output with all repos if requested via option --csv
    # first check if we are updating a file
    rows_to_csv = []
    if os.path.exists(args.CSV_OUT):
        logging.info(f'Updating teams in existing CSV file *{args.CSV_OUT}*.')
        with open(args.CSV_OUT, 'r') as f:
            csv_reader = csv.DictReader(f, fieldnames=CSV_HEADER)

            next(csv_reader)  # skip header
            for row in csv_reader:
                if args.teams is not None and row['REPO_ID'] not in args.teams:
                    rows_to_csv.append(row)
    else:
        logging.info(f'List of author stats will be saved to CSV file *{args.CSV_OUT}*.')

    # next build the rows for the repo inspected for update
    for x in authors_stats: # x = (repo_name, dict_authors_commits)
            for author in x[1]:
                row = {}
                row['REPO_ID'] = x[0]
                row['AUTHOR'] = author
                row['COMMITS'] = x[1][author]
                row['ADDITIONS'] = x[2][author]
                row['DELETIONS'] = x[3][author]
                rows_to_csv.append(row)
    
    # sort by repo id first, then author
    rows_to_csv.sort(key = lambda x: (x['REPO_ID'], x['AUTHOR']))

    # finally, write to csv the whole pack of rows (old and updated)
    with open(args.CSV_OUT, 'w') as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=CSV_HEADER)
        csv_writer.writeheader()
        csv_writer.writerows(rows_to_csv)

