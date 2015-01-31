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

try:
    import requests
except ImportError:
    print('Requests (http://python-requests.org/) seems to be missing.',
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


def _get_gists(user_name):
    gh = github.Github()
    user = gh.get_user(user_name)
    paginated = user.get_gists()

    gists = []
    page = 0
    while True:
        gists_current_page = paginated.get_page(page)
        if not gists_current_page:
            break
        gists += gists_current_page
        page += 1

    return gists


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
    target_directory = os.path.join(target_directory_base, 'repositories', repo.full_name)
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


def _sanitize_path_component(text):
    text = text.replace('/', '-')
    while text.startswith('.'):
        text = text[1:]

    if not text:
        raise ValueError('Path compoment cannot be empty')

    return text


def _process_gist(gist, target_directory_base, github_user_name, messenger, index, count):
    len_gist_files = len(gist.files)
    if len_gist_files != 1:
        messenger.warn('Gist "%s" contains %d files, expected a single one' % \
            (gist.id, len_gist_files))

    if not len_gist_files:
        return

    gist_file = sorted(gist.files.items())[0][1]  # First only
    messenger.info('[%*d/%s] Processing gist "%s" (ID %s, %s)...' % \
            (len(str(count)), index + 1, count,
            gist_file.filename, gist.id, gist_file.language))

    target_filename = os.path.join(target_directory_base, 'gists',
            _sanitize_path_component(github_user_name),
            _sanitize_path_component(gist.id),
            _sanitize_path_component(gist_file.filename))
    _create_parent_directories(target_filename, messenger)

    f = open(target_filename, 'w')
    r = requests.get(gist_file.raw_url)
    f.write(r.text)
    f.close()


def main():
    parser = argparse.ArgumentParser(prog='backup-my-hub')
    parser.add_argument('github_user_name', metavar='USER',
            help='GitHub user name')
    parser.add_argument('target_directory_base', metavar='DIRECTORY',
            help='Local directory to sync repositories and gists to')
    parser.add_argument('--verbose', default=False, action='store_true',
            help='Increase verbosity')
    options = parser.parse_args()

    messenger = Messenger(options.verbose)
    repos = _get_repositories(options.github_user_name, messenger)
    len_repos = len(repos)
    for i, repo in enumerate(repos):
        _process_repository(repo, options.target_directory_base,
                messenger, options.verbose, i, len_repos)

    gists = _get_gists(options.github_user_name)
    len_gists = len(gists)
    for i, gist in enumerate(gists):
        _process_gist(gist, options.target_directory_base,
                options.github_user_name,
                messenger, i, len_gists)


if __name__ == '__main__':
    main()
