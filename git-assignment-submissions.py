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


def load_timestamps(timestamp_filename):
    team_timestamps = {}

    with open(timestamp_filename, 'r') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"', fieldnames=['team', 'submitted_at', 'commit'])

        next(reader)    # skip header
        for row in reader:
            team_timestamps[row['team']] = row['submitted_at']
    return team_timestamps


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
    parser.add_argument(
        '--team',
        help='to mark a specific team only.'
    )
    parser.add_argument(
        '--file-timestamps',
        help='filename to store the timestamps of submissions (default: %(default)s)..',
        default='submissions_timestamps.csv',
    )
    args = parser.parse_args()

    team_csv_file = args.team_csv_file
    submission_tag = args.tag_str
    output_folder = args.output_folder
    timestamps_file = args.file_timestamps

    teams_file = open(team_csv_file, 'r')
    # Get the list of teams with their GIT URL from csv file
    teams_reader = csv.DictReader(teams_file, delimiter=',')
    list_teams = list(teams_reader)

    # If there was a specific team given, just keep that one in the list to clone just that
    if not args.team is None:
        list_teams = [team for team in list_teams if team['TEAM'] == args.team]


    # Build submission timestamp data (if submission file given exists)
    if os.path.exists(timestamps_file):
        existing_timestamps = load_timestamps(timestamps_file)
        logging.info('Timestamp file exists; will update it ({} teams in last submission)...'.format(len(existing_timestamps)))
        shutil.copy(timestamps_file, timestamps_file + '.bak')
    else:
        existing_timestamps = []


    # Open the submission file for writing
    submission_timestamps_file = open(timestamps_file, 'w')
    submission_writer = csv.DictWriter(submission_timestamps_file, fieldnames=['team', 'submitted_at', 'commit'])
    submission_writer.writeheader()


    logging.info('Database contains {} teams to clone in folder {}/.'.format(len(list_teams), output_folder))
    team_new = []
    team_bad = []
    team_exist = []
    for c, row in enumerate(list_teams, 1):
        print('\n')
        logging.info('Processing {} team **{}** in git url {}'.format(c, row['TEAM'], row['GIT-URL']))

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
                submission_time_local, _ = get_tag_time(repo, submission_tag)
                if submission_time_local is None:
                    print('\t No tag {} in the repository, strange as it was already there...'.format(submission_tag))
                else:
                    print('\t Current LOCAL submission tag for {} dated {}; updating it...'.format(team_name, submission_time_local))


                # Next, we update the repo to get updated submission tag
                repo.remote('origin').fetch(tags=True)
                submission_time, submission_commit = get_tag_time(repo, submission_tag)
                if submission_time is None:
                    team_bad.append(team_name)
                    print('\t No tag {} in the repository for team {} anymore; removing it...'.format(submission_tag,
                                                                                                      team_name))
                    shutil.rmtree(git_local_dir)
                    continue
                print('\t Existing submission: {} - New Submission: {}'.format(existing_timestamps[team_name], submission_time))
                if submission_time == existing_timestamps[team_name]:
                    print('\t\t Team {} submission has not changed, no need to checkout...'.format(team_name))
                    team_exist.append(team_name)
                else:
                    repo.git.checkout(submission_tag)
                    # We now we have a repo with the submission tag  updated in the local filesystem
                    print('\t Repo for team {} extracted successfully with tag date {}'.format(team_name,
                                                                                                   submission_time))
                    team_new.append(team_name)

                submission_writer.writerow(
                    {'team': team_name, 'submitted_at': submission_time, 'commit': submission_commit})
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

        # local copy already exists - needs to update it maybe tag is newer

    print("\n ============================================== \n")
    print('New teams: {}'.format(len(team_new)))
    for t in team_new:
        print("\t %s" % t)
    print('Unchanged teams: {}'.format(len(team_exist)))
    for t in team_exist:
        print("\t %s" % t)


    print('\n')
    print('Teams NOT clonned successfully ({}):'.format(len(team_bad)))
    for t in team_bad:
        print(t)
