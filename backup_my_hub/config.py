# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

import os
from configparser import RawConfigParser


class Config(object):
    def __init__(self):
        self._whole_users = set()
        self._additional_repositories = set()

    @staticmethod
    def _raise_malformed_section_name(section):
        raise ValueError('Malformed section name "%s"' % section)

    def load(self, filename, messenger):
        if not os.path.exists(filename):
            raise IOError('File "%s" does not exist' % filename)
        parser = RawConfigParser()
        parser.read([filename])

        sections = parser.sections()
        if not sections:
            raise ValueError('No sections found')

        for section in sections:
            if section.startswith('repository '):
                repository = section[len('repository '):].strip()
                if not repository or repository.count('/') != 1:
                    self._raise_malformed_section_name(section)
                self._additional_repositories.add(repository)
            elif section.startswith('user '):
                user = section[len('user '):].strip()
                if not user:
                    self._raise_malformed_section_name(section)
                self._whole_users.add(user)
            else:
                self._raise_malformed_section_name(section)

        for global_name in list(self._additional_repositories):
            user, local_name = global_name.split('/')
            if user in self._whole_users:
                messenger.info('Request for repository "%s" covered by '
                               'request for user "%s", already.' %
                               (global_name, user))
                self._additional_repositories.remove(global_name)

    def get_whole_users(self):
        return iter(self._whole_users)

    def get_additional_repositories(self):
        return iter(self._additional_repositories)
