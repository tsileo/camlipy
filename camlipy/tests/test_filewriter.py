# -*- encoding: utf-8 -*-
import unittest
import os
import logging
import tempfile

from camlipy.tests import CamliPyTestCase
from camlipy.filewriter import FileWriter
from camlipy.filereader import FileReader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestFileWriterAndFileReader(CamliPyTestCase):

    def testBigFile(self):
        # Create a 1MB random file
        test_blob = tempfile.TemporaryFile()
        test_blob.write(os.urandom(2 * (1024 << 10)))

        log.debug('Ramdom file generated')
        test_blob.seek(0)
        blob_hash = self.compute_hash(test_blob)
        test_blob.seek(0)
        file_writer = FileWriter(self.server, fileobj=test_blob)
        file_writer.chunk()

        self.assertEqual(list(file_writer.check_spans())[:len(file_writer.spans) - 2], range(len(file_writer.spans) - 2))

        blob_ref = file_writer.bytes_writer()

        file_reader = FileReader(self.server, blob_ref)
        file_reader.load_spans()
        spans2 = file_reader.spans

        print file_writer.spans
        print spans2

        out = file_reader.build()
        out_hash = self.compute_hash(out)
        test_blob.seek(0)
        out.seek(0)
        print len(test_blob.read()), len(out.read())
        self.assertEqual(out_hash, blob_hash)

if __name__ == '__main__':
    unittest.main()
