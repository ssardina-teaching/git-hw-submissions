# Submission Management Support Scripts

REPO: https://github.com/ssardina-teaching/git-hw-submissions

These are some useful scripts that I use in teaching:

* `gh_classroom_collect.py`: will collect all repos in a given GitHub Classroom/Organization for a given assignment.
* `git_clone_submissions.py`: will clone and update a set of repositories (provided in a CSV file) for a given submission tag.
* `gh_authors_collect.py`: extract the number of commits per each author in a set of GitHub repositories. This can be used to do analysis of student contributions
* `git_create_wiki.py`: will push a template Wiki to a list of GitHub repos.
* `gh_member_bulk_team.py`: add/delete GH username to a list of teams in an organization (e.g., to add tutors to groups so they can see student repos).
* `gh_pr_feedback_check_merged.py`: check if a GH Classroom Feedback PRs have been (wrongly) merged in each repo.
* `gh_pr_feedback_comment.py`: push feedback marking to repos' Feedback PRs.
* `gg_get_worksheet.py`: dump a Google Sheet worksheet as CSV file (usually marking sheet).
* `git_batch_commit.sh`: a shell script template to make changes to a collection of repos.


Other scripts (under [`other-scripts/`](other-scripts/) folder):

* `gh_scrape_scrape.py`: Scrape GitHub for repo info via searches.
* `gh_clone_repos.py`: Clones set of GitHub repo.

All these scripts were tested under Python 3.6+

To install all requirements:

```bash
$ sudo pip install -r requirements.txt
```


