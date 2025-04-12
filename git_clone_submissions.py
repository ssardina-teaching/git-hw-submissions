#!/usr/bin/env python
"""
A script to manage assignment submissions via git repositories.

Script takes a CSV file containing repo URL GIT  for each team and a tag and will clone/update them in an
output directory.

It also produces a file submission_timestamp.csv with all timestamp of the tag for the successful repo cloned/updated.

This script uses GitPython module to have Git API:
    https://gitpython.readthedocs.io/en/stable/tutorial.html

A lot of tips on using GitPython:
    http://www.legendu.net/misc/blog/hands-on-GitPython/

GitPython provides object model access to your git repository.

    python3 -m pip install gitpython pytz

One could also use pygit2 (https://www.pygit2.org/), which are bindings to the libgit2 shared library


Manual debug via gitpython:

    >>> import git
    >>> repo = git.Repo("submissions/deepyellow2")
    >>> repo.common_dir
    /mnt/ssardina-volume/cosc1125-1127-AI/AI21/p-contest/preliminary/submissions/deepyellow2/.git
    >>> repo.remote()
    <git.Remote "origin">
    >>> repo.remote().exists()
    True
    >>> repo.remote('origin').fetch(tags=True,force=True)
    [<git.remote.FetchInfo object at 0x7fd4469054f0>, <git.remote.FetchInfo object at 0x7fd446905ae0>, <git.remote.FetchInfo object at 0x7fd446905a40>, <git.remote.FetchInfo object at 0x7fd4469059a0>, <git.remote.FetchInfo object at 0x7fd446905900>, <git.remote.FetchInfo object at 0x7fd446905b80>, <git.remote.FetchInfo object at 0x7fd446905c70>, <git.remote.FetchInfo object at 0x7fd446905cc0>, <git.remote.FetchInfo object at 0x7fd446905d60>, <git.remote.FetchInfo object at 0x7fd446905e50>]
    >>> repo.commit()
    <git.Commit "d859a90ef90b3212750d0f70c894995c5311b893">
    >>> repo.commit().committed_date
    1648214671
    >>> repo.git.pull()
    'Already up to date.'
"""
__author__ = "Sebastian Sardina - ssardina - ssardina@gmail.com"
__copyright__ = "Copyright 2018-2025"

import shutil
import os
import sys
import argparse
import csv
import time
import traceback

# local utilities
import util
from util import (
    TIMEZONE,
    UTC,
    NOW,
    NOW_ISO,
    NOW_TXT,
    LOGGING_DATE,
    LOGGING_FMT,
    GH_URL_PREFIX,
)


# https://gitpython.readthedocs.io/en/stable/reference.html
# http://gitpython.readthedocs.io/en/stable/tutorial.html
import git

# from git import Repo, Git

import logging
import coloredlogs
LOGGING_LEVEL = logging.INFO
# LOGGING_LEVEL = logger.DEBUG
# logger.basicConfig(format=LOGGING_FMT, level=LOGGING_LEVEL, datefmt=LOGGING_DATE)
logger = logging.getLogger(__name__)
coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT, datefmt=LOGGING_DATE)


CSV_REPO_GIT = "REPO_URL"
CSV_REPO_ID = "REPO_ID"


# return timestamps form a csv submission file
def load_timestamps(timestamp_filename):
    """
    Builds a dictionary from a CSV file of timestamps for each team

    :param timestamp_filename: a CSV file containing three columns: team, submitted_at, commit
    :return: a dictionary with key the team name, and value the timestamp of submission as per CSV file
    """
    team_timestamps = {}

    with open(timestamp_filename, "r") as f:
        reader = csv.DictReader(
            f,
            delimiter=",",
            quotechar='"',
            fieldnames=["team", "submitted_at", "commit"],
        )

        next(reader)  # skip header
        for row in reader:
            team_timestamps[row["team"]] = row["submitted_at"]
    return team_timestamps


