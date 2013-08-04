# -*- coding: utf-8 -*-

""" Helper for uploading recursively directory. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

import camlipy
from camlipy.rollsum import Rollsum
from camlipy.schema import Bytes, File, StaticSet, Directory

log = logging.getLogger(__name__)
