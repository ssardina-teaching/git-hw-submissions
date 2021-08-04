#!/bin/bash

##### GET OPTIONS FROM COMMAND-LINE
NO_ARGS=$#   # Get the number of arguments passed in the command lin
ME=`basename "$0"`

if [ "$NO_ARGS" -lt 1 ]; then
  echo -e "USAGE: ./$ME <folder wirh repos>"
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


#########################
# HERE GOES THE SCRIPT
#########################

for d in $1/*/ ; do
    echo "Processing $d"

    ## Copy good files into student repo
    cp pacman-p1-search.git/pacman.py $d/

    # Get into student repo, add, commit and push 
    cd $d
    echo $PWD
    git add .
    git commit -m "Updated pacman.py; fix foodEdible issue"
    git push

    # Get out of student repo (ready to process next)
    cd -
    echo
done

