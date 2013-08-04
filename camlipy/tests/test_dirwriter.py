# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os
import logging
import tempfile

from dirtools import Dir

from camlipy.tests import CamliPyTestCase
from camlipy.dirwriter import DirWriter
from camlipy.dirreader import DirReader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestDirWriter(CamliPyTestCase):
    def testFileWriter(self):
        dir_writer = DirWriter(self.server, '/work/writing')
        dir_br = dir_writer.put_dir()

        dest = tempfile.mkdtemp()
        print "#" * 200
        print dest
        dir_reader = DirReader(self.server, dir_br, dest)
        dir_reader.download()

        self.assertEqual(Dir('/work/writing').hash(), Dir(os.path.join(dest, 'writing')).hash())