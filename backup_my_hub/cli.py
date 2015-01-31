# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

from __future__ import print_function

import argparse
import sys

try:
    import github
except ImportError:
    print('PyGithub (https://github.com/jacquev6/PyGithub) seems to be missing.',
            file=sys.stderr)
    sys.exit(1)


class Messenger(object):
    def warn(self, *args, **kwargs):
        print('WARNING:', *args, file=sys.stderr, **kwargs)


def _get_repositories(user_name, messenger):
    gh = github.Github()
    paginated = gh.search_repositories('', user=user_name)

    repos = []
    page = 0
    while True:
        repos_current_page = paginated.get_page(page)
        if not repos_current_page:
            break
        repos += repos_current_page
        page += 1

    len_repos = len(repos)
    if len_repos != paginated.totalCount:
        messenger.warn('%d repositories announced, but %d repositories retrieved' % \
                 (paginated.totalCount, len_repos))

    return repos


def main():
    parser = argparse.ArgumentParser(prog='backup-my-hub')
    parser.add_argument('github_user_name', metavar='USER',
            help='GitHub user name')
    parser.add_argument('target_directory', metavar='DIRECTORY',
            help='Local directory to sync repositories to')
    options = parser.parse_args()

    messenger = Messenger()
    repos = _get_repositories(options.github_user_name, messenger)


if __name__ == '__main__':
    main()
