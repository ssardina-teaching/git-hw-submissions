#!/user/bin/env python
"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub:

    python3 -m pip install PyGithub

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python

    Sebastian Sardina 2020 - ssardina@gmail.com

"""
#
# Script obtained from: https://gist.github.com/robwhess/48547bf369ccf422cca78e5753b5a1c7
# This is a simple python script to clone all of the repositories for an
# assignment managed via GitHub Classroom.  It has a dependency on the
# requests module, so to use it, you must:
#
#   pip install requests
#
# You can run the script with the '-h' option to get info on its usage.
#
import base64
import csv
import re
import traceback

from argparse import ArgumentParser
from github import Github, Repository, Organization, GithubException
import logging
import util

CSV_GITHUB_USERNAME="github_username"
CSV_GITHUB_IDENTIFIER= "identifier"

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO,
                    datefmt='%a, %d %b %Y %H:%M:%S')

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)



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



if __name__ == '__main__':
    parser = ArgumentParser(
        description="Extract no of commits per author in a collection of repositories given as a CSV file"
                    "CSV HEADERS: ORG_NAME, ASSIGNMENT, REPO_ID, REPO_NAME, REPO_GIT")
    parser.add_argument('REPO_CSV', help="List of repositories to get data from.")
    parser.add_argument('CSV_OUT', help="File to output the stats of authors.")
    parser.add_argument('--repo', help='if given, only the team specified will be cloned/updated.')
    parser.add_argument('--tag', help='if given, check up to a given tag.')
    parser.add_argument('-u', '--user', help="GitHub username.")
    parser.add_argument('-t', '--token-file', help="File containing GitHub authorization token/password.")
    parser.add_argument('-p', '--password', help="GitHub username's password.")
    args = parser.parse_args()

    # Get the list of TEAM + GIT REPO links from csv file
    list_repos = util.get_repos_from_csv(args.REPO_CSV, args.repo)

    if len(list_repos) == 0:
        logging.warning(f'No repos found in the mapping file "{args.repos_csv_file}". Stopping.')
        exit(0)

    if not args.token_file and not (args.user or args.password):
        logging.error('No authentication provided, quitting....')
        exit(1)
    try:
        g = util.open_gitHub(user=args.user, token_file=args.token_file, password=args.password)
    except:
        logging.error("Something wrong happened during GitHub authentication. Check credentials.")
        exit(1)

    authors_stats = []
    for r in list_repos:
        repo = g.get_repo(r["REPO_NAME"])
        print(f'*** Processing repo {r["REPO_NAME"]}: ', end= '')
        try:
            repo_commits = repo.get_commits(sha=args.tag) if args.tag is not None else repo.get_commits()
            repo_no_commits = repo_commits.totalCount
        except:
            print('NONE - SKIP')
            continue
        print(repo_no_commits)

        repo_authors = {}
        for c in repo_commits:
            try:
                repo_authors[c.author.login] = repo_authors.get(c.author.login, 0) + 1
            except:
                repo_authors[f'name({c.commit.author.name})'] = repo_authors.get(f'name({c.commit.author.name})', 0) + 1

        authors_stats.append((r["REPO_ID"], repo_authors))

    # Produce CSV file output with all repos if requested via option --csv
    logging.info(f'List of author stats will be saved to CSV file *{args.CSV_OUT}*.')
    with open(args.CSV_OUT, 'w') as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=['REPO_ID', 'AUTHOR', 'NO_COMMITS'])
        csv_writer.writeheader()

        # for each repo in repo_select produce a row in the CSV file, add the team name from mapping
        for x in authors_stats: # x = (repo_name, dict_authors_commits)
            for author in x[1]:
                row = {}
                row['REPO_ID'] = x[0]
                row['AUTHOR'] = author
                row['NO_COMMITS'] = x[1][author]

                csv_writer.writerow(row)