- [Submission Management Support Scripts](#submission-management-support-scripts)
  - [`gh_classroom_collect.py`: collect repos from a GH Organizations](#gh_classroom_collectpy-collect-repos-from-a-gh-organizations)
  - [`git_clone_submissions.py`: batch git cloning](#git_clone_submissionspy-batch-git-cloning)
  - [`gh_authors_collect.py`: extract author commit stats](#gh_authors_collectpy-extract-author-commit-stats)
  - [`gh_create_wiki.py`: push Wiki template to list of repos](#gh_create_wikipy-push-wiki-template-to-list-of-repos)
  - [`gh_member_bulk_team.py`: add/delete GH username to GH teams](#gh_member_bulk_teampy-adddelete-gh-username-to-gh-teams)
  - [Some useful commands](#some-useful-commands)
  - [`git_batch_commit.sh`: a shell script template to make changes to a collection of repos.](#git_batch_commitsh-a-shell-script-template-to-make-changes-to-a-collection-of-repos)
  - [Links](#links)


## `gh_classroom_collect.py`: collect repos from a GH Organizations

The script `gh_classroom_collect.py` produces a CSV file with all the repos in a given GitHub Classroom for a particular assignment.

The CSV file produced, for each repo, the following information:

* the organization name of the GitHub classroom;
* the assignment prefix name;
* the user of the repo;
* the GitHub name of the repo; and
* the full SSH git URL specification.

The script requires a username and its password or file with GitHub access token that allows access to the organization.

For example, to get all the repos submitted for assignment with prefix `p0-warmup` into a CSV file `p0-repos.csv`:

```shell
$ python3 ../git-hw-submissions.git/gh_classroom_collect.py -u ssardina -t ~/.ssh/keys/github-token-ssardina-new-May_5-2021.txt RMIT-COSC1127-1125-AI21  p0-warmup p0-repos.csv
```

This will produce a CSV of this form:

```csv
ORG_NAME,ASSIGNMENT,REPO_ID,REPO_NAME,REPO_URL
RMIT-COSC1127-1125-AI21,p0-warmup,CallumA3791362,RMIT-COSC1127-1125-AI21/p0-warmup-CallumA3791362,git@github.com:RMIT-COSC1127-1125-AI21/p0-warmup-CallumA3791362.git
RMIT-COSC1127-1125-AI21,p0-warmup,eolivesjo,RMIT-COSC1127-1125-AI21/p0-warmup-eolivesjo,git@github.com:RMIT-COSC1127-1125-AI21/p0-warmup-eolivesjo.git
RMIT-COSC1127-1125-AI21,p0-warmup,bivhitscar,RMIT-COSC1127-1125-AI21/p0-warmup-bivhitscar,git@github.com:RMIT-COSC1127-1125-AI21/p0-warmup-bivhitscar.git
...
...
```

If we want to map repo's suffixex (github_username) to student ids (identifier), we can use `--student-map cosc1127-map.csv`

Next, we can use that CSV file to clone the corresponding repos at a given tag `submission` using the script `git_clone_submissions.py`.

```bash
$ python ../git-hw-submissions.git/git_clone_submissions.py --file-timestamps test/cosc1127_timestamps.csv p0/cosc1127-repos-p0.csv submission p0/
```

## `git_clone_submissions.py`: batch git cloning

Script `git_clone_submissions.py` clones a set of student/team repositories listed in a CSV file at a given _tagged_ commit.  The CVS file should contain the team name (under column name `TEAM`) and a GIT ssh link (under column name `GIT-URL`).

If a repository already exists, it will be _updated_ automatically:

* if the tag changed to a different commit, the new commit will be pulled;
* if the repo does not have the tag anymore (the student has withdraw the submission), the local copy will be removed from disk.

At the end, the script produces a CSV file with the information of each repo successfully cloned, including commit id (`commit`), time of the commit (`submitted_at`), and time of the tagging (`tagged_at`).  

The script depends on the [GitPython](https://gitpython.readthedocs.io) module:

```shell
$ pip3 install gitpython --user
```

For example, to clone Project 0 at commit with tag "`submission`" using the database of repos `p0-repos.csv`:

```shell
$ python ../git-hw-submissions.git/git_clone_submissions.py --file-timestamps p0/cosc1127_timestamps.csv p0-repos.csv submission p0/ &| tee p0/clone-p0.txt
```

All repos will be cloned within folder `p0/` and the file `p0/cosc1127_timestamps.csv` will contain the timestamps and commits of each repo cloned successfully. The file will contain the date of the commit linked to the tag and, if the tag is an annotated tag (and not just lightweight tag), it will also include the date tagged (otherwise they will be assumed the same). See annotated vs lightweight tags [here](https://git-scm.com/book/en/v2/Git-Basics-Tagging).

To just clone the last commit in the master branch, use `master` as the tag. 

The timezone used is defined by constant `TIMEZONE` in the script (default to Australia/Melbourne time zone).

## `gh_authors_collect.py`: extract author commit stats

Given a CSV file with a collection of repositories, extract in a CSV file how many commits each author has done per repo. For example:

```bash
python3 git-hw-submissions.git/gh_authors_collect.py -u ssardina \
    -t ~/.ssh/keys/github-token-ssardina.txt \
    --tag submission ai20-p2-repos.csv ai20-p2-authors.csv
```

The `--tag` option restricts to tags finishing in a given tag. If no tag is given, the whole repo is parsed.

The input csv file must have the fields:

* `REPO_NAME`: the full repo name: owner/organization + name of repo.
* `REPO_ID`: the id of the repo (e.g., team name).

## `gh_create_wiki.py`: push Wiki template to list of repos

Example:

```bash
$ python3 gh_create_wiki.py ../ai20-contest-repos.csv ~/AI20/assessments/project-contest/updated-src/wiki-template/
```

## `gh_member_bulk_team.py`: add/delete GH username to GH teams

For example, to add Axel to all the teams except teachers:

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

## `git_batch_commit.sh`: a shell script template to make changes to a collection of repos.

This script allows to commit and push changes to a collection of repos; for example to make edits to students' repos after they have been created.

## Links

- GitHub REST documentation: https://docs.github.com/en/rest
- PyGithub: https://github.com/PyGithub/PyGithub
- gitpython: http://www.legendu.net/misc/blog/hands-on-GitPython/
- gh API CLI tool: https://github.com/cli/cli ([manual](https://cli.github.com/manual/))