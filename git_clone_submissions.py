#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a csv file containing repo URL GIT  for each team and a tag and will clone/update them in an
output directory.

It also produces a file submission_timestamp.csv with all timestamp of the tag for the successful repo cloned/updated.

This script uses GitPython module to have Git API: https://gitpython.readthedocs.io/en/stable/tutorial.html
"""
import shutil
import os
import sys
import argparse
import csv
import logging
import traceback
import time

# https://gitpython.readthedocs.io/en/2.1.9/reference.html
# http://gitpython.readthedocs.io/en/stable/tutorial.html
import git

# from git import Repo, Git

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO,
                    datefmt='%a, %d %b %Y %H:%M:%S')

DATE_FORMAT = '%-d/%-m/%Y %-H:%-M:%-S'  # RMIT Uni (Australia)


# Extract the timestamp for a given tag in a repo
def get_tag_info(repo:git.Repo, tag_str):
    """
    Returns the information of a tag in a repo

    :param repo: the repository to search for a tag
    :param tag_str: the tag in the repo
    :return: the tag's commit time, the tag's commit, the time it was tagged
    """
    if tag_str == 'master':
        tag_commit = repo.commit()
    else:
        tag = next((tag for tag in repo.tags if tag.name == tag_str), None)
        # tag_commit = next((tag.commit for tag in repo.tags if tag.name == tag_str), None)
        if tag is None:
            logging.error("\t Repo {} does not have tag {}".format(repo, tag_str))
            return None
        tag_commit = tag.commit

    tag_commit_date = time.localtime(tag_commit.committed_date)
    try:
        tagged_date = time.localtime(tag.object.tagged_date)  # if it is an annotated tag
    except:
        tagged_date = tag_commit_date  # if it is a lightweight tag
    return time.strftime(DATE_FORMAT, tag_commit_date), tag_commit, time.strftime(DATE_FORMAT, tagged_date)


# return timestamps form a csv submission file
def load_timestamps(timestamp_filename):
    """
    Builds a dictionary from a CSV file of timestamps for each team

    :param timestamp_filename: a CSV file containing three columns: team, submitted_at, commit
    :return: a dictionary with key the team name, and value the timestamp of submission as per CSV file
    """
    team_timestamps = {}

    with open(timestamp_filename, 'r') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"', fieldnames=['team', 'submitted_at', 'commit'])

        next(reader)  # skip header
        for row in reader:
            team_timestamps[row['team']] = row['submitted_at']
    return team_timestamps


def get_teams_from_csv(csv_file, team=None):
    """
    Collect list of teams with their git URL links from a csv file

    :param csv_file: file where csv data is with two fields TEAM and GIT
    :param team: the specific name of one team or None
    :return: a list of teams
    """
    teams_file = open(csv_file, 'r')
    # Get the list of teams with their GIT URL from csv file
    teams_reader = csv.DictReader(teams_file, delimiter=',')
    teams = list(teams_reader)

    # If there was a specific team given, just keep that one in the list to clone just that
    if team is not None:
        teams = [t for t in teams if t['TEAM'] == team]

    return teams


def clone_team_repos(list_teams, tag_str, output_folder):
    """
    Clones a the repositories from a list of teams at the tag commit into a given folder

    :param list_teams: a dictionary mapping team names to git-urls
    :param tag_str: the tag to grab
    :return: the following information as a tuple:
         teams_cloned : teams that were successfully cloned
         team_new: teams that are new
         team_updated: teams that were there and got a new version in the tag
         team_unchanged: teams that were there but with the same tag version
         team_missing: teams that where not clonned
    """
    no_teams = len(list_teams)
    list_teams.sort(key=lambda tup: tup['TEAM'].lower())  # sort the list of teams
    logging.info('About to clone {} repo teams into folder {}/.'.format(no_teams, output_folder))
    team_new = []
    team_missing = []
    team_unchanged = []
    team_updated = []
    teams_cloned = []
    for c, row in enumerate(list_teams, 1):
        print('\n')
        logging.info('Processing {}/{} team **{}** in git url {}.'.format(c, no_teams, row['TEAM'], row['GIT-URL']))

        team_name = row['TEAM']
        git_url = row['GIT-URL']
        git_local_dir = os.path.join(output_folder, team_name)

        if not os.path.exists(git_local_dir):  # if there is NOT already a local repo for the team
            logging.info('Trying to clone NEW team repo from URL {}.'.format(git_url))
            try:
                repo = git.Repo.clone_from(git_url, git_local_dir, branch=tag_str)
            except git.GitCommandError as e:
                team_missing.append(team_name)
                logging.warning('Repo for team {} with tag {} cannot be cloned: {}'.
                                format(team_name, tag_str, e.stderr))
                continue
            except KeyboardInterrupt:
                logging.warning('Script terminated via Keyboard Interrupt; finishing...')
                sys.exit("keyboard interrupted!")
            submission_time, submission_commit, tagged_time = get_tag_info(repo, tag_str)
            logging.info('Team {} cloned successfully with tag date {}.'.format(team_name, submission_time))
            team_new.append(team_name)
        else:  # OK, so there is already a directory for this team in local repo, check if there is an update
            try:
                # First get the timestamp of the local repository for the team
                repo = git.Repo(git_local_dir)
                submission_time_local, _, _ = get_tag_info(repo, tag_str)
                logging.info('Existing LOCAL submission for {} dated {}; updating it...'.format(team_name,
                                                                                                submission_time_local))

                # Next, update the repo to check if there is a new updated submission time for submission tag
                repo.remote('origin').fetch(tags=True)
                submission_time, submission_commit, tagged_time = get_tag_info(repo, tag_str)
                if submission_time is None:  # tag has been deleted! remove local repo, no more submission
                    team_missing.append(team_name)
                    logging.info('No tag {} in the repository for team {} anymore; removing it...'.format(tag_str,
                                                                                                          team_name))
                    shutil.rmtree(git_local_dir)
                    continue

                # Checkout the repo from server (doesn't matter if there is no update, will stay as is)
                repo.git.checkout(tag_str)

                # Now processs timestamp to report new or unchanged repo
                if submission_time == submission_time_local:
                    logging.info('Team {} submission has not changed.'.format(team_name))
                    team_unchanged.append(team_name)
                else:
                    logging.info('Team {} updated successfully with new tag date {}'.format(team_name, submission_time))
                    team_updated.append(team_name)
            except git.GitCommandError as e:
                team_missing.append(team_name)
                logging.warning('Problem with existing repo for team {}; removing it: {}'.format(team_name, e.stderr))
                print('\n')
                shutil.rmtree(git_local_dir)
                continue
            except KeyboardInterrupt:
                logging.warning('Script terminated via Keyboard Interrupt; finishing...')
                sys.exit(1)
            except: # catch-all
                team_missing.append(team_name)
                logging.warning('\t Local repo {} is problematic; removing it...'.format(git_local_dir))
                print(traceback.print_exc())
                print('\n')
                shutil.rmtree(git_local_dir)
                continue
        # Finally, write team into submission timestamp file
        teams_cloned.append(
            {'team': team_name,
             'submitted_at': submission_time,
             'commit': submission_commit,
             'tag': tag_str,
             'tagged_at': tagged_time})

    return teams_cloned, team_new, team_updated, team_unchanged, team_missing


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Clone a list of GIT repositories containing assignment submissions via a tag.'
    )
    parser.add_argument(
        dest='team_csv_file', type=str,
        help='csv file containing the URL git repo for each team (must contain two named columns: TEAM and GIT-URL).'
    )
    parser.add_argument(
        dest='tag_str', type=str,
        help='commit tag to clone (use "master" for latest commit at master).'
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
    # we could also use vars(parser.parse_args()) to make args a dictionary args['<option>']
    args = parser.parse_args()

    # collect all the options given in CLI
    team_csv_file = args.team_csv_file  # csv file with team git repo links
    submission_tag = args.tag_str  # tag to grab when cloning, if any
    output_folder = args.output_folder  # folder where to clone repos
    submission_timestamps_file = args.file_timestamps  # filename to store timestamps
    add_timestamps = args.add_timestamps  # True if we just append to the timestamp file
    team_to_clone = args.team  # the specific team to mark

    # Get the list of TEAM + GIT REPO links from csv file
    list_teams = get_teams_from_csv(team_csv_file, team_to_clone)

    # If a submission csv file exists, make a backup of it as it will be overwritten
    if os.path.exists(submission_timestamps_file):
        shutil.copy(submission_timestamps_file, submission_timestamps_file + '.bak')

    # Perform the ACTUAL CLONING of all teams in list_teams
    teams_cloned, team_new, team_updated, team_unchanged, team_missing = clone_team_repos(list_teams, submission_tag,
                                                                                          output_folder)

    # Write the submission timestamp file
    if add_timestamps:  # we just append to the file
        f = open(submission_timestamps_file, 'a')
        submission_writer = csv.DictWriter(f, fieldnames=['team', 'submitted_at', 'commit', 'tag', 'tagged_at'])
    else:
        f = open(submission_timestamps_file, 'w')
        submission_writer = csv.DictWriter(f, fieldnames=['team', 'submitted_at', 'commit', 'tag', 'tagged_at'])
        submission_writer.writeheader()
    for r in teams_cloned:
        submission_writer.writerow(r)

    # produce report of what was cloned
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
    print('TEAMS MISSING (or not cloned successfully): ({})'.format(len(team_missing)))
    for t in team_missing:
        print("\t {}".format(t))
    print("\n ============================================== \n")
