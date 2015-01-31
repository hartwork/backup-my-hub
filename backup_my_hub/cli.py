# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

import argparse


def main():
    parser = argparse.ArgumentParser(prog='backup-my-hub')
    parser.add_argument('github_user_name', metavar='USER',
            help='GitHub user name')
    parser.add_argument('target_directory', metavar='DIRECTORY',
            help='Local directory to sync repositories to')
    parser.parse_args()


if __name__ == '__main__':
    main()
