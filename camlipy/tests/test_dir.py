# encoding: utf-8
import os
import logging
import tempfile

from dirtools import Dir

from camlipy.tests import CamliPyTestCase
from camlipy.directory import put_directory, get_directory

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class testDir(CamliPyTestCase):
    def testDirectory(self):
        dir_br = put_directory(self.server, '/work/writing')

        dest = tempfile.mkdtemp()

        get_directory(self.server, dir_br, dest)

        # Check the two directories are equal using Dirtools.hash
        self.assertEqual(Dir('/work/writing').hash(),
                         Dir(os.path.join(dest, 'writing')).hash())
