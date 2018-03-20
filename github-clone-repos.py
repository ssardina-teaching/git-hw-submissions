#!/usr/bin/env python

import os


if __name__ == "__main__":
	print("This script will clone a list of GitHub repos...")
	
	repo_file = open('repos.txt', 'r')
	list_of_repos_id = repo_file.readlines()
	#print(list_of_repos_id)
	
	github_repos = [(x.split('/')[0],'git@github.com:'+x.rstrip()) for x in list_of_repos_id]
	#print(github_repos)	

	for repo in github_repos:
		print("\nCloning repo: " + repo[0])
		if os.path.isdir(repo[0]):
			print("\t Repo already cloned, skipping....")
		else:
			cmd = "git clone "+ repo[1] + " " + repo[0]
			print(cmd)
			os.system(cmd)
		
