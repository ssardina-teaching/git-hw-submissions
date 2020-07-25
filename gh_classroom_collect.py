#!/user/bin/env python
"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGithub (https://github.com/PyGithub/PyGithub) as API to GitHub

Some usage help on PyGithub:
    https://www.thepythoncode.com/article/using-github-api-in-python

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
import os
import re

from argparse import ArgumentParser
from github import Github, Repository, Organization
import logging

CSV_GITHUB_USERNAME="github_username"
CSV_TEAM_NAME="identifier"

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
        description="Extract repos in a GitHub Classroom repositories for a given assignment into a CSV file"
                    "CSV HEADERS: ORG_NAME, ASSIGNMENT, USERNAME, TEAM, REPO-NAME, GIT-URL")
    parser.add_argument('ORG_NAME', help="Organization name for GitHub Classroom")
    parser.add_argument('ASSIGNMENT_PREFIX', help="Prefix string for the assignment.")
    parser.add_argument('CSV', help="CSV file where to store the set of repo links.")
    parser.add_argument('-u', '--user', help="GitHub username.")
    parser.add_argument('-t', '--token-file', help="File containing GitHub authorization token/password.")
    parser.add_argument('-p', '--password', help="GitHub username's password.")
    parser.add_argument('-m', '--team-map',
                        help="CSV file with maps team name ({}) - GitHub user ({}).".format(CSV_TEAM_NAME,
                                                                                            CSV_GITHUB_USERNAME))
    args = parser.parse_args()

    REPO_URL_PATTERN = re.compile(r'^{}/{}-(.*)$'.format(args.ORG_NAME, args.ASSIGNMENT_PREFIX))

    try:
        if args.token_file:
            with open(args.token_file) as fh:
                token = fh.read().strip()
            g = Github(token)
        elif args.user and args.password:
            g = Github(args.user, args.password)
        else:
            logging.error('No authentication provided, quitting....')
            exit(1)
    except:
        logging.error("Something wrong happened during GitHub authentication. Check credentials.")
        exit(1)

    # Populate user to team name mapping dictionary if CSV map was provided
    user_to_team_map = dict()
    if args.team_map:
        with open(args.team_map, 'r') as file:
            csv_content = csv.DictReader(file)
            for row in csv_content:
                row = dict(row)
                user_to_team_map[row[CSV_GITHUB_USERNAME]] = row[CSV_TEAM_NAME]
    else:
        logging.info('No GitHub to Team name mapping provided. Using username as team names.')


    logging.info(
        'Dumping repos in organization *{}* for assignment *{}* into CSV file *{}*.'.format(args.ORG_NAME,
                                                                                            args.ASSIGNMENT_PREFIX,
                                                                                            args.CSV))


    # Get the repos of the organization and extract the ones matching the assignment prefix
    org = g.get_organization(args.ORG_NAME)
    org_repos = org.get_repos()
    repos_select = []
    for repo in org_repos:
        match = re.match(REPO_URL_PATTERN, repo.full_name)
        if match:
            # repo_url = 'git@github.com:{}'.format(repo.full_name)
            logging.info('Found repo {}'.format(repo.full_name))
            repos_select.append({'USERNAME': match.group(1), 'REPO-NAME': repo.full_name, 'GIT-URL': repo.ssh_url})

    # Produce CSV file output with all repos if requested via option --csv
    logging.info('List of repos will be saved to CSV file *{}*.'.format(args.CSV))
    with open(args.CSV, 'w') as output_csv_file:
        csv_writer = csv.DictWriter(output_csv_file,
                                    fieldnames=['ORG_NAME', 'ASSIGNMENT', 'USERNAME', 'TEAM', 'REPO-NAME', 'GIT-URL'])
        csv_writer.writeheader()

        # for each repo in repo_select produce a row in the CSV file, add the team name from mapping
        for row in repos_select:
            if row['USERNAME'] in user_to_team_map.keys():
                row['TEAM'] = user_to_team_map[row['USERNAME']]

            row['ORG_NAME'] = args.ORG_NAME
            row['ASSIGNMENT'] = args.ASSIGNMENT_PREFIX
            csv_writer.writerow(row)
