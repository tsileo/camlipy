# -*- encoding: utf-8 -*-

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import unittest
import os
import logging

logging.basicConfig(level=logging.DEBUG)

import camlipy
from camlipy import Camlistore, compute_hash

camlipy.DEBUG = True
CAMLIPY_SERVER = os.environ.get('CAMLIPY_SERVER', 'http://localhost:3179/')
CAMLIPY_CAMLISTORE_PATH = os.environ.get('CAMLIPY_CAMLISTORE_PATH',
                                         os.path.expanduser('~/camlistore'))


class CamliPyTestCase(unittest.TestCase):
    def setUp(self):
        self.server = Camlistore(CAMLIPY_SERVER, auth=('', 'pass3179'))
        self.compute_hash = compute_hash
