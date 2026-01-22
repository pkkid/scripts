#!/bin/bash
# Mount Nasuni Kin share with CIFS
#
# This script mounts the Nasuni Kin network share (//kin.nasuni.net/groupsad)
# to the local /media/Kin directory using CIFS protocol. The mount uses the
# current user's UID for file ownership.
#
# Usage:
#  ./nasuni-mount-kin.sh <username>
#
# Requirements:
#  - cifs-utils package installed
#  - /media/Kin directory must exist
#  - Root privileges (uses pkexec)
#
# Mount Options:
#  - iocharset=utf8: UTF-8 character encoding
#  - file_mode=0777: Files are readable/writable by all
#  - dir_mode=0755: Directories are readable by all, writable by owner
#  - uid: Set to current user's UID for ownership

if [ -z "$1" ]; then
    echo "Usage: $0 <username>"
    echo "Example: $0 mikes"
    exit 1
fi

USERNAME="$1"
CURRENT_UID=$(id -u)
pkexec mount -t cifs //kin.nasuni.net/groupsad /media/Kin -o username=$USERNAME,iocharset=utf8,file_mode=0777,dir_mode=0755,uid=$CURRENT_UID
