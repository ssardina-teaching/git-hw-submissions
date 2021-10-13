# Submission Management Support Scripts

These are some useful scripts that I use in teaching:

* `gh_classroom_collect.py`: will collect all repos in a given GitHub Classroom/Organization for a given assignment.
* `git_clone_submissions.py`: will clone and update a set of repositories (provided in a CSV file) for a given submission tag.
* `gh_authors_collect.py`: extract the number of commits per each author in a set of GitHub repositories. This can be used to do analysis of student contributions
* `git_create_wiki.py`: will push a template Wiki to a list of GitHub repos.
* `git_batch_commit.sh`: a shell script template to make changes to a collection of repos.

Other scripts (under [`other-scripts/`](other-scripts/) folder):

* `gh_scrape_scrape.py`: Scrape GitHub for repo info via searches.
* `gh_clone_repos.py`: Clones set of GitHub repo.

All this scripts were tested under Python 3.6.

## Setup

To install all requirements:

```bash
sudo apt install python3-pip
sudo pip3 install -r requirements.txt
```

## Extract repos from a GitHub Classroom/Organization

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

## Clone GIT-based Homework Submissions  

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

All repos will be cloned within folder `p0/` and the file `p0/cosc1127_timestamps.csv` will contain the timestamps and commits of each repo cloned successfully. 

To just clone the last commit in the master branch, use `master` as the tag. 

The timezone used is defined by constant `TIMEZONE` in the script (default to Australia/Melbourne time zone).

## Extract author commit stats

Given a CSV file with a collection of repositories, extract in a CSV file how many commits each author has done per repo. For example:

```bash
python3 git-hw-submissions.git/gh_authors_collect.py -u ssardina \
    -t ~/.ssh/keys/github-token-ssardina.txt \
    --tag submission ai20-p2-repos.csv ai20-p2-authors.csv
```

The `--tag` option restricts to tags finishing in a given tag.

The input csv file must have the fields:

* `REPO_NAME`: the full repo name: owner/organization + name of repo.
* `REPO_ID`: the id of the repo (e.g., team name).

## Push Wiki template to a list of repos

Example:

```bash
$ python3 gh_create_wiki.py ../ai20-contest-repos.csv ~/AI20/assessments/project-contest/updated-src/wiki-template/
```

### Some useful commands

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

