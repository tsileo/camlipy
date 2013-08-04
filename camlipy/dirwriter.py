# -*- coding: utf-8 -*-

""" Helper for uploading recursively directory. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

from dirtools import Dir

from camlipy.schema import StaticSet, Directory

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
