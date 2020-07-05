#!/user/bin/env python
"""
Script to obtain all the repositories from a GitHub Classroom

Uses PyGihub (https://github.com/PyGithub/PyGithub) as API to GitHub

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
        description="Extract repos in a GitHub Classroom repositories for a given assignment into a CSV file")
    parser.add_argument('ORG_NAME', help="Organization name for GitHub Classroom")
    parser.add_argument('ASSIGNMENT_PREFIX', help="Prefix string for the assignment.")
    parser.add_argument('CSV', help="CSV file where to store the set of repo links.")
    parser.add_argument('-u', '--user', help="GitHub username.")
    parser.add_argument('-t', '--token-file', help="File containing GitHub authorization token/password.")
    parser.add_argument('-p', '--password', help="GitHub username's password.")
    args = parser.parse_args()

    REPO_URL_PATTERN = re.compile(r'^{}/{}-(.*)$'.format(args.ORG_NAME, args.ASSIGNMENT_PREFIX))

    if args.token_file:
        with open(args.token_file) as fh:
            token = fh.read().strip()
        g = Github(token)
    elif args.user and args.password:
        g = Github(args.user, args.password)
    else:
        logging.error('No authentication provided, quitting....')
        exit(1)

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
            repos_select.append({'USER': match.group(1), 'GITHUB-NAME': repo.full_name, 'GIT-URL': repo.ssh_url})

    # Produce CSV file with all repos if requested via option --csv
    logging.info('List of repos save to CSV file *{}*.'.format(args.CSV))
    f = open(args.CSV, 'w')
    csv_writer = csv.DictWriter(f, fieldnames=['ORG_NAME', 'ASSIGNMENT', 'USER', 'GITHUB-NAME', 'GIT-URL'])
    csv_writer.writeheader()
    for r in repos_select:
        r['ORG_NAME'] = args.ORG_NAME
        r['ASSIGNMENT'] = args.ASSIGNMENT_PREFIX
        csv_writer.writerow(r)
    f.close()
