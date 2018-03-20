from github import Github   # package pip3 install pygithub --user
import csv


csvData = [["repo_name", "login", "email"]]

# using username and password
# g = Github("ssardina@gmail.com", "se22pa30na16")

# or using an access token
g = Github("268de4e6bf5d4ba8241591643a58de2b7512fded")

# for repo in g.get_user().get_repos():
#     print(repo.name)
#     # repo.edit(has_wiki=False)

myFile = open('github-repos.csv', 'w')
with myFile:
    writer = csv.writer(myFile, delimiter=',')

    query = 'pacman berkeley'
    results = g.search_repositories(query)
    # print(results. .totalCount)
    # exit(1)
    # for page in results.get_page(0):  # but how do I know how many pages are out there?
    for page in results:
        repo = g.get_repo(page.full_name)

        full_name = repo.full_name
        owner = repo.owner
        login = owner.login
        email = owner.email

        print("%s, %s, %s" % (full_name, login, email))
        # print("%s, %s" % (repo.name, repo.user))
        csvData.append([full_name, login, email])
        writer.writerow([full_name, login, email])

# Now write data collected in console
print(csvData)





