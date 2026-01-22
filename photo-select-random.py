#!/usr/bin/python3
"""
Randomly select and copy photos from starred photo collection.

This script selects a random subset of photos from a starred photo collection
organized by date. Photos are copied to a destination directory with sequential
naming (photo-0000.jpg, photo-0001.jpg, etc.).

Examples:
  ./photo-select-random.py --source /path/to/source --dest /path/to/dest --num 50
  ./photo-select-random.py -s /media/photos -d ~/output --num 100 --mindate 2023-01-01
  ./photo-select-random.py -s /photos -d /output -n 200 -m 2024-06-01 --ignore "Past Life,Vacation"

The script will:
  1. Scan source directory for albums organized by date (YYYY-MM-DD format)
  2. Filter albums by minimum date if specified
  3. Collect all JPEG photos from matching albums
  4. Randomly shuffle the photo list
  5. Copy the requested number of photos with sequential naming
"""
import logging
import argparse, os, sys
import random, re, shutil

# Logging configuration
log = logging.getLogger()
logformat = logging.Formatter('%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s')
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(logformat)
log.addHandler(streamhandler)
log.setLevel(logging.INFO)

REGEX_DATE = r'^\d{4}-\d{2}-\d{2}'


class SelectPhotos:

    def __init__(self, opts, source_dir, dest_dir, ignores):
        self.opts = opts
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.ignores = ignores

    def run(self):
        photos = self.get_manifest(self.source_dir)
        random.shuffle(photos)
        self.copy_photos(photos[0:int(self.opts.num)])

    def get_manifest(self, dirpath):
        photos = []
        for item in sorted(os.listdir(dirpath)):
            subdirpath = os.path.join(dirpath, item)
            if os.path.isdir(subdirpath) and item not in self.ignores:
                matches = re.findall(REGEX_DATE, item)
                datestr = matches[0] if matches else None
                if datestr and (not self.opts.mindate or datestr >= self.opts.mindate):
                    for item in sorted(os.listdir(subdirpath)):
                        photopath = os.path.join(subdirpath, item)
                        extension = photopath[-4:].lower()
                        if extension == '.jpg' and os.path.isfile(photopath):
                            photos.append(photopath)
        return photos

    def copy_photos(self, photos):
        os.makedirs(self.dest_dir, exist_ok=True)
        for i in range(len(photos)):
            newphotopath = os.path.join(self.dest_dir, 'photo-%s.jpg' % str(i).zfill(4))
            shutil.copyfile(photos[i], newphotopath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='resize and copy starred photos')
    parser.add_argument('-s', '--source', required=True, help='source directory')
    parser.add_argument('-d', '--dest', required=True, help='destination directory')
    parser.add_argument('-n', '--num', default=100, help='num photos to select')
    parser.add_argument('-m', '--mindate', default=None, help='min date to include')
    parser.add_argument('-i', '--ignore', default='', help='comma-separated list of directories to ignore')
    opts = parser.parse_args()
    ignores = [x.strip() for x in opts.ignore.split(',') if x.strip()]
    SelectPhotos(opts, opts.source, opts.dest, ignores).run()
