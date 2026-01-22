#!/usr/bin/env python3
"""
Unpack and merge rotated log files.

This script unpacks gzipped log files and merges numbered log file rotations
(e.g., app.log.1, app.log.2) into a single consolidated log file. Files are
merged in reverse rotation order (oldest first) to maintain chronological order.
"""
import subprocess
import os
import re
from collections import defaultdict


def unpack_gz_files():
    if any(f for f in os.listdir('.') if f.endswith('.gz')):
        print('/usr/bin/unp *.gz')
        subprocess.check_output('/usr/bin/unp *.gz', shell=True)
        print('rm *.gz')
        subprocess.check_output('rm *.gz', shell=True)


def merge_similar_files():
    # Group all files by original filename
    groups = defaultdict(list)
    for filename in os.listdir('.'):
        if matches := re.findall(r'(.+?)(\.\d+)*$', filename):
            shortname = matches[0][0]
            groups[shortname].append(filename)
    # Sort grouped filenames by their number (reversed)
    for shortname, filenames in groups.items():
        filenames = sorted(filenames, key=_filename_key, reverse=True)
        if len(filenames) > 2:
            # Merge the sorted filename groupings
            cmd = f'cat {" ".join(list(filenames))} >> tmp.log'
            print(cmd)
            subprocess.check_output(cmd, shell=True)
            for filename in filenames:
                subprocess.check_output(f'rm {filename}', shell=True)
            subprocess.check_output(f'mv tmp.log {shortname}', shell=True)


def _filename_key(filename):
    num = re.findall(r'.+?\.(\d+)$', filename)
    return int(num[0]) if num else 0


if __name__ == '__main__':
    unpack_gz_files()
    merge_similar_files()
