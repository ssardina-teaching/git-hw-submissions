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
__copyright__ = "Copyright 2018-2022"

import shutil
import os
import sys
import argparse
import csv
import time
import traceback

# local utilities
import util

# https://gitpython.readthedocs.io/en/stable/reference.html
# http://gitpython.readthedocs.io/en/stable/tutorial.html
import git

# from git import Repo, Git

import logging
import coloredlogs

# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%a, %d %b %Y %H:%M:%S",
)


LOGGING_LEVEL = "INFO"
LOGGING_FMT = "%(asctime)s %(levelname)s %(message)s"


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


def clone_team_repos(list_repos, tag_str, output_folder):
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
    no_repos = len(list_repos)
    list_repos.sort(key=lambda tup: tup[CSV_REPO_ID].lower())  # sort the list of teams

    logging.info(f"About to clone {no_repos} repo teams into folder {output_folder}/.")
    teams_new = []
    teams_missing = []
    teams_unchanged = []
    teams_updated = []
    teams_cloned = []
    teams_notag = []
    teams_noteam = []
    for c, row in enumerate(list_repos, 1):
        print("\n")
        http_repo_link = row[CSV_REPO_GIT].replace(
            "git@github.com:", "http://github.com/"
        )
        logging.info(
            f"Processing {c}/{no_repos} team **{row[CSV_REPO_ID]}** in git url {http_repo_link}."
        )

        team_name = row[CSV_REPO_ID]
        if not team_name:
            logging.info(
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
            logging.info(f"Trying to clone NEW team repo from URL {git_url}.")
            try:
                repo = git.Repo.clone_from(git_url, git_local_dir, branch=tag_str)
                new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                    repo, tag_str="head"
                )
                logging.info(
                    f"Team {team_name} cloned successfully with tag date {new_commit_time}."
                )
                teams_new.append(team_name)
                status = "new"
            except git.GitCommandError as e:
                teams_missing.append(team_name)
                logging.warning(
                    f"Repo for team {team_name} with tag/branch {tag_str} cannot be cloned: {e.stderr}"
                )
                continue
            except KeyboardInterrupt:
                logging.warning(
                    "Script terminated via Keyboard Interrupt; finishing..."
                )
                sys.exit("keyboard interrupted!")
            except TypeError as e:
                logging.warning(
                    f"Repo for team {team_name} was cloned but has no tag {tag_str}, removing it...: {e}"
                )
                repo.close()
                shutil.rmtree(git_local_dir)
                teams_notag.append(team_name)
                continue
            except Exception as e:
                logging.error(
                    f"Repo for team {team_name} cloned but unknown error when getting tag {tag_str}; should not happen. Stopping... {e}"
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

                logging.info(
                    f"Existing LOCAL submission for {team_name} dated {local_commit_time} ({str(repo.commit())[:7]}); updating it..."
                )

                # Next, first fetch from remote all tags and new commits
                # As of Git 2.2, we need to force to allow overwriting existint tags!
                # https://gitpython.readthedocs.io/en/stable/reference.html#git.remote.Remote.fetch
                repo.remote("origin").fetch(tags=True, force=True)

                if tag_str in ["master", "main"]:
                    repo.git.checkout(tag_str, force=True)
                    repo.git.pull()
                    new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                        repo, tag_str="head"
                    )
                else:
                    new_commit_time, new_commit, new_tagged_time = util.get_tag_info(
                        repo, tag_str
                    )
                    if (
                        new_commit_time is None
                    ):  # tag has been deleted! remove local repo, no more submission
                        teams_missing.append(team_name)
                        logging.info(
                            f"No tag {tag_str} in the repository for team {team_name} anymore; removing it..."
                        )
                        repo.close()
                        shutil.rmtree(git_local_dir)
                        continue
                    # Checkout the submission tag (doesn't matter if there is no update, will stay as is)
                    repo.git.checkout(tag_str)

                logging.debug(
                    f"Tag *{tag_str}* seen in in commit {str(new_commit)[:7]} ({new_commit_time}) tagged on {new_tagged_time}"
                )

                # Now process timestamp to report new or unchanged repo
                if new_commit_time == local_commit_time:
                    logging.info(f"Team {team_name} submission has not changed.")
                    teams_unchanged.append(team_name)
                    status = "unchanged"
                else:
                    logging.info(
                        f"Team {team_name} updated successfully with new tag date {new_commit_time}"
                    )
                    teams_updated.append(team_name)
                    status = "updated"
            except git.GitCommandError as e:
                teams_missing.append(team_name)
                logging.warning(
                    f"Problem with existing repo for team {team_name}; removing it: {e} - {e.stderr}"
                )
                print("\n")
                repo.close()
                continue
            except KeyboardInterrupt:
                logging.warning(
                    "Script terminated via Keyboard Interrupt; finishing..."
                )
                repo.close()
                sys.exit(1)
            except:  # catch-all
                print(traceback.print_exc())
                exit(1)

                teams_missing.append(team_name)
                logging.warning(
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
                "--count", tag_str
            )  # get the no of commits tracing to the tag
        except git.exc.GitCommandError:
            no_commits = repo.git.rev_list(
                "--count", f"tags/{tag_str}"
            )  # get the no of commits tracing to the tag
        repo.close()
        # Finally, write teams that have repos (new/updated/unchanged) into submission timestamp file
        teams_cloned.append(
            {
                "team": team_name,
                "submitted_at": new_commit_time.strftime(util.DATE_FORMAT),
                "commit": new_commit,
                "tag": tag_str,
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
        dest="repos_csv_file",
        type=str,
        help="CSV file containing the URL git repo for each team (must contain two named columns: REPO_ID and REPO_URL).",
    )
    parser.add_argument(
        dest="tag_str",
        type=str,
        help='commit tag to clone (use "master" for latest commit at master).',
    )
    parser.add_argument(
        dest="output_folder",
        type=str,
        help="the folder where to clone all repositories.",
    )
    parser.add_argument(
        "--teams",
        "--repos",
        nargs="+",
        help="if given, only the teams specified will be cloned/updated.",
    )
    parser.add_argument(
        "--file-timestamps",
        help="CSV filename to store the timestamps of submissions (default: %(default)s).",
        default="submissions_timestamps.csv",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Show debugging info while processing games (default: %(default)s).",
    )
    # we could also use vars(parser.parse_args()) to make args a dictionary args['<option>']
    args = parser.parse_args()
    print(f"Running the script on: {util.get_time_now()}", flush=True)

    # Set format and level of logging
    coloredlogs.install(level="DEBUG" if args.debug else LOGGING_LEVEL, fmt=LOGGING_FMT)

    if not os.path.exists(args.repos_csv_file):
        print(f"Repo CSV database {args.repos_csv_file} does not exists!")
        exit(1)

    if (
        os.path.split(args.file_timestamps)[-2]
        and not os.path.split(args.file_timestamps)[-2]
    ):
        print(
            f"Path to timestamp file {args.file_timestamps} does not exists! Not able to dump cloning timestamp of repos anywhere. Quitting..."
        )
        exit(1)

    # Get the list of TEAM + GIT REPO links from csv file
    list_repos = util.get_repos_from_csv(args.repos_csv_file, args.teams)

    if len(list_repos) == 0:
        logging.warning(
            f'No repos found in the mapping file "{args.repos_csv_file}". Stopping.'
        )
        exit(0)

    print(args)
    print(f"Start cloning repos at: {util.get_time_now()}")

    # Perform the ACTUAL CLONING of all teams in list_teams
    (
        teams_cloned,
        teams_new,
        teams_updated,
        teams_unchanged,
        teams_missing,
        teams_notag,
        teams_noteam,
    ) = clone_team_repos(list_repos, args.tag_str, args.output_folder)

    # Write the submission timestamp file
    logging.warning("Producing timestamp csv file...")
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
        logging.warning(
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
        if args.teams and timestamp_bak is not None:
            for row in timestamp_bak:
                if row["team"] not in args.teams:
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
