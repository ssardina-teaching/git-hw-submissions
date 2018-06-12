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
    tag = next((tag for tag in repo.tags if tag.name == tag_str), None)

    # tag_commit = next((tag.commit for tag in repo.tags if tag.name == tag_str), None)
    if tag is None:
        return None
    else:
        tag_commit = tag.commit
        tag_commit_date = time.localtime(tag_commit.committed_date)
        try:
            tagged_date = time.localtime(tag.object.tagged_date)    # if it is an annotated tag
        except:
            tagged_date = tag_commit_date   # if it is a lightweight tag
        return time.strftime(DATE_FORMAT, tag_commit_date), tag_commit, time.strftime(DATE_FORMAT, tagged_date)

# return timestamps form a csv submission file
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
        help='csv file containing the URL git repo for each team (must contain two named columns: TEAM and GIT-URL).'
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
        help='filename to store the timestamps of submissions (default: %(default)s).',
        default='submissions_timestamps.csv',
    )
    parser.add_argument(
        '--add-timestamps',
        help='append to the timestamps file.',
        action='store_true'
    )
    args = parser.parse_args()

    team_csv_file = args.team_csv_file
    submission_tag = args.tag_str
    output_folder = args.output_folder
    timestamps_file = args.file_timestamps
    add_timestamps = args.add_timestamps


    teams_file = open(team_csv_file, 'r')
    # Get the list of teams with their GIT URL from csv file
    teams_reader = csv.DictReader(teams_file, delimiter=',')
    list_teams = list(teams_reader)

    # If there was a specific team given, just keep that one in the list to clone just that
    if not args.team is None:
        list_teams = [team for team in list_teams if team['TEAM'] == args.team]


    # If a submission csv file exists, make a backup of it as it will be overwritten
    if os.path.exists(timestamps_file):
        shutil.copy(timestamps_file, timestamps_file + '.bak')

    # Open the submission file for writing
    if add_timestamps:
        submission_timestamps_file = open(timestamps_file, 'a')
        submission_writer = csv.DictWriter(submission_timestamps_file,
                                           fieldnames=['team', 'submitted_at', 'commit', 'tagged_at'])
    else:
        submission_timestamps_file = open(timestamps_file, 'w')
        submission_writer = csv.DictWriter(submission_timestamps_file,
                                           fieldnames=['team', 'submitted_at', 'commit', 'tagged_at'])
        submission_writer.writeheader()


    no_teams = len(list_teams)
    list_teams.sort(key=lambda tup: tup['TEAM'].lower())    # sort the list of teams
    logging.info('Database contains {} teams to clone in folder {}/.'.format(no_teams, output_folder))
    team_new = []
    team_missing = []
    team_unchanged = []
    team_updated = []
    for c, row in enumerate(list_teams, 1):
        print('\n')
        logging.info('Processing {}/{} team **{}** in git url {}.'.format(c, no_teams, row['TEAM'], row['GIT-URL']))

        team_name = row['TEAM']
        git_url = row['GIT-URL']
        git_local_dir = os.path.join(output_folder, team_name)


        if not os.path.exists(git_local_dir):   # if there is already a local repo for the team
            print('\t Trying to clone NEW team repo from URL {}.'.format(git_url))
            try:
                repo = git.Repo.clone_from(git_url, git_local_dir, branch=submission_tag)
            except git.GitCommandError as e:
                team_missing.append(team_name)
                logging.warning('Repo for team {} with tag {} cannot be cloned: {}'.
                                format(team_name, submission_tag, e.stderr))
                continue
            submission_time, submission_commit, tagged_time = get_tag_time(repo, submission_tag)
            print('\t\t Team {} cloned successfully with tag date {}.'.format(team_name, submission_time))
            team_new.append(team_name)
        else:   # OK, so there is already a directory for this team in local repo, check if there is an update
            try:
                # First get the timestamp of the local repository for the team
                repo = git.Repo(git_local_dir)
                submission_time_local, _, _ = get_tag_time(repo, submission_tag)
                if submission_time_local is None:
                    print('\t No tag {} in the repository, strange as it was already there...'.format(submission_tag))
                else:
                    print('\t Existing LOCAL submission for {} dated {}; updating it...'.format(team_name, submission_time_local))


                # Next, update the repo to check if there is a new updated submission time for submission tag
                repo.remote('origin').fetch(tags=True)
                submission_time, submission_commit, tagged_time = get_tag_time(repo, submission_tag)
                if submission_time is None: # submission_tag has been deleted! remove local repo, no more submission
                    team_missing.append(team_name)
                    print('\t No tag {} in the repository for team {} anymore; removing it...'.format(submission_tag,
                                                                                                      team_name))
                    shutil.rmtree(git_local_dir)
                    continue

                # Checkout the repo from server (doesn't matter if there is no update, will stay as is)
                repo.git.checkout(submission_tag)

                # Now processs timestamp to report new or unchanged repo
                if submission_time == submission_time_local:
                    print('\t\t Team {} submission has not changed.'.format(team_name))
                    team_unchanged.append(team_name)
                else:
                    print('\t Team {} updated successfully with new tag date {}'.format(team_name, submission_time))
                    team_updated.append(team_name)
            except git.GitCommandError as e:
                    team_missing.append(team_name)
                    logging.warning('\t Problem with existing repo for team {}; removing it: {}'.format(team_name, e.stderr))
                    print('\n')
                    shutil.rmtree(git_local_dir)
                    continue
            except:
                    team_missing.append(team_name)
                    logging.warning('\t Local repo {} is problematic; removing it...'.format(git_local_dir))
                    print(traceback.print_exc())
                    print('\n')
                    shutil.rmtree(git_local_dir)
                    continue
        # Finally, write team into submission timestamp file
        submission_writer.writerow(
            {'team': team_name, 'submitted_at': submission_time, 'commit': submission_commit, 'tagged_at': tagged_time})

                    # local copy already exists - needs to update it maybe tag is newer

    print("\n ============================================== \n")
    print('NEW TEAMS: {}'.format(len(team_new)))
    for t in team_new:
        print("\t {}".format(t))
    print('UPDATED TEAMS: {}'.format(len(team_updated)))
    for t in team_updated:
        print("\t {}".format(t))
    print('UNCHANGED TEAMS: {}'.format(len(team_unchanged)))
    for t in team_unchanged:
        print("\t {}".format(t))
    print('TEAMS MISSING (or not clonned successfully): ({})'.format(len(team_missing)))
    for t in team_missing:
        print("\t {}".format(t))
    print("\n ============================================== \n")
