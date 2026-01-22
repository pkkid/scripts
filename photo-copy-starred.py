#!/usr/bin/python3
"""
Copy and resize starred photos from Picasa albums.

This script scans Picasa photo albums for starred photos (marked in .picasa.ini
files) and copies them to a new directory with resizing. Images are resized to
a maximum dimension of 1600px while maintaining aspect ratio.

Examples:
  ./photo-copy-starred.py
  ./photo-copy-starred.py --force

Directories:
  Source: /media/Synology/Photos/Albums
  Destination: /media/Synology/Photos/Starred

The script will:
  1. Recursively scan source albums for .picasa.ini files
  2. Identify photos marked as starred
  3. Create corresponding directory structure in destination
  4. Resize images to max 1600px (longest side)
  5. Save as optimized JPEG with 95% quality

Requirements:
  pip install Pillow
"""
import logging
import argparse, os, sys
import configparser
from PIL import Image

# Logging configuration
log = logging.getLogger()
logformat = logging.Formatter('%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s')
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(logformat)
log.addHandler(streamhandler)
log.setLevel(logging.INFO)

# Contants
MAX_SIZE = 1600
SOURCE_DIR = '/media/Synology/Photos/Albums'
DEST_DIR = '/media/Synology/Photos/Starred'
IGNORES = ['Past Life']


class CopyStarred:

    def __init__(self, opts):
        self.opts = opts
        self.total_albums = 0
        self.total_photos = 0

    def run(self):
        self.walk_children(SOURCE_DIR)
        print('\nProcessed albums: %s' % self.total_albums)
        print('Processed photos: %s' % self.total_photos)

    def walk_children(self, dirpath):
        log.info('finding albums in: %s', dirpath)
        for item in sorted(os.listdir(dirpath)):
            subdirpath = os.path.join(dirpath, item)
            subinipath = os.path.join(subdirpath, '.picasa.ini')
            if os.path.isdir(subdirpath) and os.path.isfile(subinipath):
                self.process_album(subdirpath, subinipath)

    def process_album(self, dirpath, inipath):
        log.info('  found album: %s', dirpath)
        newdirpath = dirpath.replace(SOURCE_DIR, DEST_DIR)
        if not os.path.exists(newdirpath) or self.opts.force:
            starred = self.list_starred_photos(inipath)
            if starred:
                self.total_albums += 1
                os.makedirs(newdirpath, exist_ok=True)
                for photopath in starred:
                    self.total_photos += 1
                    self.process_photo(photopath)

    def process_photo(self, photopath):
        try:
            log.info('    processing photo: %s', photopath)
            image = Image.open(photopath)
            image.thumbnail((MAX_SIZE, MAX_SIZE), Image.ANTIALIAS)
            newfilepath = photopath.replace(SOURCE_DIR, DEST_DIR)
            image.save(newfilepath, 'JPEG', quality=95, optimize=True, progressive=False)
        except Exception as err:
            log.error('    ERROR processing: %s; %s', photopath, err)

    def list_starred_photos(self, inipath):
        starred = set()
        dirpath = os.path.dirname(inipath)
        config = configparser.ConfigParser()
        config.read(inipath)
        for photoname in config.sections():
            if config[photoname].get('star','').lower() == 'yes':
                photopath = os.path.join(dirpath, photoname)
                starred.add(photopath)
        return sorted(starred)

    def resize(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='resize and copy starred photos')
    parser.add_argument('-f', '--force', default=False, action='store_true', help='force copy even if dest exists.')
    opts = parser.parse_args()
    CopyStarred(opts).run()
