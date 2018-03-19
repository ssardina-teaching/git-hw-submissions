from github import Github

# using username and password
# g = Github("ssardina@gmail.com", "se22pa30na16")

# or using an access token
g = Github("268de4e6bf5d4ba8241591643a58de2b7512fded")

# for repo in g.get_user().get_repos():
#     print(repo.name)
#     # repo.edit(has_wiki=False)

query = 'pacman berkeley'
results = g.search_repositories(query)
for page in results.get_page(1):
    repo = g.get_repo(page.full_name)
    print("%s, %s" % (repo.full_name, repo.owner))
	# print("%s, %s" % (repo.name, repo.user))






