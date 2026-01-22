#! /usr/bin/env python
"""
Recursively remove empty directories from a given path.

This script walks through a directory tree and removes all empty folders.
It can be used as a standalone script or imported as a module into other
scripts. By default, it will also remove the root directory if it becomes
empty after cleaning subdirectories.

Examples:
  ./remove-empty-dirs.py /path/to/clean
  ./remove-empty-dirs.py /path/to/clean False

Arguments:
  directory    Path to the directory to clean (required)
  removeRoot   Set to "False" to keep root directory even if empty (optional)

The script will:
  1. Recursively traverse the directory tree from bottom to top
  2. Identify directories that contain no files or subdirectories
  3. Remove empty directories (printing each removal)
  4. Optionally remove the root directory if it becomes empty
"""
import os, sys


def removeEmptyDirs(path, removeRoot=True):
    """ Function to remove empty folders. """
    if not os.path.isdir(path):
        return
    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                removeEmptyDirs(fullpath)
    # if dir empty, delete it
    files = os.listdir(path)
    if len(files) == 0 and removeRoot:
        try:
            print('Removing empty dir: %s' % path)
            os.rmdir(path)
        except Exception:
            pass
    

def usageString():
    """ Return usage string to be output in error cases. """
    return 'Usage: %s directory [removeRoot]' % sys.argv[0]


if __name__ == '__main__':
    removeRoot = True
    if len(sys.argv) < 1:
        print('Not enough arguments')
        sys.exit(usageString())
    if not os.path.isdir(sys.argv[1]):
        print('No such directory %s' % sys.argv[1])
        sys.exit(usageString())
    if len(sys.argv) == 2 and sys.argv[2] != "False":
        print('removeRoot must be "False" or not set')
        sys.exit(usageString())
    else:
        removeRoot = False
    removeEmptyDirs(sys.argv[1], removeRoot)
