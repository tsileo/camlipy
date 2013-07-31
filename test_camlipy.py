# -*- encoding: utf-8 -*-
import unittest
import os

from camlipy import Camlistore, compute_hash

CAMLIPY_SERVER = os.environ.get('CAMLIPY_SERVER', 'http://localhost:3179/')


class CamliPyTestCase(unittest.TestCase):
    def setUp(self):
        self.server = Camlistore(CAMLIPY_SERVER)

    def testPutBlobStr(self):
        test_blob_str = os.urandom(4096)
        resp = self.server.put_blobs([test_blob_str])
        self.assertEqual(resp['received'], [{'blobRef': compute_hash(test_blob_str), 'size': 4096}])


if __name__ == '__main__':
    unittest.main()
