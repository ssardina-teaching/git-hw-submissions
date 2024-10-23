# Teaching scripts

This repo contains useful scripts I developed over the years to support student's submissions for homeworks and projects. They include tools to manage Git and  GitHub repositories, Google Workspaces (drive, spreadsheets), and shell/filesystem scripts.

- [Teaching scripts](#teaching-scripts)
  - [Setup](#setup)
  - [GitHub \& GitHub Classrooms](#github--github-classrooms)
    - [`gh_classroom_collect.py`: collect repos from a GH Organizations](#gh_classroom_collectpy-collect-repos-from-a-gh-organizations)
    - [`gh_authors_collect.py`: extract commits per author](#gh_authors_collectpy-extract-commits-per-author)
    - [`gh_create_wiki.py`: push Wiki template to list of repos](#gh_create_wikipy-push-wiki-template-to-list-of-repos)
    - [`gh_member_bulk_team.py`: add/delete GH username to GH teams](#gh_member_bulk_teampy-adddelete-gh-username-to-gh-teams)
    - [`gh_pr_merge.py`: bulk merge of PRs](#gh_pr_mergepy-bulk-merge-of-prs)
    - [`gh_pr_feedback_create.py`: create Feedback PRs](#gh_pr_feedback_createpy-create-feedback-prs)
    - [`gh_pr_check_merged_forced.py`: check for merged PR and forced pushes](#gh_pr_check_merged_forcedpy-check-for-merged-pr-and-forced-pushes)
    - [`gh_pr_feedback_comment.py`: push comments to repo's PRs](#gh_pr_feedback_commentpy-push-comments-to-repos-prs)
  - [Git Tools](#git-tools)
    - [`git_clone_submissions.py`: batch git cloning](#git_clone_submissionspy-batch-git-cloning)
    - [`git_batch_commit.sh`: bulk commit and push to repos](#git_batch_commitsh-bulk-commit-and-push-to-repos)
  - [Google Tools](#google-tools)
    - [`gg_get_worksheet.py`: download Google Sheet worksheet as CSV file](#gg_get_worksheetpy-download-google-sheet-worksheet-as-csv-file)
    - [`gg_sheet_submissions.py`: download submissions from Google Sheets](#gg_sheet_submissionspy-download-submissions-from-google-sheets)
    - [`gg_drive_download.py`: download files in Drive folder](#gg_drive_downloadpy-download-files-in-drive-folder)
  - [Some useful commands](#some-useful-commands)


## Setup

To install all requirements:

```bash
$ sudo pip install -r requirements.txt
```

The libraries used are:

- GitHub REST documentation: https://docs.github.com/en/rest
- PyGithub: https://github.com/PyGithub/PyGithub
- gitpython: http://www.legendu.net/misc/blog/hands-on-GitPython/
- gh API CLI tool: https://github.com/cli/cli ([manual](https://cli.github.com/manual/))

## GitHub & GitHub Classrooms

These `gh_xxx.py` scripts mostly use [PyGithub](https://github.com/PyGithub/PyGithub). Scripts will require a GitHub access token that allows access the corresponding repos/organization.

* `gh_classroom_collect.py`: will collect all repos in a given GitHub Classroom/Organization for a given assignment (using the prefix name of the project).
* `gh_authors_collect.py`: extract the number of commits per each author in a set of GitHub repositories. This can be used to do analysis of student contributions
* `gh_member_bulk_team.py`: add/delete GH username to a list of teams in an organization (e.g., to add tutors to groups so they can see student repos).
* `gh_pr_feedback_check_merged.py`: check if a GH Classroom Feedback PRs have been (wrongly) merged in each repo.
* `gh_pr_feedback_comment.py`: push feedback marking to repos' Feedback PRs.

Another tool that one can consider is [gh API CLI](https://github.com/cli/cli) tool; see the [manual](https://cli.github.com/manual/).


### `gh_classroom_collect.py`: collect repos from a GH Organizations

Produces a CSV file with all the repos in a given GitHub Classroom for a particular assignment, using its corresponding prefix.

For example, to get all the repos submitted for AI24 project with prefix `p3-prolog` into a CSV file `repos.csv`:

```shell
$  python ./gh_classroom_collect.py -t ~/.ssh/keys/gh-token-ssardina.txt RMIT-COSC1127-1125-AI24  p3-prolog repos.csv |& tee -a repos.log
```

> [!NOTE]
> The CSV `repo.csv` file will be used for many later tasks, including cloning the repos locally using script `git_clone_submissions.py`, extracting collaborators, etc.


### `gh_authors_collect.py`: extract commits per author

Produce a CSV file with how many commits each author has done per repo. For example:

```shell
$ python ./gh_authors_collect.py ~/.ssh/keys/github-token-ssardina.txt \
    --tag submission repos.csv authors.csv
```

The `--tag` option restricts to tags finishing in a given tag. If no tag is given, the whole repo is parsed to the head of `main`.

### `gh_create_wiki.py`: push Wiki template to list of repos

This script will push a template Wiki to each repo:

```bash
$ python ./gh_create_wiki.py repos.csv ./wiki-template
```

See [wiki-template](wiki-template/) for an example of a Wiki template.


### `gh_member_bulk_team.py`: add/delete GH username to GH teams

This script will add a GH username to GH teams in an organization. For example, to add Axel to all the teams except teams `teachers` and `headtutor`:

```shell
$ python gh_member_bulk_team.py RMIT-COSC2780-2973-IDM24  axelahmer  --nteams  "teachers" "headtutor"
Running the script on: 2024-05-18-00-35-27
Sat, 18 May 2024 00:35:27 INFO     Getting organization RMIT-COSC2780-2973-IDM24...
Sat, 18 May 2024 00:35:27 INFO     Getting GH user for axelahmer...
Teams available: ['AI NPCs', 'ASP Dads', 'Galacticos', 'gASP', 'Harry Ron and Hermoine', 'IDM Project', 'Intellect Realm', 'Inter-Dimensional Masochists (IDM)', 'Logic Nexus', 'Lorem Ipsum', 'Mister World Wide', 'Prolog nightmares again', 'sajeevan', 'Super awesome team name', 'teachers', 'TRY']
Adding user **axelahmer** to team AI NPCs
Adding user **axelahmer** to team ASP Dads
Adding user **axelahmer** to team Galacticos
Adding user **axelahmer** to team gASP
Adding user **axelahmer** to team Harry Ron and Hermoine
Adding user **axelahmer** to team IDM Project
Adding user **axelahmer** to team Intellect Realm
Adding user **axelahmer** to team Inter-Dimensional Masochists (IDM)
Adding user **axelahmer** to team Logic Nexus
Adding user **axelahmer** to team Lorem Ipsum
Adding user **axelahmer** to team Mister World Wide
Adding user **axelahmer** to team Prolog nightmares again
Adding user **axelahmer** to team sajeevan
Adding user **axelahmer** to team Super awesome team name
Adding user **axelahmer** to team TRY
```

### `gh_pr_merge.py`: bulk merge of PRs

This script can be used to merge PRs in a set of repos. This is useful when a PR have been opened in each student repo to implement updates in the project spec via GitHub Classroom sync feature (new in 2024).

For example, to merge PR with title `Sync` from the 40th repo in `repo.csv`:

```shell
$ python ./gh_pr_merge.py repos.csv -t ~/.ssh/keys/gh-token-ssardina.txt --title Sync --start 40 |& tee -a merge_pr.log
```

### `gh_pr_feedback_create.py`: create Feedback PRs

Check which repos are missing an expected Feedback PR #1 from GitHub Classroom; and create them as needed. This may be needed because sometimes GH Classroom failed to create the PRs in some repos.

For example:

```shell
$ python ./gh_pr_create.py -t ~/.ssh/keys/gh-token-ssardina.txt repos.csv a7b3d7aee55d00d55ee29b8a505d17fc8283e9f8 |& tee pr_create.log
```

Notice that the script needs the list of repos to consider ()`repos.csv`) and the base sha to create the Feedback branch and corresponding PR. Because the repos were created by GH Classroom, the first commit should have the same sha than the original staff template.

### `gh_pr_check_merged_forced.py`: check for merged PR and forced pushes

This script will check for PRs that have been merged and 

```shell
$ python ../git-hw-submissions.git/gh_pr_check_merged_forced.py  -t ~/.ssh/keys/gh-token-ssardina.txt   repos.csv
```

It will leave two CSV files `pr_merged.csv` and `pr_forced.csv` with the corresponding repos' ids.


### `gh_pr_feedback_comment.py`: push comments to repo's PRs

This tool will push feedback comments to PRs in GH repositories. This may be useful to provide feedback and results to students after automarking. It requires:

- A CSV file with the list of all relevant repos to process (e.g., student's projects).
- A CSV file with the marking results (points, marks, comments, etc).
- A folder with the automarking reports as text files.
- A Python file defining two functions that process a row in the marking results:
  - `check_submission`: can be used to check if the row contains a legal/successful submission. It will return whether the row/submission needs to be skipped and a string message to be posted to the PR, if any (e.g., the reason why the submission was not marked and skipped).
  - `report_feedback`: produce the actual feedback text to be posted in the PR.

Now push all feedback to their pull requests from fist row (1) to row 5:

```shell
$ python ./gh_pr_feedback_comment.py repos.csv marking.csv reports config_report_p2.py -t ~/.ssh/keys/gh-token-ssardina.txt  -s 1 -e 5 |& tee -a pr_feedback_0-10.log
```

Use `--repos ssardina juan` to restrict to the three repos, and `--dry-run` to send feedback to console instead of repos:

```shell
$ python  ./gh_pr_feedback_comment.py repos.csv marking.csv reports -t ~/.ssh/keys/gh-token-ssardina.txt --repos ssardina juan --dry-run
```


## Git Tools

These tools use [GitPython](https://gitpython.readthedocs.io/en/stable/tutorial.html) module to have Git API in Python.

* `git_clone_submissions.py`: will clone and update a set of repositories (provided in a CSV file) for a given submission tag.
* `git_create_wiki.py`: will push a template Wiki to a list of GitHub repos.
* `git_batch_commit.sh`: a shell script template to make changes to a collection of repos.


### `git_clone_submissions.py`: batch git cloning

This tool clones a set of student/team repositories listed in a CSV file at a given _tagged_ commit. The CVS file should contain the team name (under column name `TEAM`) and a GIT ssh link (under column name `GIT-URL`).

If a repository already exists, it will be _updated_ automatically:

* if the tag changed to a different commit, the new commit will be pulled;
* if the repo does not have the tag anymore (the student has withdraw the submission), the local copy will be removed from disk.

At the end, the script produces a CSV file with the information of each repo successfully cloned, including commit id (`commit`), time of the commit (`submitted_at`), and time of the tagging (`tagged_at`).

For example, to clone Project 0 at commit with tag "`final`" using the database of repos `repos.csv`:

```shell
$ python ./git_clone_submissions.py --file-timestamps timestamps.csv repos.csv final submissions/ &| tee clone.log
```

All repos will be cloned within folder `submissions/` and the file `timestamps.csv` will contain the timestamps and commits of each repo cloned successfully. The file will contain the date of the commit linked to the tag. If the tag is an annotated tag (and not just lightweight tag), it will also include the date tagged (otherwise they will be assumed the same); see [annotated vs lightweight tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging).

To just clone the last commit in the master branch, use `main` as the tag.

The timezone used is defined by constant `TIMEZONE` in the script (defaults to `Australia/Melbourne` time zone).


### `git_batch_commit.sh`: bulk commit and push to repos

This script allows to commit and push changes to a collection of repos that already exist in a folder. This is useful to make edits to students' repos after they have been created.

## Google Tools

To access [Google Workspaces](https://developers.google.com/workspace) resources via the Google API, one needs to enable the API access and get a proper authentication credentials. Different APIs are provided for teh different resources (drive, gmail, sheet, etc.).

For authentication to Google Workspaces one needs the the application configurations file from APIs Console. Check the [Google Sheet API setup process](https://developers.google.com/sheets/api/quickstart/python) to obtain a `client_secret.json` (same as`credentials.json`) file for your project. PyDrive2 also explains how to get the file [here](https://docs.iterative.ai/PyDrive2/quickstart/#authentication).

All access to Google API requires authentication; usually the workflow is as follows:

* Go to the [Google API Access Panel](https://console.developers.google.com/apis/credentials).
* Create a project.
* Create an OAuth consent screen.
* Create credentials of type "OAuth Client ID".
* Download the JSON file of such credentials and name it `client_secrets.json`
* Place the file in the same directory as the scripts.


> [!TIP]
> Read [Integrating Google Drive API with Python: A Step-by-Step Guide](https://medium.com/the-team-of-future-learning/integrating-google-drive-api-with-python-a-step-by-step-guide-7811fcd16c44).
> 
> - [Google Sheet API](https://developers.google.com/sheets/api/guides/concepts) access:
>   - [gsheets](https://gsheets.readthedocs.io/en/stable/index.html)
>   - [pygsheets](https://github.com/nithinmurali/pygsheets)
> - [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk) access:
>   - [PyDrive2](https://docs.iterative.ai/PyDrive2/) package for more abstract access to the .
> - [Google Forms API](https://developers.google.com/forms/api/guides):


### `gg_get_worksheet.py`: download Google Sheet worksheet as CSV file

This script allows to download a Google Sheet from the cloud. It relies on the [gsheets](https://gsheets.readthedocs.io/en/stable/index.html) package to access the [Google Sheet API](https://developers.google.com/sheets/api/guides/concepts). 

The sheet to download is often a marking sheet. For example, to get the sheet `MARKING` from Google Spreadsheet with id `1kX-fa3_DMNDQROUr1Y-cG89UksTUUqlYdrNcV1yN6NA`:

```shell
$ python ./gg_get_worksheet.py 1kX-fa3_DMNDQROUr1Y-cG89UksTUUqlYdrNcV1yN6NA MARKING -c ~/.ssh/keys/credentials.json -o marking.csv
```
The `credentials.json` was obtained via the [Google Sheet API setup process](https://developers.google.com/sheets/api/quickstart/python). The first time that is used, a permission will be required. A certificate file `storage.json` will be left then that will allow direct access from there on (until certificate expires).

The authentication will be done via console. Use `--webserver` to open an actual browser.

### `gg_sheet_submissions.py`: download submissions from Google Sheets

This script can process Google Sheets produced by Google Forms, and download links to uploaded files in each submission. Files will be placed in folders identifying each submission, for example with the student number or email associated to the submission.

For example, to download the files recorded in column `G` in the worksheet `W4-resolution` of a Google Sheet with id `1ogCRbx...`, and save each in a folder `submission/XXXX` where `XXXX` is the student number recorded in column `C`:

```shell
$ python ./gg_sheet_submissions.py 1ogCRbxB3seVhoqhD7iBmVZ8EdpvGEB94oLowDIs5s2g W4-resolution tea --output test/submissions --file-name test.cnf --column-id C --column-file G
```

### `gg_drive_download.py`: download files in Drive folder

This tool allows downloading file submissions in a Google Drive folder, usually submitted via a Google Form by students. It uses [PyDrive2](https://docs.iterative.ai/PyDrive2/) package for more abstract access to the [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk).

```shell
$ python ./gg_drive_download.py 1mttf61NwuFNY25idwWw5AKzV3tQQbwlMp980i-9vnkK3PIV4o7ZOtykWvjM-VLqmHuYJ0jX4 -c ~/.ssh/keys/credentials.json --output test/submissions --file-name submissions.cnf
```

This script is a new and simpler version of the one in [this repo](https://github.com/ssardina-teaching/google-assignment-submission).

## Some useful commands

Once all git repos have been cloned in `git-submissions/`, one can build zip files from the submissions into directory `zip-submissions/` as follows:

```bash
for d in git-submissions-p2/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p2/`basename "$d.zip"`" "${d}"/p2-multiagent/* ;done
```

or for the final CTF project:

```bash
for d in git-submissions-p4/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p4/`basename "$d.zip"`" "${d}"/pacman-contest/* ;done
```

To count the number of commits between dates:

```bash
git log --after="2018-03-26T00:00:00+11:00" --before="2018-03-28T00:00:00+11:00" | grep "Date:" | wc -l
```

To copy just the new zip files:

```bash
rsync  -avt --ignore-existing  zip-submissions-p4/*.zip AI18-assessments/project-4/zip-submissions/
```
