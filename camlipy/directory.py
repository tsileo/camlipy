# -*- coding: utf-8 -*-

""" Helper for uploading recursively directory. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

from dirtools import Dir

from camlipy.schema import StaticSet, Directory, Schema, apply_stat_info

log = logging.getLogger(__name__)


class DirWriter(object):
    def __init__(self, con, path):
        assert os.path.isdir(path)
        self.con = con
        self.path = path

    def put_dir(self):
        return self._put_dir(self.path)

    def _put_dir(self, path):
        directory = Directory(self.con, path)
        static_set = StaticSet(self.con)
        members = []
        # Don't walk recursively with walk, since we already
        # calling _put_dir recursively.
        root, dirs, files = Dir(path).walk().next()
        for f in files:
            members.append(self.con.put_file(os.path.join(root, f)))
        for d in dirs:
            members.append(self._put_dir(os.path.join(root, d)))

        static_set_br = static_set.save(members)
        return directory.save(static_set_br)


class DirReader(object):
    def __init__(self, con, br, path):
        if not os.path.isdir(path):
            os.mkdir(path)

        self.br = br
        self.con = con
        self.path = path

    def restore(self):
        return self._read_dir(self.br)

    def _read_dir(self, br, base_root=None):
        if base_root is None:
            base_root = self.path
        directory = Directory(self.con, blob_ref=br)
        root = os.path.join(base_root, directory.data['fileName'])
        if not os.path.isdir(root):
            os.mkdir(root)
        apply_stat_info(root, directory.data)

        static_set = StaticSet(self.con, directory.data['entries'])
        for member in static_set.data['members']:
            blob_metadata = self.con.describe_blob(member)
            if blob_metadata['camliType'] == 'file':
                file_path = os.path.join(root, blob_metadata['file']['fileName'])
                with open(file_path, 'wb') as fh:
                    self.con.get_file(member, fh)
            elif blob_metadata['camliType'] == 'directory':
                self._read_dir(member, base_root=root)

# TODO


def get_directory():
    pass


def put_directory():
    pass
