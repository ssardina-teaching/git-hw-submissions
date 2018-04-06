#!/usr/bin/env python

import os
import argparse
import csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This script will clone a list of github repos.'
    )
    parser.add_argument(
        '--repos-csv',
        help='file where the gihub repo names are listed'
    )
    args = parser.parse_args()

    if args.repos_csv is None:
        print('ERROR: Sorry, you have to specify an input csv file')
        exit(1)

    print("This script will clone a list of GitHub repos form file: %s" % args.repos_csv)

    github_repos = []
    repo_file = open(args.repos_csv, 'r')
    repo_reader = csv.reader(repo_file, delimiter=',')
    for row in repo_reader:
        repo_name = row[0]
        github_url = repo_name.split('/')[0], 'git@github.com:' + repo_name.rstrip()
        github_repos.append(github_url)

    # Now we clone all the repos in github_repos list
    for repo in github_repos:
        print("\nCloning repo: " + repo[0])
        if os.path.isdir(repo[0]):
            print("\t Repo already cloned, skipping....")
        else:
            cmd = "git clone %s %s" % (repo[1], repo[0])
            print("Cloneing: %s" %cmd)
            os.system(cmd)