def clone_team_repos(repos:list, tag:str, output_folder:str):
    """
    Clones a the repositories from a list of teams at the tag commit into a given folder

    :param list_repos: a dictionary mapping team names to git-urls
    :param tag_str: the tag to grab
    :return: the following information as a tuple:
         teams_cloned : teams that were successfully cloned
         team_new: teams that are new
         team_updated: teams that were there and got a new version in the tag
         team_unchanged: teams that were there but with the same tag version
         team_missing: teams that where not cloned
    """
    no_repos = len(repos)
    repos.sort(key=lambda tup: tup[CSV_REPO_ID].lower())  # sort the list of teams

    logger.info(f"About to clone {no_repos} repo teams into folder {output_folder}/.")
    teams_new = []
    teams_missing = []
    teams_unchanged = []
    teams_updated = []
    teams_cloned = []
    teams_notag = []
    teams_noteam = []
    for c, row in enumerate(repos, start=1):
        http_repo_link = row[CSV_REPO_GIT].replace(
            "git@github.com:", "http://github.com/"
        )
        logger.info(
            f"Processing {c}/{no_repos} team **{row[CSV_REPO_ID]}** in git url {http_repo_link}."
        )

        team_name = row[CSV_REPO_ID]
        if not team_name:
            logger.info(
                f"Repository {row[CSV_REPO_ID]} does not have a team associated; skipping..."
            )
            teams_noteam.append(row["USERNAME"])
            continue

        git_url = row[CSV_REPO_GIT]
        git_local_dir = os.path.join(output_folder, team_name)

        time.sleep(2)
        if not os.path.exists(
            git_local_dir
        ):  # if there is NOT already a local repo for the team - clone from scratch!
            logger.info(f"Trying to clone NEW team repo from URL {git_url}.")
            try:
                repo = git.Repo.clone_from(git_url, git_local_dir, branch=tag)
                new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                    repo, tag_str="head"
                )
                logger.info(
                    f"Team {team_name} cloned successfully with tag date {new_commit_time}."
                )
                teams_new.append(team_name)
                status = "new"
            except git.GitCommandError as e:
                teams_missing.append(team_name)
                logger.warning(
                    f"Repo for team {team_name} with tag/branch {tag} cannot be cloned: {e.stderr}"
                )
                continue
            except KeyboardInterrupt:
                logger.warning(
                    "Script terminated via Keyboard Interrupt; finishing..."
                )
                sys.exit("keyboard interrupted!")
            except TypeError as e:
                logger.warning(
                    f"Repo for team {team_name} was cloned but has no tag {tag}, removing it...: {e}"
                )
                repo.close()
                shutil.rmtree(git_local_dir)
                teams_notag.append(team_name)
                continue
            except Exception as e:
                logger.error(
                    f"Repo for team {team_name} cloned but unknown error when getting tag {tag}; should not happen. Stopping... {e}"
                )
                repo.close()
                exit(1)
        else:  # OK, so there is already a directory for this team in local repo, check if there is an update
            try:
                # First get the timestamp of the local repository for the team
                repo = git.Repo(
                    git_local_dir
                )  # https://gitpython.readthedocs.io/en/stable/reference.html#module-git.repo.base

                # get date of local head commit (where the local repo is pointing to)
                local_commit_time, _, _ = util.get_tag_info(repo, tag_str="head")

                logger.info(
                    f"Existing LOCAL submission for {team_name} dated {local_commit_time} ({str(repo.commit())[:7]}); updating it..."
                )

                # Next, first fetch from remote all tags and new commits
                # As of Git 2.2, we need to force to allow overwriting existint tags!
                # https://gitpython.readthedocs.io/en/stable/reference.html#git.remote.Remote.fetch
                repo.remote("origin").fetch(tags=True, force=True)

                if tag in ["master", "main"]:
                    repo.git.checkout(tag, force=True)
                    repo.git.pull()
                    new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                        repo, tag_str="head"
                    )
                else:
                    new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                        repo, tag
                    )
                    if (
                        new_commit_time is None
                    ):  # tag has been deleted! remove local repo, no more submission
                        teams_missing.append(team_name)
                        logger.info(
                            f"No tag {tag} in the repository for team {team_name} anymore; removing it..."
                        )
                        repo.close()
                        shutil.rmtree(git_local_dir)
                        continue
                    # Checkout the submission tag (doesn't matter if there is no update, will stay as is)
                    repo.git.checkout(tag)

                logger.debug(
                    f"Tag *{tag}* seen in in commit {str(new_commit)[:7]} ({new_commit_time}) tagged on {new_tagged_time}"
                )

                # Now process timestamp to report new or unchanged repo
                if new_commit_time == local_commit_time:
                    logger.info(f"Team {team_name} submission has not changed.")
                    teams_unchanged.append(team_name)
                    status = "unchanged"
                else:
                    logger.info(
                        f"Team {team_name} updated successfully with new tag date {new_commit_time}"
                    )
                    teams_updated.append(team_name)
                    status = "updated"
            except git.GitCommandError as e:
                teams_missing.append(team_name)
                logger.warning(
                    f"Problem with existing repo for team {team_name}; removing it: {e} - {e.stderr}"
                )
                print("\n")
                repo.close()
                continue
            except KeyboardInterrupt:
                logger.warning(
                    "Script terminated via Keyboard Interrupt; finishing..."
                )
                repo.close()
                sys.exit(1)
            except:  # catch-all
                print(traceback.print_exc())
                exit(1)

                teams_missing.append(team_name)
                logger.warning(
                    f"\t Local repo {git_local_dir} is problematic; removing it..."
                )
                print(traceback.print_exc())
                print("\n")
                repo.close()
                shutil.rmtree(git_local_dir)
                continue

        # this just calls git rev-list --count /tags/<tag> to get the number of commits tracing to the tag
        try:
            no_commits = repo.git.rev_list(
                "--count", tag
            )  # get the no of commits tracing to the tag
        except git.exc.GitCommandError:
            no_commits = repo.git.rev_list(
                "--count", f"tags/{tag}"
            )  # get the no of commits tracing to the tag
        repo.close()
        # Finally, write teams that have repos (new/updated/unchanged) into submission timestamp file
        teams_cloned.append(
            {
                "team": team_name,
                "submitted_at": new_commit_time.strftime(util.DATE_FORMAT),
                "commit": new_commit,
                "tag": tag,
                "tagged_at": new_tagged_time.strftime(util.DATE_FORMAT),
                "no_commits": no_commits,
                "status": status,
            }
        )

    # the end....
    return (
        teams_cloned,
        teams_new,
        teams_updated,
        teams_unchanged,
        teams_missing,
        teams_notag,
        teams_noteam,
    )


