# -*- encoding: utf-8 -*-
import unittest
import logging

from camlipy.tests import CamliPyTestCase

logging.basicConfig(level=logging.DEBUG)


class CamliPyTestCase(CamliPyTestCase):
    def testBasicSchema(self):
        pass

if __name__ == '__main__':
    unittest.main()
