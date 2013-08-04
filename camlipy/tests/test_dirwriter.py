# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os
import logging
import tempfile

from camlipy.tests import CamliPyTestCase
from camlipy.dirwriter import DirWriter

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestDirWriter(CamliPyTestCase):
    def testFileWriter(self):
        dir_writer = DirWriter(self.server, '/work/writing')
        print dir_writer.put_dir()