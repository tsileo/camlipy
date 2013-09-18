# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os
import logging
import tempfile

import sh

from camlipy.tests import CamliPyTestCase, CAMLIPY_CAMLISTORE_PATH
from camlipy.filewriter import FileWriter, put_file

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestCamputAndCamgetCompatibility(CamliPyTestCase):

    def testCamlistoreFileWriteAndCamputCompatibility(self):
        # Create a 1MB random file
        test_file = tempfile.NamedTemporaryFile()
        test_file.write(os.urandom(int(1.5 * (1024 << 10))))
        test_file.seek(0)

        log.debug('Random file generated')

        log.info('Putting file with camput file:')
        old_pwd = os.getcwd()
        sh.cd(CAMLIPY_CAMLISTORE_PATH)
        camput_blobref = sh.devcam('put', 'file', test_file.name)
        sh.cd(old_pwd)
        log.info('Camput blobRef: {0}'.format(camput_blobref))

        file_writer = FileWriter(self.server, fileobj=test_file)
        file_writer.chunk()
        camplipy_blobref = file_writer.bytes_writer()

        log.info('Camlipy blobRef: {0}'.format(camplipy_blobref))

        log.info('FileWriter cnt={0}'.format(file_writer.cnt))

        # Check that no data blob has been uploaded,
        # since we just uploaded the same file with camput file.

        # "<= 1" since sometimes, camlipy make a slightly bigger end blob.
        self.assertTrue(file_writer.cnt['uploaded'] <= 1)

    def testPutFileAndCamgetCompatibility(self):
        test_file = tempfile.NamedTemporaryFile()
        test_file.write(os.urandom(int(1.5 * (1024 << 10))))
        test_file.seek(0)

        log.debug('Random file generated')

        blob_ref = put_file(self.server, test_file.name)
        log.info('Camlipy put_file blobRef: {0}'.format(blob_ref))

        td = tempfile.mkdtemp()
        old_pwd = os.getcwd()

        sh.cd(CAMLIPY_CAMLISTORE_PATH)

        sh.devcam('get', '-o', td, blob_ref)
        sh.cd(old_pwd)
        original_hash = self.compute_hash(open(os.path.join(td,
                                                            test_file.name)))
        restored_hash = self.compute_hash(test_file)

        self.assertEqual(original_hash, restored_hash)

if __name__ == '__main__':
    unittest.main()
