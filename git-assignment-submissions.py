#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a csv file containing repo URL GIT  for each team and a tag and will clone/update them in an
output directory.

It also produces a file submission_timestamp.csv with all timestamp of the tag for the successful repo cloned/updated.
"""
import shutil
import os
import argparse
import csv
import logging
# import iso8601
# from pytz import timezone
import traceback
import time

# https://gitpython.readthedocs.io/en/2.1.9/reference.html
# http://gitpython.readthedocs.io/en/stable/tutorial.html
import git
# from git import Repo, Git

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%a, %d %b %Y %H:%M:%S')

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)

# Extract the timestamp for a given tag in a repo
def get_tag_time(repo, tag_str):
    tag_commit = next((tag.commit for tag in repo.tags if tag.name == tag_str), None)

    if tag_commit is None:
        return None
    else:
        tag_date = time.localtime(tag_commit.committed_date)
        return time.strftime(DATE_FORMAT, tag_date), tag_commit


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


    # Get the list of teams with their GIT URL from csv file
    teams_file = open(team_csv_file, 'r')
    teams_reader = csv.DictReader(teams_file, delimiter=',')
    list_teams = list(teams_reader)

    # Setup file to save the submission timestamps for each successful student
    submission_timestamps_file = open('submissions_timestamps.csv', 'w')
    submission_writer = csv.DictWriter(submission_timestamps_file, fieldnames=['team', 'submitted_at', 'commit'])
    submission_writer.writeheader()


    logging.info('Found {} team repositories.'.format(len(list_teams)))
    successful_clones = 1
    team_good = []
    team_bad = []
    for c, row in enumerate(list_teams, 1):
        print('\n')
        logging.info('Processing {} team {} in git url {}'.format(c, row['TEAM'], row['GIT-URL']))

        team_name = row['TEAM']
        git_url = row['GIT-URL']
        git_local_dir = os.path.join(output_folder, team_name)

        if not os.path.exists(git_local_dir):
            print('\t Cloning repo for team {} from remote.'.format(team_name))
            try:
                repo = git.Repo.clone_from(git_url, git_local_dir, branch=submission_tag)
            except git.GitCommandError as e:
                team_bad.append(team_name)
                logging.warning('Repo for team {} with tag {} cannot be cloned: {}'.
                                format(team_name, submission_tag, e.stderr))
                continue
            submission_time, submission_commit = get_tag_time(repo, submission_tag)
        else:
            print('\t Repository for team {} already exists.'.format(team_name))
            try:
                repo = git.Repo(git_local_dir)
                submission_time, _ = get_tag_time(repo, submission_tag)
                if submission_time is None:
                    print('\t No tag {} in the repository, strange as it was already there...'.format(submission_tag))
                else:
                    print('\t Current submission tag for {} dated {}; updating it...'.format(team_name, submission_time))

                # Next, we update the repo to get updated submission tag
                repo.remote('origin').fetch(tags=True)
                submission_time, submission_commit = get_tag_time(repo, submission_tag)
                if submission_time is None:
                    team_bad.append(team_name)
                    print('\t No tag {} in the repository for team {} anymore; removing it...'.format(submission_tag,
                                                                                                      team_name))
                    shutil.rmtree(git_local_dir)
                    continue
                repo.git.checkout(submission_tag)
            except git.GitCommandError as e:
                    team_bad.append(team_name)
                    logging.warning('\t Problem with existing repo for team {}; removing it: {}'.format(team_name, e.stderr))
                    print('\n')
                    shutil.rmtree(git_local_dir)
                    continue
            except:
                    team_bad.append(team_name)
                    logging.warning('\t Local repo {} is problematic; removing it...'.format(git_local_dir))
                    print(traceback.print_exc())
                    print('\n')
                    shutil.rmtree(git_local_dir)
                    continue

        # We now we have a repo with the submission tag  updated in the local filesystem
        print('\t Repo for team {} extracted successfully with tag date {}'.format(team_name, submission_time))
        submission_writer.writerow({'team' : team_name, 'submitted_at': submission_time, 'commit': submission_commit})
        successful_clones = successful_clones + 1
        team_good.append(team_name)
        # local copy already exists - needs to update it maybe tag is newer

    print("\n ================================ \n")
    logging.info("Finished clonning repositories: {} successful out of {}".format(successful_clones, len(list_teams)))
    print("\n ================================ \n")
    print('Teams clonned successfully:')
    for t in team_good:
        print(t)

    print('\n Teams NOT clonned successfully:')
    for t in team_bad:
        print(t)
