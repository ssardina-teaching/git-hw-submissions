#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a csv file containing repo URL GIT  for each team and will clone them in an output directory.

"""
import shutil
import os
import argparse
import csv
import logging
import iso8601
from pytz import timezone
import time

# https://gitpython.readthedocs.io/en/2.1.9/reference.html
# http://gitpython.readthedocs.io/en/stable/tutorial.html
import git
# from git import Repo, Git

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%a, %d %b %Y %H:%M:%S')

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Clone a list of GIT repositories contatining assignment submissions via a tag.'
    )

    parser.add_argument(
        dest='team_csv_file', type=str,
        help='csv file containing the git repo for each team.'
    )
    parser.add_argument(
        dest='tag_str', type=str,
        help = 'commit tag representing a submission.'
    )
    parser.add_argument(
        dest='output_folder', type=str,
        help='the folder where to clone all repositories.'
    )
    args = parser.parse_args()

    team_csv_file = args.team_csv_file
    submission_tag = args.tag_str
    output_folder = args.output_folder


    git_repos = []
    teams_file = open(team_csv_file, 'r')
    teams_reader = csv.DictReader(teams_file, delimiter=',')

    # for row in teams_reader:
    #     print(row['TEAM'], row['URL'])

    submission_timestamps_file = open('submissions_timestamps.csv', 'w')
    submission_writer = csv.DictWriter(submission_timestamps_file, fieldnames=['team', 'submitted_at'])
    submission_writer.writeheader()

    # logging.info("Start cloning. Found %d team repositories.\n" % len(list(teams_reader)))
    for row in teams_reader:
        print(row['TEAM'], row['GIT-URL'])

        team_name = row['TEAM']
        git_url = row['GIT-URL']
        git_local_dir = os.path.join(output_folder, team_name)

        if not os.path.exists(git_local_dir):
            try:
                git.Repo.clone_from(git_url, git_local_dir, branch=submission_tag)

                repo = git.Repo(git_local_dir)
                tag_commit = repo.tags[0].commit
                tag_date = time.localtime(tag_commit.committed_date)
                submission_time = time.strftime(DATE_FORMAT, tag_date)
                submission_writer.writerow({'team' : team_name, 'submitted_at': submission_time})
            except Exception as e:
                print(e)



        else:
            repo = git.Repo(git_local_dir)
            print(repo.tags)
            tag_commit = repo.tags[0].commit
            tag_date = time.localtime(tag_commit.committed_date)
            submission_time = time.strftime(DATE_FORMAT, tag_date)


            logging.warning('Repository for team {} already exists with tag dated {}; updating it...'.format(team_name, submission_time))
            # local copy already exists - needs to update it maybe tag is newer

            repo.remote('origin').fetch(tags=True)
            try:
                repo.git.checkout(submission_tag)
            except git.GitCommandError as e:
                print(e.stderr)
                shutil.rmtree(git_local_dir)
                logging.info('Removing repository for team {}'.format(team_name))

        exit(0)
    print("\n")

    exit(0)


    # Now we clone all the repos in github_repos list
    # for repo in git_repos:
    #     print("\nCloning repo: " + repo[0])
    #     if os.path.isdir(repo[0]):
    #         print("\t Repo already cloned, skipping....")
    #     else:
    #         cmd = "git clone %s %s" % (repo[1], repo[0])
    #         print("Cloneing: %s" %cmd)
    #         os.system(cmd)
