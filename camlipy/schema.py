""" Helper for creating/loading schemas. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import urlparse
import logging
import uuid
import os
import stat
from datetime import datetime

try:
    import grp
    import pwd
except ImportError:
    pass

import requests
import ujson as json

import camlipy

CAMLIVERSION = 1
MAX_STAT_BLOB = 1000

log = logging.getLogger(__name__)


def ts_to_camli_iso(ts):
    """ Convert timestamp to UTC iso datetime compatible with camlistore. """
    return datetime.utcfromtimestamp(ts).isoformat() + 'Z'


def camli_iso_to_ts(iso):
    try:
        dt = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        dt = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ')

    return int(dt.strftime('%s'))


def get_stat_info(path):
    """ Return OS stat info for the given path. """
    file_stat = os.stat(path)
    return {"unixOwnerId": file_stat.st_uid,
            "unixGroupId": file_stat.st_gid,
            "unixPermission": oct(stat.S_IMODE(file_stat.st_mode)),
            "unixGroup": grp.getgrgid(file_stat.st_gid).gr_name,
            "unixOwner": pwd.getpwuid(file_stat.st_uid).pw_name,
            "unixMtime": ts_to_camli_iso(file_stat.st_mtime),
            "unixCtime": ts_to_camli_iso(file_stat.st_ctime)}


def apply_stat_info(path, data):
    if 'unixMtime' in data:
        mtime_ts = camli_iso_to_ts(data['unixMtime'])
        os.utime(path, (mtime_ts, mtime_ts))
    if 'unixPermission' in data:
        os.chmod(path, int(data['unixPermission'], 8))
    if 'unixOwner' in data and 'unixOwnerId' in data and \
            'unixGroup' in data and 'unixGroupId' in data:
        unix_owner = -1
        if data['unixOwner'] == pwd.getpwuid(data['unixOwnerId']).pw_name:
            unix_owner = data['unixOwnerId']
        unix_group = -1
        if data['unixGroup'] == grp.getgrgid(data['unixGroupId']).gr_name:
            unix_group = data['unixGroupId']
        os.chown(path, unix_owner, unix_group)


class Schema(object):
    """ Basic Schema base class.

    Also used to load (and decoding?) existing schema.

    Args:
        con: Camlistore instance
        blob_ref: Optional blobRef if the blob already exists.

    """
    def __init__(self, con, blob_ref=None):
        self.con = con
        self.data = {'camliVersion': CAMLIVERSION}
        self.blob_ref = blob_ref

        # If it's an existing schema then we load it
        if blob_ref is not None:
            self.data = self.con.get_blob(self.blob_ref)

            if camlipy.DEBUG:
                log.debug('Loading existing schema: {0}'.format(self.data))

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
        _return = self._sign(self.data)
        if camlipy.DEBUG:
            log.debug('Signature result: {0}'.format(_return))
        return _return

    def json(self):
        """ Return json data. """
        return json.dumps(self.data)

    def describe(self):
        """ Call the API to describe the blob. """
        return self.con.describe_blob(self.blob_ref)

    def __getattr__(self, attr):
        return self.data.get(attr)

    def __repr__(self):
        return '<Schema {0}:{1}>'.format(self.__class__.__name__, self.blob_ref)


class Permanode(Schema):
    """ Permanode Schema with helpers for claims. """
    def __init__(self, con, permanode_blob_ref=None):
        super(Permanode, self).__init__(con, permanode_blob_ref)
        self.metadata = {}
        if permanode_blob_ref is None:
            self.data.update({'random': str(uuid.uuid4()),
                              'camliType': 'permanode'})
        else:
            self._fetch_metadata(permanode_blob_ref)

    def _fetch_metadata(self, br):
        self.metadata = self.con.describe_blob(br)
        assert self.metadata['camliType'] == 'permanode'

    def save(self, camli_content=None, camli_member=None, title=None, tags=[]):
        """ Create the permanode, takes optional title and tags. """
        blob_ref = self.con.put_blob(self.sign())

        if blob_ref:
            self.blob_ref = blob_ref
            if camli_content is not None:
                self.set_camli_content(camli_content)
            if camli_member is not None:
                self.set_camli_member(camli_member)
            if title is not None:
                Claim(self.con, blob_ref).set_attribute('title', title)
            for tag in tags:
                Claim(self.con, blob_ref).add_attribute('tag', tag)

        self._fetch_metadata(blob_ref)
        return blob_ref

    def set_camli_content(self, camli_content):
        """ Create a new camliContent claim. """
        self.set_attr('camliContent', camli_content)

    def get_camli_content(self):
        """ Fetch the current camliContent blobRef. """
        return self.get_attr('camliContent')

    def add_camli_member(self, camli_member):
        """ Append a new camliMember. """
        self.add_attr('camliMember', camli_member)

    def get_camli_member(self):
        """ Fetch the current camliMember blobRef. """
        return self.get_attr('camliMember')

    def get_attr(self, attr):
        """ Retrieve attr from indexer. """
        attr = self.metadata['permanode']['attr'].get(attr)
        if attr and len(attr) == 1:
            return attr[0]
        return attr

    def set_attr(self, attr, value):
        """ Create a claim to set attr to value. """
        Claim(self.con, self.blob_ref).set_attribute(attr, value)
        # Reset the meta-data
        self._fetch_metadata(self.blob_ref)

    def delete_attr(self, attr, value=None):
        """ Create a claim to delete attr/attr:value. """
        Claim(self.con, self.blob_ref).del_attribute(attr, value)
        # Reset the meta-data
        self._fetch_metadata(self.blob_ref)

    def add_attr(self, attr, value):
        """ Create a claim to add avlue to attr. """
        Claim(self.con, self.blob_ref).add_attribute(attr, value)
        # Reset the meta-data
        self._fetch_metadata(self.blob_ref)

    def claims(self):
        """ Return claims for the current permanode. """
        claim = 'camli/search/claims?permanode={0}'.format(self.blob_ref)
        claim_url = urlparse.urljoin(self.con.url_searchRoot, claim)

        r = requests.get(claim_url, auth=self.con.auth)
        r.raise_for_status()

        claims = []
        for claim in r.json()['claims']:
            try:
                claim['date'] = datetime.strptime(claim['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                claim['date'] = datetime.strptime(claim['date'], '%Y-%m-%dT%H:%M:%SZ')
            claims.append(claim)

        return sorted(claims, key=lambda c: c['date'], reverse=True)


class Claim(Schema):
    """ Claim schema with support for set/add/del attribute. """
    def __init__(self, con, permanode_blobref, claim_blobref=None):
        super(Claim, self).__init__(con, claim_blobref)
        self.permanode_blobref = permanode_blobref
        self.data.update({'claimDate': datetime.utcnow().isoformat() + 'Z',
                          'camliType': 'claim',
                          'permaNode': permanode_blobref})

    def set_attribute(self, attr, val):
        if camlipy.DEBUG:
            log.debug('Setting attribute {0}:{1} on permanode:{2}'.format(attr,
                                                                          val,
                                                                          self.permanode_blobref))

        self.data.update({'claimType': 'set-attribute',
                          'attribute': attr,
                          'value': val})
        return self.con.put_blob(self.sign())

    def del_attribute(self, attr, val=None):
        if camlipy.DEBUG:
            log.debug('Deleting attribute {0}:{1} on permanode:{2}'.format(attr,
                                                                           val,
                                                                           self.permanode_blobref))

        self.data.update({'claimType': 'del-attribute',
                          'attribute': attr})
        if val is not None:
            self.data.update({'value': val})
        return self.con.put_blob(self.sign())

    def add_attribute(self, attr, val):
        if camlipy.DEBUG:
            log.debug('Adding attribute {0}:{1} on permanode:{2}'.format(attr,
                                                                         val,
                                                                         self.permanode_blobref))

        self.data.update({'claimType': 'add-attribute',
                          'attribute': attr,
                          'value': val})
        return self.con.put_blob(self.sign())


class StaticSet(Schema):
    """ StaticSet schema. """
    def __init__(self, con, br=None):
        super(StaticSet, self).__init__(con, br)
        if br is None:
            self.data.update({'camliType': 'static-set',
                              'members': []})

    def save(self, members=[]):
        self.data.update({'members': members})

        blob_ref = self.con.put_blob(self.json())

        if blob_ref:
            self.blob_ref = blob_ref

        return self.blob_ref

    def update(self, members=[]):
        """ Update a static-set by creating a new one. """
        if self.blob_ref:
            new_members = list(self.members)
            new_members.extend(members)
            self.blob_ref = self.save(new_members)
            return self.blob_ref
        else:
            self.blob_ref = self.save(members)
            return self.blob_ref


class Bytes(Schema):
    """ Bytes schema. """
    def __init__(self, con, br=None):
        super(Bytes, self).__init__(con, br)
        if br is None:
            self.data.update({'camliType': 'bytes',
                              'parts': []})

    def save(self):
        blob_ref = self.con.put_blob(self.json())

        if blob_ref:
            self.blob_ref = blob_ref

        return self.blob_ref

    def _add_ref(self, ref_type, blob_ref, size):
        self.parts.append({ref_type: blob_ref, 'size': size})

    def add_blob_ref(self, blob_ref, size):
        self._add_ref('blobRef', blob_ref, size)

    def add_bytes_ref(self, blob_ref, size):
        self._add_ref('bytesRef', blob_ref, size)


class FileCommon(Schema):
    """ FileCommon schema. """
    def __init__(self, con, path=None, blob_ref=None):
        super(FileCommon, self).__init__(con, blob_ref)
        self.path = path
        if self.path:
            try:
                # Unix only
                self.data.update(get_stat_info(path))
            except:
                pass


class File(FileCommon):
    """ File schema. """
    def __init__(self, con, path=None, file_name=None, blob_ref=None):
        """ file_name is guessed from path if provided. """
        super(File, self).__init__(con, path, blob_ref)
        self.data.update({'camliType': 'file'})
        if path and os.path.isfile(path):
            self.data.update({'fileName': os.path.basename(path)})
        else:
            self.data.update({'fileName': file_name})

    def save(self, parts, permanode=False, tags=[]):
        self.data.update({'parts': parts})

        blob_ref = self.con.put_blob(self.json())

        self.blob_ref = blob_ref
        if permanode:
            permanode = Permanode(self.con).save(camli_content=self.blob_ref,
                                                 title=self.fileName,
                                                 tags=tags)
            return permanode
        return self.blob_ref


class Directory(FileCommon):
    """ Directory Schema """
    def __init__(self, con, path=None, blob_ref=None):
        super(Directory, self).__init__(con, path, blob_ref)
        self.data.update({'camliType': 'directory'})
        if path and os.path.isdir(path):
            dir_name = os.path.basename(os.path.normpath(path))
            self.data.update({'fileName': dir_name})

    def save(self, static_set_blobref, permanode=False, tags=[]):
        self.data.update({'entries': static_set_blobref})
        blob_ref = self.con.put_blob(self.json())

        if blob_ref:
            self.blob_ref = blob_ref
            if permanode:
                permanode = Permanode(self.con).save(camli_content=self.blob_ref,
                                                     title=self.fileName,
                                                     tags=tags)
                return permanode
        return self.blob_ref
