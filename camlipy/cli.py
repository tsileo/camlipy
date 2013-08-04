"""Camlipy command line tool.

Usage:
  camlipy put [-] [<file>...] [--permanode]
  camlipy get <blob_ref> [--contents]
  camlipy -h | --help
  camlipy --version

Options:
  -h --help      Show this screen.
  --version      Show version.
  --permanode    Create a permanode.
"""
import sys
import os
import logging

from docopt import docopt

from camlipy import __version__, Camlistore

c = Camlistore('http://localhost:3179')

log = logging.getLogger(__name__)


class CamlipyFilter(logging.Filter):
    def filter(self, rec):
        if rec.name.startswith('camlipy') or rec.name == '__main__':
            return True
        else:
            return rec.levelno >= logging.WARNING

handler = logging.StreamHandler()
handler.addFilter(CamlipyFilter())
handler.setFormatter(logging.Formatter('%(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)


def piped_in():
    with sys.stdin as stdin:
        if not stdin.isatty():
            return stdin.read()
        return None


def main():
    arguments = docopt(__doc__, version=__version__)

    if arguments['put']:
        if arguments['-']:
            # Read stdin
            data = piped_in()
            # TODO gerer le put blob
        for f in arguments['<file>']:
            if os.path.isfile(f):
                br = c.put_file(f, permanode=arguments['--permanode'])
                log.info('{0}: {1}'.format(f, br))
            # TODO handle directory

    elif arguments['get']:
        blob = c.get_blob(arguments['<blob_ref>'])
        blob_metadata = c.describe_blob(arguments['<blob_ref>'])
        if arguments['--contents']:
            if isinstance(blob, dict):
                log.info(blob)
            else:
                log.info(blob.read())
        elif blob_metadata['camliType'] == 'file':
            log.info()
        elif blob_metadata['camliType'] == 'directory':
            log.info()
        # TODO handle file/directory

if __name__ == '__main__':
    main()
