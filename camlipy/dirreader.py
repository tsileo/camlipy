# -*- coding: utf-8 -*-

""" Helper for downloading directory. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

from dirtools import Dir

from camlipy.schema import StaticSet, Directory, Schema, apply_stat_info

log = logging.getLogger(__name__)


class DirReader(object):
    def __init__(self, con, br, path):
        if not os.path.isdir(path):
            os.mkdir(path)

        self.br = br
        self.con = con
        self.path = path

    def download(self):
        print self._read_dir(self.br)

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
