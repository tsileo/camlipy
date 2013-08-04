# -*- coding: utf-8 -*-
"""Camlipy command line tool.

Usage:
  camlipy put [-] [<file>...] [--permanode]
  camlipy get <blob_ref> [--contents]
  camlipy config <server_url>
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

import simplejson as json
from docopt import docopt

from camlipy import __version__, Camlistore

DEFAULT_SERVER = 'http://localhost:3179'
CAMLISTORE_CLIENT_CONFIG = os.path.expanduser('~/.config/camlistore/client-config.json')
CAMLIPY_CONFIG = os.path.expanduser('~/.config/camlipy/config.json')


def load_conf(path):
    return json.loads(open(CAMLISTORE_CLIENT_CONFIG, 'rb').read())

server = DEFAULT_SERVER
for path in [CAMLISTORE_CLIENT_CONFIG, CAMLIPY_CONFIG]:
    if os.path.isfile(CAMLISTORE_CLIENT_CONFIG):
        server = load_conf(CAMLISTORE_CLIENT_CONFIG)['server']

c = Camlistore(server)

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
    if arguments['config']:
        # Write a basic configuration file.
        conf = {'server': arguments['<server_url>']}
        config_path = os.path.expanduser('~/.config/camlipy/')
        if not os.path.isdir(config_path):
            os.mkdir(config_path)
        with open(os.path.join(config_path, 'config.json'), 'wb') as fh:
            fh.write(json.dumps(conf))

    elif arguments['put']:
        # Put sub-command
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
        if not arguments['--content'] and blob_metadata['camliType'] == 'permanode':
            new_br = blob_metadata['permanode']['attr']['camliContent'][0]
            blob = c.get_blob(new_br)
            blob_metadata = c.describe_blob(new_br)

        if arguments['--contents'] or blob_metadata['camliType'] not in ['file', 'directory']:
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
