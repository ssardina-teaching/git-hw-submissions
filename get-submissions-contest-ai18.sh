#!/bin/bash

python3 git-assignment-submissions.py link-AI18/project-4-contest/AI18-Contest-TEAMS.csv submission-contest git-submissions-p4/ --file-timestamps link-AI18/project-4-contest/submissions_timestamps.csv

rm -f ./zip-submission-p4/*.zip

for d in git-submissions-p4/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p4/`basename "$d.zip"`" "${d}"/pacman-contest/* ;done

rsync  -avt --delete zip-submissions-p4/*.zip link-AI18/project-4-contest/zip-submissions/
