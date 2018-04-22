# Various Support Scripts for Teaching

## Scrape Github for repo info: `github-scrape.py`

It collects information in csv files on various searches.

* Uses [PyGithub]()https://github.com/PyGithub/PyGithub) Github API.

* Github searches: https://help.github.com/articles/searching-code/
* Github search limits: https://developer.github.com/v3/search/#rate-limit
    * 5000 per hour total (and 30 per minute for search API)
* Github search API: https://developer.github.com/v3/search/


## Clone set of GitHub repo: `github-clone-repos.py`

Clones many repos.


## Manage GIT-based Assignment Submissions:  `git-assignment-submissions.py`

This script manages assignment submissions done via GIT repositories. For example:

```
python3 git-assignment-submissions.py ai18-repos.csv submission git-submissions/
```

Once all git repos have been cloned in `git-submissions/`, one can build zip files from the submissions into directory `zip-submissions/` as follows:

```
for d in git-submissions/*; do echo "============> Processing ${d}" ; zip -j "./zip-submissions/`basename "$d.zip"`" "${d}"/p2-multiagent/* ;done
```

### Some useful commands

To count the number of commits between dates:

```
git log --after="2018-03-26T00:00:00+11:00" --before="2018-03-28T00:00:00+11:00" | grep "Date:" | wc -l
```

To copy just the new zip files:

```
rsync  -avt --ignore-existing  zip-submissions/*.zip AI18-assessments/project-2/zip-submissions/
```