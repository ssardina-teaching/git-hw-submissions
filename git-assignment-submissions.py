#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a csv file containing repo URL GIT  for each team and will clone them in an output directory.

"""

import os
import argparse
import csv
import logging
import git
import iso8601
from pytz import timezone
import time
# from git import Repo, Git # http://gitpython.readthedocs.io/en/stable/tutorial.html

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This script will clone a list of GIT repositories contatining assignment submissions.'
    )
    parser.add_argument(
        '--output',
        help='directory where to clone all repositories'
    )
    parser.add_argument(
        '--repos-file',
        help='list of URL repositories with their team names'
    )
    args = parser.parse_args()

    if args.repos_file is None or args.output is None:
        logging.error('Missing output or repos arguments; check both information are given.')
        exit(1)


    git_repos = []
    repo_file = open(args.repos_file, 'r')
    repo_reader = csv.DictReader(repo_file, delimiter=',')

    logging.info("Start cloning. Found %d team repositories.\n" % len(list(repo_reader)))
    for row in repo_reader:
        print(row['TEAM'], row['URL'])
    print("\n")

    git_url = 'git@bitbucket.org:ssardina-teaching/script-tools.git'
    git_local_dir = os.path.join(args.output, git_url.split('/')[1])
    tag = 'init'
    if not os.path.exists(git_local_dir):
        # https://gitpython.readthedocs.io/en/2.1.9/reference.html
        git.Repo.clone_from(git_url, git_local_dir, branch=tag)

    else:
        logging.warning('Repository %s already exists, ignoring...' % git_url)
        repo = git.Repo(git_local_dir)
        print(repo.tags)
        tag_commit = repo.tags[0].commit
        tag_date = time.localtime(tag_commit.committed_date)
        print(time.strftime(DATE_FORMAT, tag_date))

        

        # print(iso8601.parse_date(tag_date).astimezone(timezone(TIMEZONE)))

    # Now we clone all the repos in github_repos list
    # for repo in git_repos:
    #     print("\nCloning repo: " + repo[0])
    #     if os.path.isdir(repo[0]):
    #         print("\t Repo already cloned, skipping....")
    #     else:
    #         cmd = "git clone %s %s" % (repo[1], repo[0])
    #         print("Cloneing: %s" %cmd)
    #         os.system(cmd)
