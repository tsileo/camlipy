# encoding: utf-8
import os
import logging
import tempfile
import shutil

from dirtools import Dir

from camlipy.tests import CamliPyTestCase
from camlipy.directory import put_directory, get_directory

log = logging.getLogger(__name__)


class testDir(CamliPyTestCase):
    def testDirectory(self):
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, 'testfile1'), 'wb') as fh:
            fh.write(os.urandom(256 << 10))
        testdir = os.path.join(tmpdir, 'testdir')
        os.mkdir(testdir)
        with open(os.path.join(testdir, 'testfile2'), 'wb') as fh:
            fh.write(os.urandom(256 << 10))

        dir_br = put_directory(self.server, tmpdir)

        dest = tempfile.mkdtemp()

        get_directory(self.server, dir_br, dest)

        # Check the two directories are equal using Dirtools.hash
        self.assertEqual(Dir(tmpdir).hash(),
                         Dir(dest).hash())

        shutil.rmtree(tmpdir)
        shutil.rmtree(dest)
