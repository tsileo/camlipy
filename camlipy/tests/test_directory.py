# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import os
import logging
import tempfile

from dirtools import Dir

from camlipy.tests import CamliPyTestCase
from camlipy.directory import DirWriter, DirReader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestDirectory(CamliPyTestCase):
    def testFileWriter(self):
        dir_writer = DirWriter(self.server, '/work/writing')
        dir_br = dir_writer.put_dir()

        dest = tempfile.mkdtemp()

        dir_reader = DirReader(self.server, dir_br, dest)
        dir_reader.download()

        self.assertEqual(Dir('/work/writing').hash(), Dir(os.path.join(dest, 'writing')).hash())
