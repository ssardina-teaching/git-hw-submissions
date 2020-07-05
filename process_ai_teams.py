import argparse
import csv
import errno
import logging
import math
import os
import pathlib
import subprocess

from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

this_module = pathlib.os.path.abspath(__file__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def https_to_ssh_git_link(https_link):
    parts = urlparse(https_link)
    return 'git@{}:{}.git'.format(parts.netloc, parts.path[1:-1])


def clone_repo(repo_link, dest_folder, use_ssh=True):
    if use_ssh and repo_link.startswith('https'):
        repo_link = https_to_ssh_git_link(repo_link)

    exit_code = subprocess.call(['git', 'clone', repo_link, dest_folder])
    if exit_code is not 0:
        logger.error("Repo clone failed for '%s'. exit code: %d", repo_link, exit_code)

    return exit_code


def zip_repo(dest_filepath, src_folder):
    args = ['python', '-m', 'zipfile', '-c', dest_filepath, src_folder]
    exit_code = subprocess.call(args)
    if exit_code is not 0:
        logging.error(
            "Failed to save src_folder '%s' to '%s'. Exit code: %d",
            src_folder,
            dest_filepath,
            exit_code)

    return exit_code


def get_tag_timestamps(repo_folder):
    """
    Build a dictionary of git tags and the times those tags were created.
    eg. {
        'v1.0.0': datetime,
        'v1.0.1': datetime,
        ...
    }
    """
    args = ['git tag -l --format=\'%(refname)  %(taggerdate)\'']
    logger.info('Calling: %s', ' '.join(args))
    completed_proc = subprocess.run(
        args,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=repo_folder
    )
    output = completed_proc.stdout.decode('utf-8')
    lines = output.split('\n')
    timestamped_tags = {}

    for line in lines:
        if not line:
            continue
        tag_ref, time_string = line.split('  ')  # important that it's double space
        tag_time = datetime.strptime(time_string, '%a %b %d %H:%M:%S %Y %z')
        tag = tag_ref.split('/')[-1]
        timestamped_tags[tag] = tag_time
    return timestamped_tags


def check_number_of_days_overdue(tag_timestamps, target_tag, due_date):
    if target_tag not in tag_timestamps:
        raise KeyError('target tag is not found in repositories tags')

    target_time = tag_timestamps[target_tag]
    if target_time <= due_date:
        return 0

    delta_seconds = (target_time - due_date).total_seconds()

    SECONDS_IN_DAY = float(60 * 60 * 24)

    return math.floor(delta_seconds / SECONDS_IN_DAY) + 1


class Config():
    def __init__(self, output_folder, due_date, tag_str):
        self.output_folder = Path(output_folder)
        self.due_date = due_date
        self.tag_str = tag_str


class TeamMember():
    def __init__(self, name, student_number):
        self.name = name
        self.student_number = student_number
        self._validate()

    def _validate(self):
        STUDENT_NUMBER_LEN = 7
        if not self.name:
            logger.warn("Team member name cannot be empty")
        if not self.student_number or len(self.student_number) is not STUDENT_NUMBER_LEN:
            logger.warn("Student number ID '{}' is invalid".format(self.student_number))
        try:
            int(self.student_number)
        except ValueError:
            logger.warn("Student number ID '{}' must be a number".format(self.student_number))

    def __repr__(self):
        return '<TeamMember: {} {}>'.format(self.name, self.student_number)


class TeamRegistration():
    def __init__(self, timestamp, email_addr, name, num_members, members, repo_link):
        self.timestamp = timestamp
        self.email_address = email_addr
        self.name = name
        self.num_members = num_members
        self.members = members
        self.repo_link = repo_link
        self._validate()

    def _validate(self):
        assert self.name
        if not self.num_members == len(self.members):
            logger.warn("Number of provided team members does not match number specified")

    def process(self, config):
        # Create a folder in the output_folder with the team name
        dest_repo_folder = Path(config.output_folder) / Path(self.name)
        try:
            os.makedirs(str(dest_repo_folder))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Clone repo in team folder
        exit_code = clone_repo(self.repo_link, str(dest_repo_folder))
        if exit_code is not 0:
            logger.error("Failed to complete processing for team: %s", self.name)
            # TODO: should not just fail and return if repo already exists in file system
            return

        tag_timestamps = get_tag_timestamps(str(dest_repo_folder))

        if config.tag_str not in tag_timestamps:
            logger.error(
                "Submission from team '%s' does not have the target submission tag",
                self.name
            )
            return

        days_overdue = check_number_of_days_overdue(tag_timestamps, config.tag_str, config.due_date)
        if days_overdue > 0:
            logger.warn("Submission from team '%s' is %d days overdue", self.name, days_overdue)
        dest_zip = config.output_folder / Path(self.name + '.zip')
        exit_code = zip_repo(dest_zip, dest_repo_folder)

        if exit_code is not 0:
            logger.error("Failed to complete processing for team: %s", self.name)

        logger.error("Successfully processed team: %s", self.name)









def main():
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

    # Build configuration settings
    csv_file_path = args.team_csv_file
    tag_str = args.tag_str
    output_folder = args.output_folder
    config = Config(
        output_folder=output_folder,
        # TODO: make the date more flexible, not hard coded in the script. Maybe just add timestamp of tag somewhere
        #           (separate csv submission date file or in zip file in name?)
        due_date=datetime(2018, 4, 9, tzinfo=timezone(timedelta(hours=10))),
        tag_str=tag_str,
    )

    all_teams = []
    with open(csv_file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        # Each row is a team, with members and URL to git repo
        for row in reader:
            num_members = row['How many members?']
            try:
                num_members = int(num_members)
            except ValueError:
                logging.error(
                    'Invalid number of members value %s for %s',
                    num_members,
                    row['Name of the team ']
                )

            # Buld student members for the team
            members = []
            for i in range(num_members):
                name_key = 'Full name of member {}'.format(i+1)
                id_key = 'Student number of member {}'.format(i+1)
                if i is 2:
                    name_key += ' (if any)'
                    id_key += ' (if any)'
                m = TeamMember(
                    row[name_key],
                    row[id_key]
                )
                members.append(m)

            team = TeamRegistration(
                timestamp=row['Timestamp'],
                email_addr=row['Email Address'],
                name=row['Name of the team '],
                num_members=num_members,
                members=members,
                repo_link=row['Bitbucket repository link']
            )
            all_teams.append(team)

    for team in all_teams:
        team.process(config)


if __name__ == '__main__':
    main()
