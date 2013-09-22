# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os
import logging
import tempfile

from camlipy.tests import CamliPyTestCase
from camlipy.filewriter import FileWriter
from camlipy.filereader import FileReader

log = logging.getLogger(__name__)


class TestFileWriterAndFileReader(CamliPyTestCase):

    def testBigFile(self):
        # Create a 1MB random file
        test_blob = tempfile.TemporaryFile()
        test_blob.write(os.urandom(1024 << 10))

        log.debug('Random file generated')
        test_blob.seek(0)
        blob_hash = self.compute_hash(test_blob)
        test_blob.seek(0)
        file_writer = FileWriter(self.server, fileobj=test_blob)
        file_writer.chunk()

        self.assertEqual(list(file_writer.check_spans())[:len(file_writer.spans) - 2], range(len(file_writer.spans) - 2))

        blob_ref = file_writer.bytes_writer()

        log.info('FileWriter cnt={0}'.format(file_writer.cnt))

        file_reader = FileReader(self.server, blob_ref)
        file_reader.load_spans()

        out = file_reader.build()

        test_blob.seek(0)
        self.assertEqual(len(out.read()), len(test_blob.read()))
        out.seek(0)
        test_blob.seek(0)
        out_hash = self.compute_hash(out)
        self.assertEqual(out_hash, blob_hash)

        # Try to re-upload the same file and check that no data is re-uploaded
        file_writer2 = FileWriter(self.server, fileobj=test_blob)
        file_writer2.chunk()

        log.info('FileWriter2 cnt={0}'.format(file_writer2.cnt))

        self.assertEqual(file_writer2.cnt['uploaded'], 0)
        self.assertEqual(file_writer2.cnt['uploaded_size'], 0)


if __name__ == '__main__':
    unittest.main()
