#!/usr/bin/env python3

# run the web application using Docker

import argparse
import os
import shutil
import sys
from shlex import split
from subprocess import run

def run_scripting_tool():
    # run the scripting tool to generate the profiles
    # this requires python3, pyyaml and requests
    # TODO: write this function
    pass

def update_profiles():
    # update the profiles in the Web-Application directory
    for dir in ['profiles', 'tables', 'draft-profiles', 'draft-tables']:
        shutil.rmtree(f'Web-Application/{dir}', ignore_errors=True)
        shutil.copytree(f'Scription-Tool/{dir}', f'Web-Application/{dir}')


def run_web_application():
    # run the web application using Docker
    cmd_str = f'docker run --rm --name BioschemasMarkupGenerator -p 8080:80 -v {os.getcwd()}/Web-Application:/usr/local/apache2/htdocs httpd'
    cmd = split(cmd_str)
    run(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the web application using Docker')
    parser.add_argument('--update_profiles', action='store_true', help='Update the profiles in the Web-Application directory')
    parser.add_argument('--regenerate_profiles', action='store_true', help='Regenerate the profiles in the Scription-Tool directory')
    args = parser.parse_args()

    if args.regenerate_profiles:
        run_scripting_tool()
        sys.exit(0)

    if args.update_profiles:
        update_profiles()
    run_web_application()
