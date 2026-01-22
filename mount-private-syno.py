#!/usr/bin/python3
"""
Mount an encrypted folder using EncFS.

This script mounts an encrypted directory (~/Sync/Private) to a decrypted
mount point (~/Private) using EncFS. The mounted filesystem will automatically
unmount after 60 minutes of inactivity.

Usage:
    ./mount-private.py

The script will:
    1. Create encrypted and decrypted directories if they don't exist
    2. Check if encfs is installed
    3. Verify the mount point is not already in use
    4. Prompt for password to decrypt the filesystem
    5. Mount with auto-unmount after 60 minutes of idle time

Requirements:
    - encfs must be installed (apt install encfs)
    - Encrypted data stored in ~/Sync/Private
    - Mount point at ~/Private

Copyright (c) 2015 M.Shepanski. All rights reserved.
"""
import getpass, os, shlex, subprocess

PATH_ENCFS = subprocess.check_output(shlex.split('which encfs')).decode().strip()
PATH_ENCRYPTED = os.path.expanduser('/media/Synology/Private')
PATH_DECRYPTED = os.path.expanduser('/media/PrivateSyno')


if __name__ == '__main__':
    os.makedirs(PATH_ENCRYPTED, exist_ok=True)
    os.makedirs(PATH_DECRYPTED, exist_ok=True)
    # System Check
    if not os.path.isfile(PATH_ENCFS):
        raise SystemExit('Please install encfs on your system.')
    if os.listdir(PATH_DECRYPTED):
        raise SystemExit('Destination already mounted: %s' % PATH_DECRYPTED)
    # Mount
    passwd = getpass.getpass('Please enter password to mount %s: ' % PATH_DECRYPTED)
    command = '%s --stdinpass --idle=60 %s %s' % (PATH_ENCFS, PATH_ENCRYPTED, PATH_DECRYPTED)
    print(command)
    proc = subprocess.Popen(shlex.split(command), stdin=subprocess.PIPE)
    proc.communicate(input=('%s\n' % passwd).encode())
