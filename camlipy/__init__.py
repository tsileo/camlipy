""" Camlistore client. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'
__version__ = '0.1.0'

import urlparse
import logging
import hashlib
import re
import tempfile

import requests

from camlipy.filewriter import put_file
from camlipy.filereader import get_file
from camlipy.directory import put_directory, get_directory
from camlipy.search import Search
from camlipy.schema import Permanode, StaticSet

__all__ = ['compute_hash', 'check_hash', 'Camlistore']

CAMLIVERSION = 1
MAX_STAT_BLOB = 1000
DEBUG = False

log = logging.getLogger(__name__)


def compute_hash(data, blocksize=4096):
    """ Return the hash object for the file `filepath', processing the file
    by chunk of `blocksize'.

    :type filepath: data
    :param filepath: string or fileobj

    :type blocksize: int
    :param blocksize: Size of the chunk when processing the file

    """
    sha = hashlib.sha1()
    if isinstance(data, basestring):
        sha.update(data)
    else:
        start = data.tell()
        while 1:
            buf = data.read(blocksize)
            if buf:
                sha.update(buf)
            else:
                break
        data.seek(start)
    return 'sha1-{0}'.format(sha.hexdigest())


def check_hash(_hash):
    """ Check if the hash is valid. """
    return bool(re.match(r'sha1-[a-fA-F0-9]{40}', _hash))


class Camlistore(object):
    """ Camlistore Python client

    Args:
        server: server address
        auth: tuple (user, password) if authentication is enabled.

    """
    def __init__(self, server='http://localhost:3179', auth=None):
        self.server = server
        self.auth = auth
        self.conf = self._conf_discovery()

        self.public_key_blob_ref = self.conf['signing']['publicKeyBlobRef']

        self.url_blobRoot = urlparse.urljoin(self.server,
                                             self.conf['blobRoot'])
        self.url_signHandler = urlparse.urljoin(self.server,
                                                self.conf['signing']['signHandler'])
        self.url_searchRoot = urlparse.urljoin(self.server,
                                               self.conf['searchRoot'])

    def _conf_discovery(self):
        """ Perform a discovery to gather server configuration. """
        r = requests.get(self.server,
                         auth=self.auth,
                         headers={'Accept': 'text/x-camli-configuration'})
        r.raise_for_status()
        return r.json()

    @staticmethod
    def get_hash(blob):
        return compute_hash(blob)

    def get_blob(self, blobref):
        """
        Retrieve blob content,
        return a fileobj.
        If the blob is a schema, it returns a dict.
        """
        if DEBUG:
            log.debug('Fetching blobref:{0}'.format(blobref))
        blobref_url = urlparse.urljoin(self.url_blobRoot,
                                       'camli/{0}'.format(blobref))

        r = requests.get(blobref_url, auth=self.auth, stream=True)

        if r.status_code == 404:
            return
        elif r.status_code == 200:
            # Store the blob in memory, and write it to disk if it exceed 1MB
            out = tempfile.SpooledTemporaryFile(max_size=1024 << 10)

            # Check if the blob contains binary data
            if not self.describe_blob(blobref).get('camliType'):
                while 1:
                    buf = r.raw.read(512 << 10)
                    if buf:
                        out.write(buf)
                    else:
                        break

                out.seek(0)
                return out
            else:
                # If the blob is not binary data,
                # then, it's a schema, so we return a dict.
                return r.json()

        r.raise_for_status()

    def _stat(self, blobrefs=[]):
        """ Perform a multi-stat on blobs
        to check if some are already present. """
        if DEBUG:
            log.debug('Perform stat')
        stat_url = urlparse.urljoin(self.url_blobRoot, 'camli/stat')
        stat_data = {'camliversion': CAMLIVERSION}

        for i, blobref in enumerate(blobrefs):
            stat_data['blob{0}'.format(i + 1)] = blobref

        r = requests.post(stat_url, data=stat_data, auth=self.auth)

        if DEBUG:
            log.debug(r.text)

        r.raise_for_status()
        return r.json()

    def put_blobs(self, blobs):
        """ Upload blobs using with standard multi-part upload.
        Returns a dict with received (blobref and size) and skipped (blobref only)
        """
        # First we create a dict {blobRef: blob, ...}
        blobrefs = {}
        for blob in blobs:
            blobrefs[compute_hash(blob)] = blob

        # And a set containing every blobRefs
        blobrefs_all = frozenset(blobrefs.keys())

        # Perform a stat to check which blobs are already present
        # and to fetch uploadUrl and maxUploadSize.
        stat_res = self._stat(blobrefs_all)
        upload_url = stat_res['uploadUrl']
        max_upload_size = stat_res['maxUploadSize']

        blobrefs_stat = frozenset([s['blobRef'] for s in stat_res['stat']])

        blobrefs_missing = blobrefs_all - blobrefs_stat
        blobrefs_skipped = blobrefs_all - blobrefs_missing

        if DEBUG:
            log.debug('blobs missing: {0}'.format(blobrefs_missing))
            log.debug('blobs skipped: {0}'.format(blobrefs_skipped))

        res = {'skipped': stat_res['stat'],
               'received': []}

        if DEBUG:
            log.debug('Starting first upload batch')

        batch_size = 0
        r_files = {}

        for br in blobrefs_missing:
            blob = blobrefs[br]
            bref = compute_hash(blob)
            if isinstance(blob, basestring):
                blob_content = blob
                blob_size = len(blob)
            else:
                blob_content = blob.read()
                # Seek to the end of the file
                blob.seek(0, 2)
                blob_size = blob.tell()

            if batch_size + blob_size > max_upload_size:
                if DEBUG:
                    log.debug('Upload first batch before continue, batch size:{0}'.format(batch_size))
                batch_res = self._put_blobs(upload_url, r_files)
                # Retrieve the next upload url
                upload_url = batch_res['uploadUrl']

                res['received'].extend(batch_res['received'])
                r_files = {}
                batch_size = 0

            r_files[bref] = (bref, blob_content)
            batch_size += blob_size

        if r_files.keys():
            if DEBUG:
                log.debug('Current batch size: {0}'.format(batch_size))
                log.debug('Uploading last batch')

            batch_res = self._put_blobs(upload_url, r_files)

            res['received'].extend(batch_res['received'])

        blobs_received = [d['blobRef'] for d in res['received']]
        blobs_skipped = [d['blobRef'] for d in res['skipped']]

        blobrefs_failed = set(blobrefs_all.difference(blobs_received))
        blobrefs_failed.difference_update(blobs_skipped)

        if len(blobrefs_failed):
            if DEBUG:
                for br in blobrefs_failed:
                    log.debug('Blob with br:{0}, content:{1} failed.'.format(br, blobrefs[br]))

            raise Exception('Some blobs failed to upload: {0}'.format(blobrefs_failed))

        res['success'] = list(blobs_received)
        res['success'].extend(blobs_skipped)

        return res

    def _put_blobs(self, upload_url, r_files):
        """ Perform the multi-part upload/
        Batch uploader. """
        if DEBUG:
            log.debug('Starting multi-part upload')
        r = requests.post(upload_url,
                          files=r_files,
                          auth=self.auth)

        if DEBUG:
            log.debug(r.text)

        r.raise_for_status()

        return r.json()

    def describe_blob(self, blobref):
        """ Return blob meta data. """
        describe = 'camli/search/describe?blobref={0}'.format(blobref)
        describe_url = urlparse.urljoin(self.url_searchRoot, describe)

        r = requests.get(describe_url, auth=self.auth)
        r.raise_for_status()

        return r.json()['meta'][blobref]

    def search(self, value, attr='', fuzzy=False, max=100):
        """ Perform query with the same syntax as Camistore ui.

        Examples of queries:
        - tag:mytag
        - title:my_text_file.txt
        - my query

        """
        return Search(self).search(value, attr=attr, fuzzy=fuzzy, max=max)

    def put_blob(self, blob):
        """ Shortcut/helper for uploading a single blob.

        Blob can be either a string or a fileobj.

        """
        res = self.put_blobs([blob])
        blob_ref = compute_hash(blob)
        if blob_ref in res['success']:
            return blob_ref

    def put_file(self, path=None, fileobj=None, permanode=False):
        """ Shortcut for uploading a file along with its meta-data.

        Call camlipy.filewriter.put_file under the hood.

        """
        return put_file(self, path=path, fileobj=fileobj, permanode=permanode)

    def get_file(self, blob_ref, fileobj=None):
        """ Shortcut for downloading/restoring a file.

        Call camlipy.filereader.get_file under the hood.

        """
        return get_file(self, blob_ref=blob_ref, fileobj=fileobj)

    def put_directory(self, path, permanode=False):
        """ Shortcut for upload an entire directory.

        Call camlipy.directory.put_directory under the hood.

        """
        return put_directory(self, path, permanode=permanode)

    def get_directory(self, br, path):
        """ Shortcut for restoring/retrieving a directory.

        Call camlipy.directory.get_directory under the hood.

        """
        return get_directory(self, br, path)

    def permanode(self, blob_ref=None):
        """ Shortcut to initialize a permanode. """
        return Permanode(self, blob_ref)

    def static_set(self, blob_ref=None):
        """ Shortcut to initialize a static-set. """
        return StaticSet(self, blob_ref)

    def add_to_static_set(self, blob_refs):
        """ Shortcut to create a new static-set. """
        return self.static_set().save(blob_refs)
