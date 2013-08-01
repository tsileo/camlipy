# -*- encoding: utf-8 -*-
import unittest
import os
import logging
import tempfile

from camlipy.tests import CamliPyTestCase
from camlipy.filewriter import FileWriter

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestFileWriter(CamliPyTestCase):

    def testBigFile(self):
        # Create a 5MB random file
        test_blob = tempfile.TemporaryFile()
        test_blob.write(os.urandom(2 * (1024 << 10)))

        log.debug('Ramdom file generated')
        test_blob.seek(0)
        file_writer = FileWriter(self.server, fileobj=test_blob)
        file_writer.chunk()

        self.assertEqual(list(file_writer.check_spans()), range(25))

if __name__ == '__main__':
    unittest.main()
