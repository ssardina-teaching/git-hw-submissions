#!/bin/bash

python3 git-assignment-submissions.py --file-timestamps link-AI18/project-3/submission_timestamps.csv link-AI18/project-3/TEAMS-REG-P3.csv submission-3 git-submissions-p3/

for d in git-submissions-p3/*; do echo "============> Processing ${d}" ; zip -q -j "./zip-submissions-p3/`basename "$d.zip"`" "${d}"/p3-reinforcement/* ;done

rsync -avt --delete zip-submissions-p3/* link-AI18/project-3/zip-submissions/

