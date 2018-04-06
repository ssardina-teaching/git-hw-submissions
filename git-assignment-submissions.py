#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a csv file containing repo URL GIT  for each team and will clone them in an output directory.

"""

import os
import argparse
import csv
import logging


# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')


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

    logging.info("We will clone the following repositories: \n")
    for row in repo_reader:
        print(row['TEAM'], row['URL'])
    print("\n")


    # Now we clone all the repos in github_repos list
    # for repo in git_repos:
    #     print("\nCloning repo: " + repo[0])
    #     if os.path.isdir(repo[0]):
    #         print("\t Repo already cloned, skipping....")
    #     else:
    #         cmd = "git clone %s %s" % (repo[1], repo[0])
    #         print("Cloneing: %s" %cmd)
    #         os.system(cmd)
