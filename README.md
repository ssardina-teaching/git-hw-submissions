# Various Support Scripts for Teaching


## Scrape Github for repo info: _github-scrape.py_

It collects information in csv files on various searches.

* Uses [PyGithub]()https://github.com/PyGithub/PyGithub) Github API.

* Github searches: https://help.github.com/articles/searching-code/
* Github search limits: https://developer.github.com/v3/search/#rate-limit
    * 5000 per hour total (and 30 per minute for search API)
* Github search API: https://developer.github.com/v3/search/


## Clone set of GitHub repo: _github-clone-repos.py_

Clones many repos.



## Manage GIT-based Assignment Submissions:  _git-assignment-submissions.py_

This script manages assignment submissions done via GIT repositories using tags.

```
usage: git-assignment-submissions.py [-h] [--team TEAM]
                                     [--file-timestamps FILE_TIMESTAMPS]
                                     team_csv_file tag_str output_folder

Clone a list of GIT repositories contatining assignment submissions via a tag.

positional arguments:
  team_csv_file         csv file containing the URL git repo for each team
                        (must contain two named columns: TEAM and GIT-URL).
  tag_str               commit tag representing a submission.
  output_folder         the folder where to clone all repositories.

optional arguments:
  -h, --help            show this help message and exit
  --team TEAM           to mark a specific team only.
  --file-timestamps FILE_TIMESTAMPS
                        filename to store the timestamps of submissions
                        (default: submissions_timestamps.csv).
```

For example:

```
python3 git-assignment-submissions.py ai18-repos.csv submission-1 git-submissions/
```

This will download all submissions of teams listed in csv file `ai18-repos.csv` using tag `submission-1`
and save them in directory `git-submissions/`. A file `submissions_timestamps.csv' with the timestamps and commits of each repo cloned successfully.

If one already has a `submissions_timestamps.csv' (from previous downloads) or want to use a different name, one can use option `--file-timestamps`.



Once all git repos have been cloned in `git-submissions/`, one can build zip files from the submissions into directory `zip-submissions/` as follows:

```
for d in git-submissions-p2/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p2/`basename "$d.zip"`" "${d}"/p2-multiagent/* ;done
```

or for the final CTF project:

``
for d in git-submissions-p4/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p4/`basename "$d.zip"`" "${d}"/pacman-contest/* ;done
```

### Some useful commands

To count the number of commits between dates:

```
git log --after="2018-03-26T00:00:00+11:00" --before="2018-03-28T00:00:00+11:00" | grep "Date:" | wc -l
```

To copy just the new zip files:

```
rsync  -avt --ignore-existing  zip-submissions-p4/*.zip AI18-assessments/project-4/zip-submissions/
```
