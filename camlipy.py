# -*- coding: utf-8 -*-
import urlparse
import logging
import hashlib
import uuid
import os
from datetime import datetime

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
        self.url_searchRoot = urlparse.urljoin(self.server,
                                               self.conf['searchRoot'])

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

        r = requests.post(stat_res['uploadUrl'],
                          files=r_files,
                          auth=self.auth)
        r.raise_for_status()

        return r.json()

    def describe_blob(self, blobref):
        """ Return blob meta data. """
        describe = 'camli/search/describe?blobref={0}'.format(blobref)
        describe_url = urlparse.urljoin(self.url_searchRoot, describe)

        r = requests.get(describe_url, auth=self.auth)
        r.raise_for_status()

        return r.json()


class Schema(object):
    def __init__(self, con, blob_ref=None):
        self.con = con
        self.data = {'camliVersion': CAMLIVERSION}
        self.blob_ref = blob_ref

    def _sign(self, data):
        camli_signer = self.con.conf['signing']['publicKeyBlobRef']
        self.data.update({'camliSigner': camli_signer})
        r = requests.post(self.con.url_signHandler,
                          data={'json': json.dumps(data)},
                          auth=self.con.auth)
        r.raise_for_status()
        return r.text

    def sign(self):
        return self._sign(self.data)

    def json(self):
        return json.dumps(self.data)

    def describe(self):
        return self.con.describe_blob(self.blob_ref)


class Permanode(Schema):
    def __init__(self, con, blob_ref=None):
        super(Permanode, self).__init__(con, blob_ref)
        self.data.update({'random': str(uuid.uuid4()),
                          'camliType': 'permanode'})

    def save(self, title=None, tags=[]):
        blob_ref = None
        res = self.con.put_blobs([self.sign()])
        if len(res['received']) == 1:
            blob_ref = res['received'][0]['blobRef']

        if blob_ref:
            self.blob_ref = blob_ref

            if title is not None:
                Claim(self.con, blob_ref).set_attribute('title', title)
            for tag in tags:
                Claim(self.con, blob_ref).add_attribute('tag', tag)

        return blob_ref

    def claims(self):
        """ Return claims for the current permanode. """
        claim = 'camli/search/claims?permanode={0}'.format(self.blob_ref)
        claim_url = urlparse.urljoin(self.con.url_searchRoot, claim)

        r = requests.get(claim_url, auth=self.con.auth)
        r.raise_for_status()

        return r.json()


class Claim(Schema):
    def __init__(self, con, permanode_blobref):
        super(Claim, self).__init__(con)
        self.data.update({'claimDate': datetime.utcnow().isoformat() + 'Z',
                          'camliType': 'claim',
                          'permaNode': permanode_blobref})

    def set_attribute(self, attr, val):
        self.data.update({'claimType': 'set-attribute',
                          'attribute': attr,
                          'value': val})
        return self.con.put_blobs([self.sign()])

    def del_attribute(self, attr, val=None):
        self.data.update({'claimType': 'del-attribute',
                          'attribute': attr})
        if val is not None:
            self.data.update({'value': val})
        return self.con.put_blobs([self.sign()])

    def add_attribute(self, attr, val):
        self.data.update({'claimType': 'add-attribute',
                          'attribute': attr,
                          'value': val})
        return self.con.put_blobs([self.sign()])
