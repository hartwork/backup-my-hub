# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

from __future__ import print_function

import argparse
import errno
import os
import subprocess
import sys

try:
    import github
except ImportError:
    print('PyGithub (https://github.com/jacquev6/PyGithub) seems to be missing.',
            file=sys.stderr)
    sys.exit(1)


class Messenger(object):
    def __init__(self, verbose):
        self._verbose = verbose

    def info(self, *args, **kwargs):
        print(*args, **kwargs)

    def command(self, argv, **kwargs):
        if not self._verbose:
            return

        cwd = kwargs.pop('cwd', None)
        flat_argv = ' '.join(argv)
        if cwd:
            text = '# ( cd %s && %s )' % (cwd, flat_argv)
        else:
            text = '# %s' % flat_argv
        print(text, **kwargs)

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


def _create_parent_directories(path, messenger):
    path_to_create = os.path.dirname(path)
    try:
        os.makedirs(path_to_create)
    except OSError as e:
        if e.errno != errno.EEXIST:
             raise
    else:
        messenger.command(['mkdir', path_to_create])


def _process_repository(repo, target_directory_base, messenger, verbose, index, count):
    messenger.info('[%*d/%s] Processing repository "%s"...' % \
            (len(str(count)), index + 1, count, repo.full_name))
    target_directory = os.path.join(target_directory_base, repo.full_name)
    if os.path.exists(target_directory):
        command = ['git', 'remote', 'update']
        cwd = target_directory
    else:
        _create_parent_directories(target_directory, messenger)
        command = ['git', 'clone',
                '--mirror',
                repo.clone_url,
                target_directory]
        cwd = None

    messenger.command(command, cwd=cwd)
    if verbose:
        git_stdout = None
    else:
        git_stdout = open('/dev/null', 'w')

    subprocess.check_call(command, cwd=cwd, stdout=git_stdout)

    if not verbose:
        git_stdout.close()


def main():
    parser = argparse.ArgumentParser(prog='backup-my-hub')
    parser.add_argument('github_user_name', metavar='USER',
            help='GitHub user name')
    parser.add_argument('target_directory_base', metavar='DIRECTORY',
            help='Local directory to sync repositories to')
    parser.add_argument('--verbose', default=False, action='store_true',
            help='Increase verbosity')
    options = parser.parse_args()

    messenger = Messenger(options.verbose)
    repos = _get_repositories(options.github_user_name, messenger)
    len_repos = len(repos)
    for i, repo in enumerate(repos):
        _process_repository(repo, options.target_directory_base,
                messenger, options.verbose, i, len_repos)


if __name__ == '__main__':
    main()
