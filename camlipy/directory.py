# -*- coding: utf-8 -*-

""" Helper for uploading recursively directory. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

from dirtools import Dir

from camlipy.schema import StaticSet, Directory, apply_stat_info

log = logging.getLogger(__name__)


def _put_directory(con, path, permanode=False):
    """ Put a directory, this function is called recursively over sub-directories. """
    # Initialization of the current directory schema.
    directory = Directory(con, path)
    # Since a Directory must point to a static set, we initialize one too.
    static_set = StaticSet(con)
    static_set_members = []
    # Don't walk recursively with walk, since we already
    # calling _put_dir recursively.
    root, dirs, files = Dir(path).walk().next()
    for f in files:
        static_set_members.append(con.put_file(os.path.join(root, f)))
    for d in dirs:
        static_set_members.append(_put_directory(con, os.path.join(root, d), permanode=False))

    static_set_br = static_set.save(static_set_members)

    # We return the directory blobRef
    return directory.save(static_set_br, permanode=permanode)


def put_directory(con, path, permanode=False):
    """ Helper to put a directory. """
    assert os.path.isdir(path)
    return _put_directory(con, path, permanode=permanode)


def _get_directory(con, br, base_path):
    # Load the directory schema
    directory = Directory(con, blob_ref=br)
    # Build the absolute path of the current directory/sub-directory.
    path = os.path.join(base_path, directory.fileName)
    if not os.path.isdir(path):
        os.mkdir(path)
    apply_stat_info(path, directory.data)

    # Load the directory static set.
    static_set = StaticSet(con, directory.entries)
    for member_br in static_set.members:
        blob_metadata = con.describe_blob(member_br)
        if blob_metadata['camliType'] == 'file':
            file_path = os.path.join(path, blob_metadata['file']['fileName'])
            with open(file_path, 'wb') as fh:
                con.get_file(member_br, fh)
        elif blob_metadata['camliType'] == 'directory':
            _get_directory(con, member_br, base_path=path)


def get_directory(con, br, path):
    # Check if the blobRef is a permanode
    blob_metadata = con.describe_blob(br)
    if blob_metadata['camliType'] == 'permanode':
        br = blob_metadata['permanode']['attr']['camliContent'][0]
    # Create the destination path if it doesn't exists.
    if not os.path.isdir(path):
        os.mkdir(path)
    # Check if the blob is permanode
    blob_metadata = con.describe_blob(br)
    if blob_metadata['camliType'] == 'permanode':
        # If so, update the destination blobRef
        br = blob_metadata['permanode']['attr']['camliContent'][0]
    _get_directory(con, br, path)
