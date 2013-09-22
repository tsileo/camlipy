# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os

import ujson as json

from camlipy.tests import CamliPyTestCase
from camlipy.schema import Schema, Permanode, StaticSet
import camlipy


class TestSchema(CamliPyTestCase):
    def testNewBasicSchema(self):
        basic_schema = Schema(self.server)
        expected = {'camliVersion': camlipy.CAMLIVERSION}
        self.assertEqual(basic_schema.json(), json.dumps(expected))
        signed = json.loads(basic_schema.sign())
        self.assertTrue('camliSigner' in signed)
        self.assertTrue('camliSig' in signed)

    def _createBlob(self):
        test_blob_str = os.urandom(4096)
        self.server.put_blobs([test_blob_str])
        return self.compute_hash(test_blob_str)

    def testPermanodeAndClaims(self):
        br = self._createBlob()
        permanode = Permanode(self.server)
        permanode_br = permanode.save(br)

        # Create a permanode with a camliContent claims
        permanode_res = self.server.get_blob(permanode_br)
        self.assertTrue(isinstance(permanode_res, dict))
        claims = permanode.claims()
        self.assertEqual(len(claims), 1)
        self.assertEqual(permanode.get_camli_content(), br)

        # Set a new camliContent claim
        br2 = self._createBlob()
        permanode.set_camli_content(br2)
        self.assertEqual(len(permanode.claims()), 2)
        self.assertEqual(permanode.get_camli_content(), br2)

        # Test that we can load an existing permanode schema.
        permanode2 = Permanode(self.server, permanode_br)
        del permanode2.data['camliSig']

        self.assertDictEqual(permanode2.data, permanode.data)

    def testClaims(self):
        br = self._createBlob()
        permanode = Permanode(self.server)
        permanode_br = permanode.save(br)

        d = self.server.describe_blob(permanode_br)
        self.assertEqual(d['camliType'], 'permanode')

        # TODO test del/add/set

    def testStaticSet(self):
        brs = [self._createBlob() for i in range(5)]
        static_set = StaticSet(self.server)
        br = static_set.save(brs)

        d = self.server.describe_blob(br)
        self.assertEqual(d['camliType'], 'static-set')

        static_set2 = StaticSet(self.server, br)
        self.assertEqual(sorted(static_set2.data['members']),
                         sorted(brs))


if __name__ == '__main__':
    unittest.main()
