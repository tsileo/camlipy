# -*- coding: utf-8 -*-
import urlparse
import logging
import hashlib
import re

import requests

CAMLIVERSION = 1
MAX_STAT_BLOB = 1000

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
    def __init__(self, server, auth=None):
        self.server = server
        self.auth = auth
        self.conf = self._conf_discovery()

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

    @classmethod
    def get_hash(cls, blob):
        return compute_hash(blob)

    def get_blob(self, blobref):
        """ Retrieve blob content. """
        log.debug('Fetching blobref:{0}'.format(blobref))
        blobref_url = urlparse.urljoin(self.url_blobRoot,
                                       'camli/{0}'.format(blobref))

        # TODO gerer le streaming
        # TODO handle already existing blobs
        r = requests.get(blobref_url, auth=self.auth, stream=True)

        if r.status_code == 404:
            return
        elif r.status_code == 200:
            return r.text

        r.raise_for_status()

    def _stat(self, blobrefs=[]):
        """ Perform a multi-stat on blobs
        to check if some are already present. """
        stat_url = urlparse.urljoin(self.url_blobRoot, 'camli/stat')
        stat_data = {'camliversion': CAMLIVERSION}

        for i, blobref in enumerate(blobrefs):
            stat_data['blob{0}'.format(i + 1)] = blobref

        r = requests.post(stat_url, data=stat_data, auth=self.auth)
        r.raise_for_status()
        return r.json()

    def put_blobs(self, blobs):
        """ Upload blobs using with standard multi-part upload. """
        blobrefs = set(['sha1-{0}'.format(compute_hash(blob)) for blob in blobs])

        stat_res = self._stat(blobrefs)

        blobrefs_stat = set([s['blobRef'] for s in stat_res['stat']])

        blobrefs_missing = blobrefs - blobrefs_stat
        blobrefs_existing = blobrefs - blobrefs_missing

        if not blobrefs_missing:
            return

        r_files = {}
        for blob in blobs:
            bref = 'sha1-{0}'.format(compute_hash(blob))
            if isinstance(blob, basestring):
                blob_content = blob
            else:
                blob_content = blob.read()
            r_files[bref] = (bref, blob_content)

        r = requests.post(stat_res['uploadUrl'],
                          files=r_files,
                          auth=self.auth)
        r.raise_for_status()

        # TODO return something better
        return r.json()

    def describe_blob(self, blobref):
        """ Return blob meta data. """
        describe = 'camli/search/describe?blobref={0}'.format(blobref)
        describe_url = urlparse.urljoin(self.url_searchRoot, describe)

        r = requests.get(describe_url, auth=self.auth)
        r.raise_for_status()

        return r.json()
