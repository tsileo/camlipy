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
        test_blob.write(os.urandom(5 * (1024 << 10)))

        log.debug('Ramdom file generated')
        test_blob.seek(0)
        file_writer = FileWriter(self.server, fileobj=test_blob)
        file_writer.chunk()

        self.assertEqual(list(file_writer.check_spans())[:8], range(8))

        blob_ref = file_writer.bytes_writer()

        file_reader = FileReader(self.server, blob_ref)
        spans2 = file_reader.load_spans()

        print file_writer.spans
        print spans2

        self.assertEqual(len(file_writer.spans), len(spans2))

        for index, span in enumerate(file_writer.spans):
            self.assertEqual(len(span.children), len(spans2[index].children))
            self.assertEqual(span.br, spans2[index].br)


if __name__ == '__main__':
    unittest.main()
