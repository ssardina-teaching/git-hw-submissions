#!/bin/bash

##### GET OPTIONS FROM COMMAND-LINE
NO_ARGS=$#   # Get the number of arguments passed in the command lin
ME=`basename "$0"`

if [ "$NO_ARGS" -lt 3 ]; then
  echo -e "build zip files from directory submissions. zip file name wil be each submission directory \n"
  echo -e "USAGE: ./$ME <dir-with-submissions> <internal project dir> <output zip dir>"
  echo -e "\t\t <dir-with-submissions>: folder containing non-zipped submissions"
  echo -e "\t\t <internal project dir>: folder inside each submission where the project of interest is located"
  echo -e "\t\t <output zip dir>: folder where zip files will be saved"
  echo
  exit
fi


INPUT=$1
DIR=$2
OUT=$3



echo "Building ZIP files from submissions in dir $1, subdir $2, into directory $3"


for d in git-submissions-p4/*; do 
	echo "============> Processing ${d}" 
	zip -q -j "$OUT/`basename "$d.zip"`" "${d}"/$DIR/* ;
done
