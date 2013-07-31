# -*- encoding: utf-8 -*-
import unittest
import os
import logging
import tempfile

from camlipy.tests import CamliPyTestCase

logging.basicConfig(level=logging.DEBUG)


class TestCamliPy(CamliPyTestCase):

    def testPutBlobStr(self):
        test_blob_str = os.urandom(4096)
        resp = self.server.put_blobs([test_blob_str])
        self.assertEqual(resp['received'], [{'blobRef': self.compute_hash(test_blob_str), 'size': 4096}])

    def testPutExistingBlob(self):
        test_blob_str = os.urandom(4096)
        test_blob_br = self.compute_hash(test_blob_str)
        resp = self.server.put_blobs([test_blob_str])
        self.assertEqual(resp['received'], [{'blobRef': self.compute_hash(test_blob_str), 'size': 4096}])

        resp2 = self.server.put_blobs([test_blob_str])

        self.assertTrue(len(resp2['received']) == 0)
        self.assertEqual(set([test_blob_br]), resp2['existing'])

    def testPutBlobFileobj(self):
        test_blob_file = tempfile.TemporaryFile()
        test_blob_file.write(os.urandom(4096))
        test_blob_file.seek(0)

        resp = self.server.put_blobs([test_blob_file])
        test_blob_file.seek(0)
        self.assertEqual(resp['received'], [{'blobRef': self.compute_hash(test_blob_file.read()), 'size': 4096}])

    def testGetBlob(self):
        data_len = (1024 << 10) + (4 << 10)
        blob_data = os.urandom(data_len)
        blob_br = self.compute_hash(blob_data)
        self.server.put_blobs([blob_data])

        fileobj = self.server.get_blob(blob_br)
        self.assertTrue(isinstance(fileobj, tempfile.SpooledTemporaryFile))
        self.assertEqual(len(fileobj.read()), data_len)
        fileobj.seek(0)
        self.assertEqual(fileobj.read(), blob_data)

    def testStat(self):
        test_blob_str = os.urandom(4096)
        blob_br = self.compute_hash(test_blob_str)
        resp = self.server.put_blobs([test_blob_str])
        self.assertEqual(blob_br, resp['received'][0]['blobRef'])

        stat_resp = self.server._stat([blob_br])
        self.assertEqual(stat_resp['stat'][0], {'blobRef': blob_br, 'size': 4096})

if __name__ == '__main__':
    unittest.main()
