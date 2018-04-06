#!/usr/bin/env python

import os
import argparse
import csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This script will clone a list of github repos.'
    )
    parser.add_argument(
        '--file-csv',
        help='file where the gihub repo names are listed'
    )
    args = parser.parse_args()

    if args.file_csv is None:
        print('ERROR: Sorry, you have to specify an input csv file')
        exit(1)

    print("This script will clone a list of GitHub repos form file: %s" % args.file_csv)

    data = []
    file_name = open(args.file_csv, 'r')
    file_reader = csv.reader(file_name, delimiter=',')
    count = 1
    for row in file_reader:
        repo_name = row[1].replace('/','--') + "--"  + row[0]
        url = row[5]
        data.append([repo_name, url])

    # Now we clone all the repos in github_repos list
    for item in data:
        if os.path.isdir(item[0]):
            print("\t Repo already cloned, skipping....")
        else:
            os.system('makdir {}'.format(item[0]))
            cmd = "wget --directory-prefix=%s \"%s\"" % (item[0], item[1])
            os.system(cmd)
