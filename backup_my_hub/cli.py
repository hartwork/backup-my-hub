# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

import argparse
import errno
import os
import subprocess
import sys

try:
    import github
except ImportError:
    print('PyGithub (https://github.com/jacquev6/PyGithub) seems to be '
          'missing.', file=sys.stderr)
    sys.exit(1)

from .config import Config
from .version import VERSION_STR

requests = None  # Module imported later


_DEFAULT_CONFIG_PATH = '~/.config/backup-my-hub/main.cfg'


def _import_requests_module():
    global requests
    try:
        import requests as _requests_module
    except ImportError:
        print('Requests (http://python-requests.org/) seems to be missing.',
              file=sys.stderr)
        sys.exit(1)
    requests = _requests_module


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


def _get_repository(global_name, api_token, messenger):
    gh = github.Github(login_or_token=api_token)
    return gh.get_repo(global_name)


def _get_repositories(user_name, api_token, messenger):
    gh = github.Github(login_or_token=api_token)
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
        messenger.warn('%d repositories announced, but %d repositories '
                       'retrieved' % (paginated.totalCount, len_repos))

    return repos


def _get_gists(user_name, api_token):
    gh = github.Github(login_or_token=api_token)
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


def _run_command(command, cwd, messenger, verbose):
    messenger.command(command, cwd=cwd)
    if verbose:
        stdout = None
    else:
        stdout = open('/dev/null', 'w')

    subprocess.check_call(command, cwd=cwd, stdout=stdout)

    if not verbose:
        stdout.close()


def _process_repository(repo, target_directory_base, messenger, verbose, index,
                        count):
    messenger.info('[%*d/%s] Processing repository "%s"...' %
                   (len(str(count)), index + 1, count, repo.full_name))
    target_directory = os.path.join(target_directory_base, 'repositories',
                                    repo.full_name)
    if os.path.exists(target_directory):
        command = ['git', 'remote', 'update', '--prune']
        cwd = target_directory
    else:
        _create_parent_directories(target_directory, messenger)
        command = ['git', 'clone',
                   '--mirror',
                   repo.clone_url,
                   target_directory]
        cwd = None

    _run_command(command, cwd, messenger, verbose)


def _sanitize_path_component(text):
    text = text.replace('/', '-')
    while text.startswith('.'):
        text = text[1:]

    if not text:
        raise ValueError('Path compoment cannot be empty')

    return text


def _process_gist(gist, target_directory_base, github_user_name, messenger,
                  index, count):
    len_gist_files = len(gist.files)
    if len_gist_files != 1:
        messenger.warn('Gist "%s" contains %d files, expected a single one' %
                       (gist.id, len_gist_files))

    if not len_gist_files:
        return

    gist_file = sorted(gist.files.items())[0][1]  # First only
    messenger.info('[%*d/%s] Processing gist "%s" (ID %s, %s)...' %
                   (len(str(count)), index + 1, count,
                    gist_file.filename, gist.id, gist_file.language))

    target_filename = os.path.join(target_directory_base, 'gists',
                                   _sanitize_path_component(github_user_name),
                                   _sanitize_path_component(gist.id),
                                   _sanitize_path_component(gist_file.filename)
                                   )
    _create_parent_directories(target_filename, messenger)

    f = open(target_filename, 'w')
    r = requests.get(gist_file.raw_url)
    f.write(r.text)
    f.close()


def main():
    parser = argparse.ArgumentParser(prog='backup-my-hub')
    parser.add_argument('--config', dest='config_file', metavar='FILE',
                        help='Configuration file to use (default: %s, if '
                             'existing)' % _DEFAULT_CONFIG_PATH)
    parser.add_argument('--user', dest='github_user_name', metavar='USER',
                        help='GitHub user name; if given, configured users '
                             'and repositories are ignored')

    parser.add_argument('target_directory_base', metavar='DIRECTORY',
                        help='Local directory to sync repositories and gists '
                             'to')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Increase verbosity')
    parser.add_argument('--api-token', metavar='TOKEN',
                        help='Authenticate to the API server (e.g. to push '
                             'rate limits)')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION_STR)
    options = parser.parse_args()

    # Late import to reduce noticable --help latency (issue #4)
    _import_requests_module()

    messenger = Messenger(options.verbose)

    if options.github_user_name:
        whole_users = [options.github_user_name]
        additional_repositories = []
    else:
        config = Config()
        if options.config_file:
            config.load(options.config_file, messenger)
        else:
            config.load(os.path.expanduser(_DEFAULT_CONFIG_PATH), messenger)

        whole_users = sorted(config.get_whole_users())
        additional_repositories = sorted(config.get_additional_repositories())

    repos = []
    gists = []
    for user_name in whole_users:
        repos.extend(_get_repositories(user_name, options.api_token,
                                       messenger))
        gists.extend(_get_gists(user_name, options.api_token))

    for global_name in additional_repositories:
        repos.append(_get_repository(global_name, options.api_token,
                                     messenger))

    len_repos = len(repos)
    len_gists = len(gists)

    len_combined = len_repos + len_gists

    for i, repo in enumerate(sorted(repos, key=lambda r: r.full_name.lower())):
        _process_repository(repo, options.target_directory_base, messenger,
                            options.verbose, i, len_combined)

    for i, gist in enumerate(gists):
        _process_gist(gist, options.target_directory_base, gist.owner.login,
                      messenger, len_repos + i, len_combined)
