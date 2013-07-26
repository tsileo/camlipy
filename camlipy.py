# -*- coding: utf-8 -*-
import urlparse
import logging
import hashlib
import uuid
import os

import requests
import simplejson as json
import gnupg

CAMLIVERSION = 1
MAX_STAT_BLOB = 1000

log = logging.getLogger(__name__)

gpg = gnupg.GPG(gnupghome=os.path.expanduser('~/.config/camlistore'))


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
    return sha.hexdigest()


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

    def _conf_discovery(self):
        """ Perform a discovery to gather server configuration. """
        r = requests.get(self.server,
                         auth=self.auth,
                         headers={'Accept': 'text/x-camli-configuration'})
        r.raise_for_status()
        return r.json()

    def get_blob(self, blobref):
        """ Retrieve blob content. """
        log.debug('Fetching blobref:{0}'.format(blobref))
        blobref_url = urlparse.urljoin(self.url_blobRoot,
                                       'camli/{0}'.format(blobref))

        # TODO gerer le streaming
        r = requests.get(blobref_url, auth=self.auth)
        r.raise_for_status()
        try:
            res = r.json()
        except json.JSONDecodeError:
            res = r.content

        return res

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
        blobrefs = set(['sha1-{0}'.format(compute_hash(blob)) for blob in blobs])

        stat_res = self._stat(blobrefs)

        blobrefs_stat = set([s['blobRef'] for s in stat_res['stat']])

        blobrefs_missing = blobrefs - blobrefs_stat

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

        r = requests.post(stat_res['uploadUrl'], files=r_files, auth=self.auth)
        r.raise_for_status()

        return r.json()

    def new_permanode(self):
        permanode = {'camliVersion': CAMLIVERSION,
                     'camliSigner': 'sha1-5b35ff5a8baaae8ccac5c32338ce3795bbebc710',
                     'random': str(uuid.uuid4()),
                     'camliType': 'permanode'}
        return self.sign(permanode)

    def sign(self, data):
        r = requests.post(self.url_signHandler, data={'json': json.dumps(data)}, auth=self.auth)
        return r.json()
