#!/usr/bin/python3
"""
Simulate ransomware file encryption by renaming files with a custom extension.

This script renames files by appending a custom extension (like .hamster) to
simulate what ransomware does when it "encrypts" files. It can also undo the
operation by removing the extension. Useful for testing backup systems,
anti-ransomware solutions, and file recovery procedures.

Examples:
  ./ransomware-test.py /tmp/test
  ./ransomware-test.py /tmp/test --dangerous-rename-files --ext .locked --recursive
  ./ransomware-test.py /tmp/test --dangerous-rename-files --maxcount 100
  ./ransomware-test.py /tmp/test --dangerous-rename-files --undo

Options:
  path                          Directory path to process (required)
  -x, --ext <ext>               Extension to append (default: .hamster)
  -r, --recursive               Recursively process subdirectories
  -m, --maxcount <n>            Maximum number of files to rename (default: 999999)
  --dangerous-rename-files      Actually rename files (default is dry-run mode)
  -u, --undo                    Reverse the operation by removing the extension

The script will:
  1. Scan the specified directory for files
  2. Append the extension to each file (or remove if --undo)
  3. Skip files that already have/don't have the extension
  4. Prompt for confirmation before making actual changes
  5. Stop after reaching maxcount files

NOTE: This script defaults to dry-run mode.
Use --dangerous-rename-files to actually rename files!
"""
import os
import argparse


def walkdir(path, ext, recursive=False, maxcount=999999, undo=False, dryrun=False, count=0):
    """ Rename all files in the specified path. """
    if os.path.isfile(path):
        rename_file(path, ext, undo, dryrun)
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if os.path.isfile(filepath):
            count += rename_file(filepath, ext, count, undo, dryrun)
            if count >= maxcount:
                break
    if recursive:
        for filename in os.listdir(path):
            dirpath = os.path.join(path, filename)
            if os.path.isdir(dirpath):
                count = walkdir(dirpath, ext, recursive, maxcount, undo, dryrun, count)
                if count >= maxcount:
                    break
    return count


def rename_file(source, ext, count, undo=False, dryrun=False):
    """ Rename the specified file. """
    if undo:
        if ext not in source: return 0
        dest = source.replace(ext, '')
    else:
        if ext in source: return 0
        dest = f'{source}{ext}'
    print(f'{count}: Renaming {source} -> {dest}')
    if not dryrun:
        os.rename(source, dest)
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rename all files in the specified path.')
    parser.add_argument('path', help='Path of directory to start in')
    parser.add_argument('-x', '--ext', default='.hamster', help='Extension to include in rename')
    parser.add_argument('-r', '--recursive', default=False, action='store_true', help='Recursivly walk the tree')
    parser.add_argument('-m', '--maxcount', type=int, default=999999, help='Max number of files to rename')
    parser.add_argument('--dangerous-rename-files', default=False, action='store_true', help='Actually rename files (disables dry-run mode)')  # noqa
    parser.add_argument('-u', '--undo', default=False, action='store_true', help='Undo the rename')
    opts = parser.parse_args()
    dryrun = not opts.dangerous_rename_files
    if not dryrun:
        answer = input('\nThis is NOT a dry run, are you sure you wish to continue? [yes/No]: ')
        if answer.lower() != 'yes':
            raise SystemExit('Exiting.')
    try:
        walkdir(opts.path, opts.ext, opts.recursive, opts.maxcount, opts.undo, dryrun)
    except KeyboardInterrupt:
        print('Keyboard Interrupt: Exiting.')
