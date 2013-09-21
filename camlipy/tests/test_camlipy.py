# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

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
        self.assertEqual(resp['success'], [self.compute_hash(test_blob_str)])

    def testPutExistingBlob(self):
        test_blob_str = os.urandom(4096)
        test_blob_br = self.compute_hash(test_blob_str)
        resp = self.server.put_blobs([test_blob_str])
        self.assertEqual(resp['received'], [{'blobRef': self.compute_hash(test_blob_str), 'size': 4096}])
        self.assertEqual(resp['success'], [self.compute_hash(test_blob_str)])

        resp2 = self.server.put_blobs([test_blob_str])

        self.assertTrue(len(resp2['received']) == 0)
        self.assertEqual([{'blobRef': test_blob_br, 'size': 4096}], resp2['skipped'])
        self.assertEqual([test_blob_br], resp2['success'])

    def testPutBlobFileobj(self):
        test_blob_file = tempfile.TemporaryFile()
        test_blob_file.write(os.urandom(4096))
        test_blob_file.seek(0)

        resp = self.server.put_blobs([test_blob_file])
        test_blob_file.seek(0)
        self.assertEqual(resp['received'], [{'blobRef': self.compute_hash(test_blob_file.read()), 'size': 4096}])

    def testPutBlobsBiggerThanMaxUpload(self):
        max_upload_size = self.server._stat()['maxUploadSize']
        nb_blobs = 10000
        blob_size = int((max_upload_size / 1000) * 1.5 / nb_blobs)
        test_blobs = [os.urandom(blob_size) * 1000 for i in xrange(blob_size)]
        test_blobs_br = set([self.compute_hash(b) for b in test_blobs])
        resp = self.server.put_blobs(test_blobs)
        self.assertEqual(test_blobs_br, set([r['blobRef'] for r in resp['received']]))

    def testGetBlob(self):
        data_len = (1024 << 10) + (4 << 10)
        blob_data = os.urandom(data_len)
        blob_br = self.server.put_blob(blob_data)
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

    def testPutBlobHelper(self):
        test_blob_str = os.urandom(4096)
        expected_br = self.compute_hash(test_blob_str)
        br = self.server.put_blob(test_blob_str)
        self.assertEqual(expected_br, br)

if __name__ == '__main__':
    unittest.main()
