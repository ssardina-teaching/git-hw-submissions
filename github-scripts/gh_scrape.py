## Scrapper using https://pygithub.readthedocs.io/en/latest/apis.html

from github import Github   # package pip3 install pygithub --user
import csv
import argparse

# from datetime import datetime, tzinfo
import datetime
import pytz

TIMEZONE = 'Australia/Melbourne'
queries = [{'type': 'repo', 'search': 'pacman berkeley'}, {'type': 'filename', 'search': 'searchAgents.py'}]
queries = [{'type': 'filename', 'search': 'searchAgents.py'}]

# queries = ['pacman berkeley']

search_repo_header = ["REPO_ID", "name", "login", "email"]
search_code_header = ["REPO_ID", "name", "login", "email", "filename", "url"]

repos = []

# Searches for repositories given a string query
def search_for_repo(g, query, writer_repo):
    global repos

    results = g.search_repositories(query)
    print('========> Searched for "%s" and found %d repos' % (query, results.totalCount))

    # for page in results.get_page(0):  # but how do I know how many pages are out there?
    count = 1
    for page in results:
        repo = g.get_repo(page.full_name)

        full_name = repo.full_name
        if full_name in repos:
            print("Repo %s already scrapped before...." % full_name)
            continue

        name = repo.name
        owner = repo.owner
        login = owner.login
        email = owner.email

        print("Repo no. %d: %s, %s, %s, %s" % (count, full_name, name, login, email))
        repos.append(full_name)
        writer_repo.writerow([full_name, name, login, email])
        count += 1



# Searches for repositories with specific files
def search_for_filename(g, file_name, writer, rate_limit_remains, start_no):
    global repos

    results = g.search_code('filename:'+ file_name)
    rate_limit_remains -= 1
    print('========> Searched for filename "%s" and found %d repos' % (file_name, results.totalCount))
    count = start_no
    for page in results[start_no:]:  # page is of github.ContentFile.ContentFile
        repo = page.repository

        full_name = repo.full_name
        name = repo.full_name
        owner = repo.owner
        login = owner.login
        email = owner.email

        html_url = page.html_url

        print("Repo no. %d: %s, %s, %s, %s, %s" % (count, full_name, name, login, email, html_url))

        repos.append(full_name)
        writer.writerow([full_name, name, login, email, file_name, html_url])
        count += 1
        rate_limit_remains -= 1
        if rate_limit_remains < 5:
            return False
    return True



def get_github_rate_limits(g, timezone = TIMEZONE):
    rate_limit = g.rate_limiting[1]
    rate_limit_remains = g.rate_limiting[0]
    tz = pytz.timezone(timezone)
    date_reset = datetime.datetime.fromtimestamp(g.rate_limiting_resettime, tz)

    return rate_limit, rate_limit_remains, date_reset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This script will scrape github repos.'
    )
    parser.add_argument(
        '--filename',
        help='file to search in github'
    )
    parser.add_argument(
        '--start-no',
        help='found number to start scrapping (default: %(default)s)',
        default = 0
    )
    parser.add_argument(
        '--check-limit',
        help='report current limit on github (default: %(default)s)',
        action = 'store_true'
    )
    args = parser.parse_args()

    if args.filename is None:
        print('ERROR: You must provide a file to search for...')
        exit(1)
    filename = args.filename

    start_no = int(args.start_no)

    print("We will search for file %s" % filename)

    # using username and password
    # g = Github("ssardina@gmail.com", "se22pa30na16")

    # or using an access token
    g = Github("268de4e6bf5d4ba8241591643a58de2b7512fded")

    # for repo in g.get_user().get_repos():
    #     print(repo.name)
    #     # repo.edit(has_wiki=False)


    # rate_limit = g.rate_limiting[1]
    # rate_limit_remains = g.rate_limiting[0]
    # tz = pytz.timezone(TIMEZONE)
    # date_reset = datetime.datetime.fromtimestamp(g.rate_limiting_resettime, tz)

    rate_limit, rate_limit_remains, date_reset = get_github_rate_limits(g)


    if rate_limit_remains < 20:
        print("[ERROR] TOO RATE LITTLE LIMIT: The remaining rate limit is %d, with reset time %s" % (
            rate_limit_remains, date_reset.strftime('%Y-%m-%d %H:%M:%S %Z%z')))
        exit(1)
    else:
        print("The remaining rate limit is (total: %d, left: %d), with reset time %s" % (
            rate_limit, rate_limit_remains, date_reset.strftime('%Y-%m-%d %H:%M:%S %Z%z')))

    # all done folks!
    if args.check_limit:
        exit(0)

    # filename_code = "db_github_code_%s.csv" % datetime.date.today().strftime("%Y%m%d-%H:%M:%S")
    filename_code = "db_github_code_%s.csv" % datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
    print("Output CSV file for code searches: {}".format(filename_code))
    file_csv_code = open(filename_code, 'w')
    writer_code = csv.writer(file_csv_code, 10, delimiter=',')
    writer_code.writerow(search_code_header)

    result = search_for_filename(g, filename, writer_code, rate_limit_remains, start_no)

    rate_limit, rate_limit_remains, date_reset = get_github_rate_limits(g, TIMEZONE)
    print("FINISHED - The remaining rate limit is %d, with reset time %s" % (
        rate_limit_remains, date_reset.strftime('%Y-%m-%d %H:%M:%S %Z%z')))

    exit(0)



    filename_repo = "db_github_repos_%s.csv" % datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
    print("Output CSV file for repo searches: {}".format(filename_repo))
    file_csv_repo = open(filename_repo, 'w')
    writer_repo = csv.writer(file_csv_repo, 10, delimiter=',')
    writer_repo.writerow(search_repo_header)

    # filename_code = "db_github_code_%s.csv" % datetime.date.today().strftime("%Y%m%d-%H:%M:%S")
    filename_code = "db_github_code_%s.csv" % datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
    print("Output CSV file for code searches: {}".format(filename_code))
    file_csv_code = open(filename_code, 'w')
    writer_code = csv.writer(file_csv_code, 10, delimiter=',')
    writer_code.writerow(search_code_header)

    for query in queries:
        if query['type'] == 'filename':
            search_for_filename(g, query['search'], writer_code)
        else:
            search_for_repo(g, query['search'], writer_repo)

