#!/usr/bin/python3
"""
Batch resize JPEG images to a maximum dimension.

This script resizes all JPEG images in a directory that exceed a specified
maximum dimension. Original images are backed up before resizing. The script
maintains aspect ratios and reports space savings achieved through compression.

Examples:
  ./photo-resize.py --dir /path/to/photos
  ./photo-resize.py --dir ~/Pictures --maxx 2048 --backupdir ~/Desktop/backup
  ./photo-resize.py -d ~/Photos -b ~/Backup -x 1920

Options:
  -d, --dir <path>        Directory containing images to resize (default: current directory)
  -b, --backupdir <path>  Directory to store original backups (default: ~/Desktop)
  -x, --maxx <pixels>     Maximum dimension (width or height) in pixels (default: 3456)

The script will:
  1. Scan the directory for JPEG files
  2. Identify images larger than the maximum dimension
  3. Backup original images to the backup directory
  4. Resize images maintaining aspect ratio
  5. Report space savings achieved

Requirements:
  pip install Pillow
"""
import argparse, os, shutil
from PIL import Image

CWD = os.getcwd()
DESKTOP = os.path.expanduser('~/Desktop')


class BatchResize:

    def __init__(self, **kwargs):
        self.dir = kwargs['dir']
        self.backupdir = kwargs['backupdir']
        self.maxx = kwargs['maxx']
        print(self.__dict__)

    def resize(self):
        self._checkargs()
        count = 0
        saved = 0
        for filepath, image in self._images_to_resize():
            try:
                count += 1
                origsize = os.stat(filepath).st_size
                self._backup_file(filepath)
                image.thumbnail((self.maxx, self.maxx), Image.LANCZOS)
                image.save(filepath, "JPEG")
                newsize = os.stat(filepath).st_size
                saved += origsize - newsize
                print("%s. %s: (%s to %s)" % (count, filepath, self._bytes(origsize), self._bytes(newsize)))
            except Exception:
                pass
        print("SAVED: %s" % self._bytes(saved))

    def _checkargs(self):
        if not os.path.isdir(self.dir):
            raise SystemExit("--dir must be an existing directory.")
        if not os.path.isdir(self.backupdir):
            raise SystemExit("--backupdir must be an existing directory.")

    def _images_to_resize(self):
        for filename in os.listdir(self.dir):
            try:
                filepath = os.path.join(self.dir, filename)
                if os.path.isfile(filepath) and filename.lower().endswith('.jpg'):
                    image = Image.open(filepath)
                    imgx = max(list(image.size))
                    if imgx > self.maxx:
                        yield filepath, image
            except Exception:
                pass

    def _backup_file(self, filepath):
        filename = os.path.basename(filepath)
        dirname = os.path.basename(os.path.dirname(filepath))
        backupdir = os.path.join(self.backupdir, dirname)
        if not os.path.exists(backupdir):
            os.makedirs(backupdir)
        shutil.copyfile(filepath, os.path.join(backupdir, filename))

    def _bytes(self, num):
        for x in ['bytes','KB','MB','GB','TB']:
            if num < 1000.0:
                return "%3.1f %s" % (num, x)
            num /= 1000.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch resize images.')
    parser.add_argument('-d', '--dir', default=CWD, help='Backup directory.')
    parser.add_argument('-b', '--backupdir', default=DESKTOP, help='Backup directory.')
    parser.add_argument('-x', '--maxx', type=int, default=3456, help='Max size x.')
    BatchResize(**vars(parser.parse_args())).resize()
