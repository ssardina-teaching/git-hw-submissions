from github import Github, EmptyRepositoryException
import datetime
import time
import argparse

def main(username, password, organization):
    g = Github(username, password, timeout=1)
    org = g.get_organization(organization)

    file_set = set()
    language_set = set()
    total_commits = 0
    total_additions = 0
    total_deletions = 0
    total_repositories = 0
    for repo in org.get_repos():
        print repo.name
        has_commits = False
        try:
            for commit in repo.get_commits(author=username):
                has_commits = True
                total_commits +=1
                total_additions +=commit.stats.additions
                total_deletions +=commit.stats.deletions
                file_set.update([fil.filename for fil in commit.files])
            if has_commits:
                total_repositories +=1
                language_set.update(repo.get_languages().keys())

        except EmptyRepositoryException:
            pass

    print "Since May 20, @wcdolpin has made %s commits in %s different languages, "\
        "editing %s different files in %s different repositories. Overall,"\
        " there were a total of %s additions and %s deletions" % (total_commits,
          len(language_set), len(file_set), total_repositories, total_additions,
          total_deletions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count contributions in an org.')
    parser.add_argument('username', metavar='USERNAME', type=str,
                help='your Github username')
    parser.add_argument('password', metavar='PASSWORD', type=str,
                help='your Github password')
    parser.add_argument('organization', metavar='ORGANIZATION', type=str,
            help='The organization to analyze')
    args = parser.parse_args()
    main(args.username, args.password, args.organization)