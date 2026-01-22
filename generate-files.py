#!/usr/bin/python3
"""
Generate random text files with common English words.

This script creates multiple text files filled with random common words.
Files are named using two random words (e.g., "apple-banana.txt") and
contain random text of specified sizes. Uses multithreading for faster
generation of large numbers of files.

Examples:
  ./generate-files.py --count 100
  ./generate-files.py --count 50 --minsize 1024 --maxsize 10240
  ./generate-files.py --count 1000 --dirpath /tmp/testfiles
  ./generate-files.py --count 100 --wordfile /path/to/words.txt

Options:
  --count <n>       Number of files to generate (default: 1)
  --minsize <n>     Minimum file size in bytes (default: 10)
  --maxsize <n>     Maximum file size in bytes (default: 50)
  --dirpath <path>  Directory to create files in (default: current directory)
  --wordfile <path> Path to word list file (default: commonwords.txt in script directory)
"""
import argparse, os, random
from multiprocessing.dummy import Pool as ThreadPool


def load_words(wordfile):
    """ Load words from the specified file, keeping only alphanumeric words. """
    with open(wordfile, 'r') as f:
        words = [w.strip() for w in f.read().split('\n')]
        return set(w for w in words if w and w.isalnum())


def word(words):
    """ Get a random word from the word list. """
    return random.sample(words, 1)[0]


def _generate_files(args):
    created = 0
    dirpath, count, minsize, maxsize, words = args
    while created < count:
        filename = '%s-%s.txt' % (word(words), word(words))
        filepath = os.path.join(dirpath, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as handle:
                currsize, wordcount = 0, 0
                filesize = random.randint(0, maxsize - minsize) + minsize
                while currsize < filesize:
                    wordcount += 1
                    newword = '%s ' % word(words)
                    newword += '\n' if wordcount % 10 == 0 else ''
                    newsize = currsize + len(newword)
                    if newsize > filesize:
                        newword = newword[0:newsize - filesize]
                    handle.write(newword)
                    currsize += len(newword)
            created += 1
    return None


def generate_files(dirpath, count, minsize, maxsize, words, threads=10):
    # Calculate how many files each thread needs to create
    threads = min(count, threads)
    counts = [int(count / threads)] * threads
    counts[-1] += count - sum(counts)
    # Create a threadpool to generate files
    dirpath = dirpath or os.getcwd()
    args = [(dirpath, c, minsize, maxsize, words) for c in counts]
    pool = ThreadPool(threads)
    pool.map(_generate_files, args)
    pool.close()
    pool.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate random files.')
    parser.add_argument('--count', default=1, type=int, help='Number of files to generate.')
    parser.add_argument('--minsize', default=10, type=int, help='Minimum file size.')
    parser.add_argument('--maxsize', default=50, type=int, help='Maximum file size.')
    parser.add_argument('--dirpath', default=None, help='Directory to create files in.')
    parser.add_argument('--wordfile', default='/usr/share/dict/words', help='Path to word list file.')
    args = parser.parse_args()
    words = load_words(args.wordfile)
    generate_files(args.dirpath, args.count, args.minsize, args.maxsize, words)
