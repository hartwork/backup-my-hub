#! /usr/bin/env python2
# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

from distutils.core import setup

from backup_my_hub.version import VERSION_STR

_GITHUB_HOME_BASE = 'https://github.com/hartwork/backup-my-hub'


if __name__ == '__main__':
    setup(
            name='backup-my-hub',
            description='Command line tool to make local backups of GitHub repositories and gists',
            license='GPL v2 or later',
            version=VERSION_STR,
            author='Sebastian Pipping',
            author_email='sebastian@pipping.org',
            url=_GITHUB_HOME_BASE,
            download_url='%s/archive/%s.tar.gz' % (_GITHUB_HOME_BASE, VERSION_STR),
            packages=[
                'backup_my_hub',
            ],
            scripts=(
                'backup-my-hub',
            ),
            classifiers=[
                'Development Status :: 3 - Alpha',
                'Environment :: Console',
                'Intended Audience :: Developers',
                'Intended Audience :: End Users/Desktop',
                'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                'Natural Language :: English',
                'Operating System :: POSIX :: Linux',
                'Programming Language :: Python :: 2.7',
                'Topic :: Software Development :: Version Control',
                'Topic :: System :: Archiving :: Backup',
                'Topic :: Utilities',
            ],
            )
