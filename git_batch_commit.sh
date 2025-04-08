#!/bin/bash

##### GET OPTIONS FROM COMMAND-LINE
NO_ARGS=$#   # Get the number of arguments passed in the command lin
ME=`basename "$0"`

if [ "$NO_ARGS" -lt 1 ]; then
  echo -e "USAGE: ./$ME <folder with repos>"
  exit
fi

echo
echo "# arguments called with ---->  ${@}     "
echo "# \$1 ---------------------->  $1       "
echo "# \$2 ---------------------->  $2       "
echo "# \$3 ---------------------->  $3       "
echo "# path to me --------------->  ${0}     "
echo "# parent path -------------->  ${0%/*}  "
echo "# my name ------------------>  ${0##*/} "
echo

# change file separator to handle filename with spaces
# https://www.cyberciti.biz/tips/handling-filenames-with-spaces-in-bash.html
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

#########################
# HERE GOES THE SCRIPT
#########################
COUNTER=0
for dir in $(ls -d $1/*) ; do

    # continue if not a directory
  	[ ! -d "$dir" ] && continue

    let COUNTER++
    echo "=================> Processing folder $COUNTER: "$dir""
    git -C "$dir" pull  # first update repo

    ######################################################
    # HERE IS WHERE WE DO THE CHANGES TO THE REPO IN $d/
    ######################################################
    # Get into student repo, add, commit and push

    # Replace automarking github
    rm -rf $dir/.github
    cp -a ./workshop-2-template.git/.github/ $dir/

    MESSAGE="Upgrade automarking workflow with new GH system"

    ## Copy good files into student repo
    # cp pacman-p1-search.git/pacman.py $dir/
    # MESSAGE = "Updated pacman.py; fix foodEdible issue"

    ######################################################
    # FINISH CHANGES
    ######################################################

    echo "Will commit with message: **$MESSAGE**"
    git -C $dir add .
    git -C $dir commit -m $MESSAGE
    git -C $dir push

    # Wait a bit to not be pushed out....
    echo
    sleep 3
done;

# restore $IFS
IFS=$SAVEIFS



