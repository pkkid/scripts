#!/usr/bin/env python
"""
Organize photos and videos by date into monthly folders.

This script sorts photos and videos from an uncategorized directory into
organized monthly folders based on EXIF date information (for photos) or
file modification time (for videos). Duplicate files are detected using
MD5 hashing and removed automatically.

Examples:
  ./photo-sort-by-month.py
  ./photo-sort-by-month.py --recurse

Directory Structure:
  Source: /volume1/Synology/Photos/Uncategorized
  Destination: /volume1/Synology/Photos/ByMonth
    
  Photos organized as: YYYY-MM/YYYY-MM-DD-HHMMSS.jpg
  Videos organized as: Videos/YYYY-MM/YYYY-MM-DD-HHMMSS.mp4
  Unknown dates: Unknown/original-filename.jpg

The script will:
  1. Read EXIF data from photos or modification time from videos
  2. Generate destination path based on date (YYYY-MM format)
  3. Rename files with timestamp format (YYYY-MM-DD-HHMMSS)
  4. Detect and remove duplicate files using MD5 hashing
  5. Clean up empty directories after moving files

Requirements:
  pip install Pillow

Note: This script only runs on the Synology NAS system.
"""
import logging, datetime, socket
import argparse, os, sys
import hashlib
from PIL import Image

log = logging.getLogger()
logformat = logging.Formatter('%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s')
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(logformat)
log.addHandler(streamhandler)
log.setLevel(logging.INFO)

UNKNOWN = 'Unknown'
if socket.gethostname() != 'Synology':
    raise SystemExit('Only run this on the Synology')
SOURCEDIR = '/volume1/Synology/Photos/Uncategorized'
DESTDIR = '/volume1/Synology/Photos/ByMonth'
PHOTOS = ['.jpg','.png']
VIDEOS = ['.mov','.mp4']


class PhotoAlreadySorted(Exception):
    pass


class SortByMonth:

    def __init__(self, opts):
        self.opts = opts
        self.cwd = os.getcwd()

    def sort_photos(self, dir=None):
        dir = dir or self.cwd
        # make sure were not in the destination directory
        if dir.startswith(DESTDIR):
            return None
        # iterate all the files in this directory
        for filename in sorted(os.listdir(dir)):
            filepath = os.path.join(dir, filename)
            name, ext = os.path.splitext(os.path.basename(filepath.lower()))
            if ext in PHOTOS + VIDEOS:
                self.sort_photo(filepath, ext)
            if self.opts.recurse and os.path.isdir(filepath):
                self.sort_photos(filepath)
            if not os.listdir(dir):
                log.info('Removing empty directory: %s' % dir)
                os.rmdir(dir)

    def sort_photo(self, filepath, ext):
        try:
            photohash = self.get_filehash(filepath)
            photodate = self.get_photodate(filepath, ext)
            newfilepath = self.get_newfilepath(filepath, photohash, photodate, ext)
            self.move_photo(filepath, newfilepath)
        except PhotoAlreadySorted:
            log.warning('Deleting photo already sorted: %s (%s)' % (filepath, photohash))
            os.unlink(filepath)

    def get_photodate(self, filepath, ext):
        try:
            if ext in VIDEOS:
                return datetime.datetime.fromtimestamp(int(os.stat(filepath).st_mtime))
            exif = Image.open(filepath)._getexif()
            if 36867 in exif:
                return datetime.datetime.strptime(exif[36867], '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
        return UNKNOWN

    def get_filehash(self, filepath):
        if '../' in filepath or '..\\' in filepath:
            raise Exception('Invalid file path')
        return hashlib.md5(open(filepath, 'rb').read()).hexdigest()

    def get_newfilepath(self, filepath, photohash, photodate, ext):
        count = 0
        # Different algorythm if we dont know the date
        if photodate == UNKNOWN:
            filename = os.path.splitext(os.path.basename(filepath.lower()))[0]
            newfilepath = '%s/Unknown/%s%s' % (DESTDIR, filename, ext)
            while os.path.exists(newfilepath):
                if self.get_filehash(newfilepath) == photohash:
                    raise PhotoAlreadySorted()
                count += 1
                newfilepath = '%s/Unknown/%s-%s%s' % (DESTDIR, filename, count, ext)
            return newfilepath
        # Rename to YYYY-MM/YYYY-MM-DD-HHMMSS.jpg
        monthstr = photodate.strftime('%Y-%m')
        monthstr = 'Videos/%s' % monthstr if ext in VIDEOS else monthstr
        datetimestr = photodate.strftime('%Y-%m-%d-%H%M%S')
        newfilepath = '%s/%s/%s%s' % (DESTDIR, monthstr, datetimestr, ext)
        while os.path.exists(newfilepath):
            if self.get_filehash(newfilepath) == photohash:
                raise PhotoAlreadySorted()
            count += 1
            newfilepath = '%s/%s/%s-%s%s' % (DESTDIR, monthstr, datetimestr, count, ext)
        return newfilepath

    def move_photo(self, filepath, newfilepath):
        log.info('Moving %s -> %s' % (filepath, newfilepath))
        os.makedirs(os.path.dirname(newfilepath), exist_ok=True)
        os.rename(filepath, newfilepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='sort photos by month')
    parser.add_argument('-r', '--recurse', default=False, action='store_true', help='recurse directories.')
    opts = parser.parse_args()
    SortByMonth(opts).sort_photos(SOURCEDIR)
