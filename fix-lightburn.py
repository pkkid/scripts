#!/usr/bin/env python3
"""
Fix LightBurn not detecting xTool D1 Laser in Ubuntu.

This script resolves issues where the laser appears in lsusb but no ttyUSB0
device is created. It adds necessary user permissions and comments out
conflicting udev rules that prevent the device from being recognized.

Usage:
  sudo ./fix-lightburn.py

References:
  https://forum.lightburnsoftware.com/t/xtool-d1-not-recognized-in-ubuntu-22-04/62369/2
  https://support.xtool.com/hc/en-us/articles/4414120232983-User-Manual-for-xTool-D1-LightBurn-Software
"""
import subprocess
import os

XTOOL_DEVICE_ID = '1a86.7523'
UDEV_RULES_DIRPATH = '/usr/lib/udev/rules.d'


def add_user_permissions():
    """ Add user permissions so we can access tty devices. """
    print('Adding dialout and tty permissions to $USER.')
    subprocess.check_output(r'adduser $USER dialout && sudo adduser $USER tty', shell=True)


def find_files_containing(dirpath, search):
    """ Return a list of files in dirpath containing the specified text. """
    print(f'Searching {UDEV_RULES_DIRPATH} for files matching device {search}.')
    filepaths = set()
    try:
        output = subprocess.check_output(f'/usr/bin/grep -riIn "{search}" {dirpath}/*', shell=True)
        for line in output.decode().split('\n'):
            filepath = line.split(':')[0]
            if os.path.isfile(filepath):
                filepaths.add(filepath)
    except subprocess.CalledProcessError:
        print(f'No results for {search} in {dirpath}.')
    return filepaths


def comment_lines_containing(filepath, search, comment='#'):
    """ Comment out lines containing the specified text. """
    print(f'Commenting out lines matching {search} in {filepath}')
    with open(filepath) as infile:
        lines = list(infile)
    with open(filepath, 'w') as outfile:
        for lineno, line in enumerate(lines):
            if line_matches(line, search) and not line.startswith(comment):
                print(f'Commenting out udev rules matching device {search}.')
                print(f'{lineno}: {comment} {line}')
                outfile.write(f'{comment} {line}')
            else:
                outfile.write(line)


def line_matches(line, search):
    """ Return True if this line contains the search device. """
    if search in line:
        return True
    if search.replace('.', '/') in line:
        return True
    if search.replace('.', ':') in line:
        return True
    return False


if __name__ == '__main__':
    add_user_permissions()
    filepaths = find_files_containing(UDEV_RULES_DIRPATH, XTOOL_DEVICE_ID)
    for filepath in filepaths:
        comment_lines_containing(filepath, XTOOL_DEVICE_ID)
