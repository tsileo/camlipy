# -*- coding: utf-8 -*-
import urlparse
import logging
import hashlib
import uuid
import os
import stat
import grp
import pwd
from datetime import datetime

import requests
import simplejson as json

CAMLIVERSION = 1
MAX_STAT_BLOB = 1000

log = logging.getLogger(__name__)


def get_stat_info(path):
    file_stat = os.stat(path)
    return {"unixOwnerId": file_stat.st_uid,
            "unixGroupId": file_stat.st_gid,
            "unixPermission": oct(stat.S_IMODE(file_stat.st_mode)),
            "unixGroup": grp.getgrgid(file_stat.st_gid).gr_name,
            "unixOwner": pwd.getpwuid(file_stat.st_uid).pw_name,
            "unixMtime": datetime.utcfromtimestamp(file_stat.st_mtime).isoformat() + 'Z',
            "unixCtime": datetime.utcfromtimestamp(file_stat.st_ctime).isoformat() + 'Z'}


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

    def get_hash(self, blob):
        return 'sha1-{0}'.format(compute_hash(blob))

    def get_blob(self, blobref):
        """ Retrieve blob content. """
        log.debug('Fetching blobref:{0}'.format(blobref))
        blobref_url = urlparse.urljoin(self.url_blobRoot,
                                       'camli/{0}'.format(blobref))

        # TODO gerer le streaming
        # TODO handle already existing blobs
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

        return r.json()

    def describe_blob(self, blobref):
        """ Return blob meta data. """
        describe = 'camli/search/describe?blobref={0}'.format(blobref)
        describe_url = urlparse.urljoin(self.url_searchRoot, describe)

        r = requests.get(describe_url, auth=self.auth)
        r.raise_for_status()

        return r.json()


class Schema(object):
    """ Basic Schema base class.

    Args:
        con: Camlistore instance
        blob_ref: Optional blobRef if the blob already exists.

    """
    def __init__(self, con, blob_ref=None):
        self.con = con
        self.data = {'camliVersion': CAMLIVERSION}
        self.blob_ref = blob_ref

    def _sign(self, data):
        """ Call the signature server to sign json. """
        camli_signer = self.con.conf['signing']['publicKeyBlobRef']
        self.data.update({'camliSigner': camli_signer})
        r = requests.post(self.con.url_signHandler,
                          data={'json': json.dumps(data)},
                          auth=self.con.auth)
        r.raise_for_status()
        return r.text

    def sign(self):
        """ Return signed json. """
        return self._sign(self.data)

    def json(self):
        """ Return json data. """
        return json.dumps(self.data)

    def describe(self):
        """ Call the API to describe the blob. """
        return self.con.describe_blob(self.blob_ref)


class Permanode(Schema):
    """ Permanode Schema with helpers for claims. """
    def __init__(self, con, permanode_blob_ref=None):
        super(Permanode, self).__init__(con, permanode_blob_ref)
        self.data.update({'random': str(uuid.uuid4()),
                          'camliType': 'permanode'})

    def save(self, title=None, tags=[]):
        """ Create the permanode, takes optional title and tags. """
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
    """ Claim schema with support for set/add/del attribute. """
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


class StaticSet(Schema):
    """ StaticSet schema. """
    def __init__(self, con):
        super(StaticSet, self).__init__(con)
        self.data.update({'camliType': 'static-set',
                          'members': []})

    def save(self, members=[]):
        self.data.update({'members': members})

        res = self.con.put_blobs([self.json()])
        if len(res['received']) == 1:
            blob_ref = res['received'][0]['blobRef']

            if blob_ref:
                self.blob_ref = blob_ref

        return self.blob_ref


class FileCommon(Schema):
    """ FileCommon schema. """
    def __init__(self, con, path=None, blob_ref=None):
        super(FileCommon, self).__init__(con, blob_ref)
        self.path = path

        self.data.update(get_stat_info(path))


class File(FileCommon):
    """ File schema with helper for uploading small files. """
    def __init__(self, con, path=None, blob_ref=None):
        super(File, self).__init__(con, path, blob_ref)
        if path and os.path.isfile(path):
            self.data.update({'camliType': 'file',
                              'fileName': os.path.basename(path)})

    def save(self, permanode=False):
        if self.path and os.path.isfile(self.path):
            received = self.con.put_blobs([open(self.path, 'rb')])

            if received:
                received = received['received']
            # TODO handle if nothing is received because it already there
            self.data.update({'parts': received})

            res = self.con.put_blobs([self.json()])

            if len(res['received']) == 1:
                blob_ref = res['received'][0]['blobRef']
            else:
                blob_ref = self.con.get_hash(self.json())

            self.blob_ref = blob_ref

            if permanode:
                permanode = Permanode(self.con).save(self.data['fileName'])
                Claim(self.con, permanode).set_attribute('camliContent',
                                                         blob_ref)
                return permanode
        return self.blob_ref


class Directory(FileCommon):
    """ Directory Shema """
    def __init__(self, con, path=None, blob_ref=None):
        super(Directory, self).__init__(con, path, blob_ref)
        self.data.update({'camliType': 'directory'})
        if path and os.path.isdir(path):
            dir_name = os.path.basename(os.path.normpath(path))
            self.data.update({'fileName': dir_name})

    def _save(self, static_set_blobref, permanode=False):
        self.data.update({'entries': static_set_blobref})

        res = self.con.put_blobs([self.json()])

        if len(res['received']) == 1:
            blob_ref = res['received'][0]['blobRef']

            if blob_ref:
                self.blob_ref = blob_ref

                if permanode:
                    permanode = Permanode(self.con).save(self.data['fileName'])
                    Claim(self.con, permanode).set_attribute('camliContent',
                                                             blob_ref)
                    return permanode

        return self.blob_ref

    def save(self, files, permanode=False):
        files_blobrefs = [File(self.con, f).save() for f in files]
        static_set_blobref = StaticSet(self.con).save(files_blobrefs)
        return self._save(static_set_blobref, permanode)
