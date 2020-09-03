# Submission Management Support Scripts 

These are some useful scripts that I use in teaching:

* `gh_classroom_collect.py`: will collect all repos in a given GitHub Classroom/Organization for a given assignment.
* `git_clone_submissions.py`: will clone and update a set of repositories (provided in a CSV file) for a given submission tag.
* `gh_authors_collect.py`: extract the number of commits per each author in a set of GitHib repositories. This can be used to do analysis of student contributions

Other:

* `gh_scrape_scrape.py`: Scrape Github for repo info via searches.
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

For example:

```bash
python3 gh_classroom_collect.py --team-map test/cosc1127-map.csv \
     -u ssardina -t ~/.ssh/keys/github-token-ssardina.txt \
     RMIT-COSC1127-1125-AI project-0-tutorial test/cosc1127-repos.csv
```

This will produce a CSV of this form:

```csv
ORG_NAME,ASSIGNMENT,USERNAME,TEAM,REPO-NAME,GIT-URL
RMIT-COSC1127-1125-AI,project-0-tutorial,msardina,boca,RMIT-COSC1127-1125-AI/project-0-tutorial-msardina,git@github.com:RMIT-COSC1127-1125-AI/project-0-tutorial-msardina.git
...
...
```

Now, with such CSV file we can clone the corresponding repos at tag `submission` into `test/repos` using the script `git_clone_submissions.py` (see below):
 
```bash
python3 git_clone_submissions.py --file-timestamps test/cosc1127_timestamps.csv \
      test/cosc1127-repos.csv submission test/repos/
```



## Clone GIT-based Homework Submissions:  

Script `git_clone_submissions.py` clones a set of student/team repositories listed in a CSV file at a given _tagged_ commit.  The CVS file should contain the team name (under column name `TEAM`) and a GIT ssh link (under column name `GIT-URL`).

If a repository already exists, it will be _updated_ automatically:
 
 * if the tag changed to a different commit, the new commit will be pulled;
 * if the repo does not have the tag anymore (the student has withdraw the submission), the local copy will be removed from disk.
 
At the end, the script produces a CSV file with the information of each repo successfully cloned, including commit id (`commit`), time of the commit (`submitted_at`), and time of the tagging (`tagged_at`).  

The script depends on the [GitPython](https://gitpython.readthedocs.io) module:

```bash
pip3 install gitpython --user
```

To get all the options, use call the script with option `-h`:

```bash
usage: git_clone_submissions.py -h
```

For example:

```bash
python3 git_clone_submissions.py --file-timestamps AI20_timestamps.csv \
    AI20-p0.csv submission p0-repos/ | tee clone-Jul-25.txt
```

This will download all submissions of teams listed in csv file `AI20-p0.csv` using tag `submission` and save them in directory `p0-repos/`. 

A file `AI20_timestamps.csv` with the timestamps and commits of each repo cloned successfully. The timezone used is defined by constant `TIMEZONE` in the script (default to Australia/Melbourne time zone).



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


### Some useful commands

Once all git repos have been cloned in `git-submissions/`, one can build zip files from the submissions into directory `zip-submissions/` as follows:

```
for d in git-submissions-p2/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p2/`basename "$d.zip"`" "${d}"/p2-multiagent/* ;done
```

or for the final CTF project:

```
for d in git-submissions-p4/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p4/`basename "$d.zip"`" "${d}"/pacman-contest/* ;done
```


To count the number of commits between dates:

```
git log --after="2018-03-26T00:00:00+11:00" --before="2018-03-28T00:00:00+11:00" | grep "Date:" | wc -l
```

To copy just the new zip files:

```
rsync  -avt --ignore-existing  zip-submissions-p4/*.zip AI18-assessments/project-4/zip-submissions/
```


## Other scripts

Under [other-scripts/](other-scripts) folder.

### Scrape Github repositories

Script `gh_scrape.py` collects information in CSV files on various searches.

* Uses [PyGithub](https://github.com/PyGithub/PyGithub) Github API.

* Github searches: https://help.github.com/articles/searching-code/
* Github search limits: https://developer.github.com/v3/search/#rate-limit
    * 5000 per hour total (and 30 per minute for search API)
* Github search API: https://developer.github.com/v3/search/


### Clone set of GitHub repo

Script `gh_clone_repos.py` clones a list of GitHub repos given in a CSV file.

### GitHub Classroom script

Various manipulation commands for GitHub classrrom.

