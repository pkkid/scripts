#!/usr/bin/env python3
"""
Refresh Sublime Text project files by scanning for git repositories.

This script automatically discovers git repositories in specified directories
and creates/updates Sublime Text project files. It also removes project files
for repositories that no longer exist.

Usage:
  ./sublime-refresh-projects.py

The script will:
  1. Scan root directories for git repositories (.git/config files)
  2. Read existing Sublime Text project files
  3. Create new project files for newly discovered repositories
  4. Remove project files for repositories that no longer exist

Configuration:
  Projects directory: ~/.config/sublime-text/Packages/User/Projects
  Scanned directories: ~/Nasuni, ~/Projects, ~/Sources

Each project file contains a simple folder reference to the git repository,
allowing Sublime Text to open the project with all repository files accessible.
"""
import json
import os
import re
import subprocess

DEFAULT_SUBLIME_PROJECT_DIR = os.path.expanduser('~/.config/sublime-text/Packages/User/Projects')
DEFAULT_ROOT_DIRS = [
    os.path.expanduser('~/Nasuni'),
    os.path.expanduser('~/Projects'),
    os.path.expanduser('~/Sources'),
]


def json_read(filepath):
    """ Read the json file after cleaning trailing commas. """
    with open(filepath) as handle:
        jsonstr = handle.read()
    jsonstr = re.sub(r',[ \t\r\n]+}', '}', jsonstr)
    jsonstr = re.sub(r',[ \t\r\n]+\]', ']', jsonstr)
    return json.loads(jsonstr)


def find_projects(rootdirs):
    """ Find all git projects in the specified root dirs. """
    repodirs = []
    for rootdir in rootdirs:
        try:
            output = subprocess.check_output(r'/usr/bin/grep -riI "^\s*url\s\=" */.git/config', cwd=rootdir, shell=True)
            for line in output.decode().split('\n'):
                if 'url =' in line:
                    dirname = line.split('.git')[0][:-1]
                    repodir = os.path.join(rootdir, dirname)
                    print(f'Found git project {repodir}')
                    repodirs.append(repodir)
        except Exception:
            pass
    return repodirs


def get_existing_projects(projectdir):
    """ Get a list of existing Sublime-Text projects. {projectpath -> filepath} """
    existing, dead = {}, []
    if os.path.isdir(projectdir):
        for filepath in os.listdir(projectdir):
            if filepath.endswith('.sublime-project'):
                filepath = os.path.join(projectdir, filepath)
                print(f'Reading project {filepath}')
                project = json_read(filepath)
                for foldersettings in project.get('folders', []):
                    projectpath = os.path.expanduser(foldersettings.get('path'))
                    if projectpath and os.path.exists(projectpath):
                        existing[projectpath] = filepath
                    elif projectpath and not os.path.exists(projectpath):
                        dead.append(filepath)
    return existing, dead


def create_project_files(repodirs, existing, projectdir):
    """ Create the individual Sublime-Text project files. """
    os.makedirs(projectdir, exist_ok=True)
    for repodir in repodirs:
        if repodir not in existing:
            settings = {'folders':[{'path': repodir}]}
            filename = f'{os.path.basename(repodir)}.sublime-project'
            filepath = os.path.join(projectdir, filename)
            if not os.path.exists(filepath):
                print(f'Creating new project: {filepath}')
                with open(filepath, 'w') as handle:
                    json.dump(settings, handle)


def remove_dead_projects(dead):
    """ Delete dead project files. """
    for filepath in dead:
        print(f'Removing dead project: {filepath}')
        os.unlink(filepath)


if __name__ == '__main__':
    repodirs = find_projects(DEFAULT_ROOT_DIRS)
    existing, dead = get_existing_projects(DEFAULT_SUBLIME_PROJECT_DIR)
    create_project_files(repodirs, existing, DEFAULT_SUBLIME_PROJECT_DIR)
    remove_dead_projects(dead)