def report_teams(type, teams):
    """
    Print the name of the teams for the class type

    :param type: string with the name of the class (new, updated, missing, etc.)
    :param teams: a list of team names
    :return:
    """
    print(f"{type}: {len(teams)}")
    for t in teams:
        print(f"\t {t}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clone a list of GIT repositories containing assignment submissions via a tag."
    )
    parser.add_argument(
        dest="REPOS_CSV",
        type=str,
        help="CSV file containing the URL git repo for each team (must contain two named columns: REPO_ID and REPO_URL).",
    )
    parser.add_argument(
        dest="TAG",
        type=str,
        help='commit tag to clone (use "master" for latest commit at master).',
    )
    parser.add_argument(
        dest="OUTPUT_FOLDER",
        type=str,
        help="the folder where to clone all repositories.",
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="if given, only the teams specified will be cloned/updated.",
    )
    parser.add_argument(
        "--file-timestamps",
        help="CSV filename to store the timestamps of submissions (default: %(default)s).",
        default="submissions_timestamps.csv",
    )
    # we could also use vars(parser.parse_args()) to make args a dictionary args['<option>']
    args = parser.parse_args()
    logger.info(f"Starting script on {TIMEZONE}: {NOW_ISO} - {args}")

    ###############################################
    # Validation checks
    ###############################################
    if not os.path.exists(args.REPOS_CSV):
        print(f"Repo CSV database {args.REPOS_CSV} does not exists!")
        exit(1)

    if (
        os.path.split(args.file_timestamps)[-2]
        and not os.path.split(args.file_timestamps)[-2]
    ):
        print(
            f"Path to timestamp file {args.file_timestamps} does not exists! Not able to dump cloning timestamp of repos anywhere. Quitting..."
        )
        exit(1)

    ###############################################
    # Get repos as desired
    ###############################################
    repos = util.get_repos_from_csv(args.REPOS_CSV, args.repos)
    if len(repos) == 0:
        logger.warning(
            f'No repos found in the mapping file "{args.REPOS_CSV}". Stopping.'
        )
        exit(0)

    # Perform the ACTUAL CLONING of all teams in list_teams
    (
        teams_cloned,
        teams_new,
        teams_updated,
        teams_unchanged,
        teams_missing,
        teams_notag,
        teams_noteam,
    ) = clone_team_repos(repos, args.TAG, args.OUTPUT_FOLDER)

    # Write the submission timestamp file
    logger.warning("Producing timestamp csv file...")
    TIMESTAMP_HEADER = [
        "team",
        "submitted_at",
        "commit",
        "tag",
        "tagged_at",
        "no_commits",
        "status",
    ]

    # Make a backup of an existing cvs timestamp file, if there is one
    timestamp_bak = None
    if os.path.exists(args.file_timestamps):
        logger.warning(
            f"Making a backup of existing timestamp file {args.file_timestamps}."
        )
        with open(args.file_timestamps, "r") as f:
            timestamp_bak = list(
                csv.DictReader(f)
            )  # read current timestamp file if exists
            # timestamp_back = list(csv.DictReader(f, fieldnames=TIMESTAMP_HEADER))

        time_now = util.get_time_now()
        shutil.copy(args.file_timestamps, f"{args.file_timestamps}-{time_now}.bak")

    with open(args.file_timestamps, "w") as csv_file:
        submission_writer = csv.DictWriter(csv_file, fieldnames=TIMESTAMP_HEADER)
        submission_writer.writeheader()

        # migrate all the other rows from the previous timestamp file, if needed
        if args.repos and timestamp_bak is not None:
            for row in timestamp_bak:
                if row["team"] not in args.repos:
                    submission_writer.writerow(row)

        # now dump all the teams that have been cloned into the csv timestamp file
        submission_writer.writerows(teams_cloned)

    # produce report of what was cloned
    print("\n ============================================== \n")
    report_teams("NEW TEAMS", teams_new)
    report_teams("UPDATED TEAMS", teams_updated)
    report_teams("UNCHANGED TEAMS", teams_unchanged)
    report_teams("TEAMS MISSING (or not cloned successfully)", teams_missing)
    report_teams("TEAMS WITH NO TAG", teams_notag)
    report_teams("REPOS WITH NO TEAM", teams_noteam)
    print("\n ============================================== \n")
