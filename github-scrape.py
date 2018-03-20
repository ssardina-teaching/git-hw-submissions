## Scrapper using https://pygithub.readthedocs.io/en/latest/apis.html

from github import Github   # package pip3 install pygithub --user
import csv
import datetime

queries = [{'type': 'code', 'search': 'filename:searchAgents.py'}, {'type': 'repo', 'search': 'pacman berkeley'}]

# queries = ['pacman berkeley']

search_repo_data = [["repo_name", "login", "email"]]
search_code_data = [["repo_name", "login", "email", "filename", "url"]]

def search_for_repo(query)



if __name__ == '__main__':
    # using username and password
    # g = Github("ssardina@gmail.com", "se22pa30na16")

    # or using an access token
    g = Github("268de4e6bf5d4ba8241591643a58de2b7512fded")

    # for repo in g.get_user().get_repos():
    #     print(repo.name)
    #     # repo.edit(has_wiki=False)

    filename = "db_github_repos_%s.csv" % datetime.date.today().strftime("%Y%m%d")
    print("Output file: {}".format(filename))
    myFile = open(filename, 'w')
    with myFile:
        writer = csv.writer(myFile, 10, delimiter=',')

        for query in queries:
            if query['type'] == 'code':
                print("skipping code query: \"%s\"" % query['search'])
                results = g.search_code(query['search'])
                for page in results:    # page is of github.ContentFile.ContentFile https://pygithub.readthedocs.io/en/latest/github_objects/ContentFile.html#github.ContentFile.ContentFile
                    # repo = g.get_repo(page.full_name)
                    print(page.html_url)
                continue
            else:
                results = g.search_repositories(query['search'])
                exit(1)

            print('========> Searched for "%s" and found %d repos' % (query, results.totalCount))
            exit(1)
            # for page in results.get_page(0):  # but how do I know how many pages are out there?
            count = 1
            for page in results:
                repo = g.get_repo(page.full_name)

                full_name = repo.full_name
                if full_name in [x[0] for x in search_repo_data]:
                    print("Repo %s already scrapped before...." % full_name)
                    continue

                owner = repo.owner
                login = owner.login
                email = owner.email

                print("Repo no. %d: %s, %s, %s" % (count, full_name, login, email))
                # print("%s, %s" % (repo.name, repo.user))
                search_repo_data.append([full_name, login, email])
                writer.writerow([full_name, login, email])
                count = count + 1

    # Now write data collected in console
    print(search_repo_data)

