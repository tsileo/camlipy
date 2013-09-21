# -*- coding: utf-8 -*-

""" Helper for uploading file, takes care of chunking file, create the file schema. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import os

import camlipy
from camlipy.rollsum_old import Rollsum
from camlipy.schema import Bytes, File


MAX_BLOB_SIZE = 1 << 20
FIRST_CHUNK_SIZE = 256 << 10
TOO_SMALL_THRESHOLD = 64 << 10
# Buffer to detect EOF in advance.
BUFFER_SIZE = 32 << 10

log = logging.getLogger(__name__)


class Span(object):
    """ Chunk metadata, used to create the tree,
    and compute chunk/bytesRef size. """
    def __init__(self, _from=0, to=0, bits=None, children=[], chunk_cnt=0, br=None, size=None):
        self._from = _from
        self.to = to
        self.bits = bits
        self.br = br
        self.children = children
        self.chunk_cnt = chunk_cnt
        self._size = size

    def __repr__(self):
        return '<Span children:{0}, iter:{1}, {2}:{3} {4}bits>'.format(len(self.children),
                                                                       self.chunk_cnt,
                                                                       self._from, self.to,
                                                                       self.bits)

    def single_blob(self):
        return not len(self.children)

    def size(self):
        if self._size:
            return self.size
        size = self.to - self._from
        for cs in self.children:
            size += cs.size()
        return size


class FileWriter(object):
    def __init__(self, con, path=None, fileobj=None):
        self.con = con
        self.path = path
        if path:
            self.reader = open(self.path, 'rb')
            self.size = os.path.getsize(self.path)
        else:
            self.reader = fileobj
            fileobj.seek(0, 2)
            self.size = fileobj.tell()
            fileobj.seek(0)

        self.rs = Rollsum()
        self.blob_size = 0
        # Store Span the instance of the chunk
        self.spans = []
        # Total size
        self.n = 0
        # buffer to store the chunk
        self.buf = ''
        self.buf_spans = {}

        # To generate the end report.
        self.cnt = {'skipped': 0,
                    'skipped_size': 0,
                    'uploaded': 0,
                    'uploaded_size': 0}

    def _upload_spans(self, force=False):
        """ Actually upload/put the blobs. """
        if len(self.buf_spans) == 10 or force:
            if camlipy.DEBUG:
                log.debug('Upload spans')
            resp = self.con.put_blobs(self.buf_spans.values())
            self.buf_spans = {}
            for rec in resp['received']:
                self.cnt['uploaded'] += 1
                self.cnt['uploaded_size'] += rec['size']
            for rec in resp['skipped']:
                self.cnt['skipped'] += 1
                self.cnt['skipped_size'] += rec['size']

    def upload_last_span(self):
        """ Empty the current blob buffer, prepare the blob,
        and add it to the spans buffer (they are uploaded once they
        are ten blobs in the buffer).
        """
        if camlipy.DEBUG:
            log.debug('Add span to buffer: {0}'.format(self.spans[-1]))

        chunk = self.buf
        self.buf = ''
        blob_ref = camlipy.compute_hash(chunk)
        self.spans[-1].br = blob_ref
        self.buf_spans[blob_ref] = chunk
        self._upload_spans()

    def chunk(self):
        """ Chunk the file with Rollsum to a tree of Spans. """
        if camlipy.DEBUG:
            log.debug('Start chunking, total size: {0}'.format(self.size))
        chunk_cnt = 0
        last = 0
        eof = False
        bits = 0
        while 1:
            c = self.reader.read(1)
            if c:
                self.buf += c
                self.n += 1
                self.blob_size += 1
                self.rs.roll(ord(c))
                on_split = self.rs.on_split()

                bits = 0
                if self.blob_size == MAX_BLOB_SIZE:
                    bits = 20
                # check EOF
                elif self.n > self.size - BUFFER_SIZE:
                    continue
                elif (on_split and self.n > FIRST_CHUNK_SIZE and
                        self.blob_size > TOO_SMALL_THRESHOLD):
                    bits = self.rs.bits()
                # First chink => 262144 bytes
                elif self.n == FIRST_CHUNK_SIZE:
                    bits = 18  # 1 << 18
                else:
                    continue

                self.blob_size = 0

                # The tricky part, take spans from the end that have
                # smaller bits score, slice them and make them children
                # of the node, that's how we end up with mixed blobRef/bytesRef,
                # And it keep them ordered by  creating a kind of depth-first graph
                children = []
                children_from = len(self.spans)

                while children_from > 0 and \
                        self.spans[children_from - 1].bits < bits:
                    children_from -= 1

                n_copy = len(self.spans) - children_from
                if n_copy:
                    children = self.spans[children_from:]
                    self.spans = self.spans[:children_from]
            else:
                eof = True
                children = []

            current_span = Span(last, self.n, bits, children, chunk_cnt)

            if camlipy.DEBUG:
                log.debug('Current span: {0}, last:{1}, n:{2}'.format(current_span, last, self.n))

            self.spans.append(current_span)
            last = self.n
            self.upload_last_span()

            chunk_cnt += 1

            if eof:
                log.debug('EOF')
                break

        # Upload left chunks
        assert self.n == self.size

        self._upload_spans(force=True)
        return chunk_cnt

    def bytes_writer(self, to_bytes=True):
        """ Transform the span in a blobRef/bytesRef tree.

        if `to_bytes' is True, returns a Bytes schema,
        if False, it returns the list of parts (ready to
        be injected in a File schema.)

        """
        return self._bytes_writer(self.spans, to_bytes=to_bytes)

    def _bytes_writer(self, spans, to_bytes=True):
        """ Actually transform the span in a blobRef/bytesRef tree.

        if `to_bytes' is True, returns a Bytes schema,
        if False, it returns the list of parts (ready to
        be injected in a File schema.)

        """
        schema = Bytes(self.con)
        if camlipy.DEBUG:
            log.debug('Starting spans: {0}'.format(spans))

        for span in spans:
            if camlipy.DEBUG:
                log.debug('Current span: {0}'.format(span))

            # Don't create a bytesRef if there is only one child,
            # make it a blobRef instead.
            if len(span.children) == 1 and span.children[0].single_blob():
                children_size = span.children[0].to - span.children[0]._from
                schema.add_blob_ref(span.children[0].br, children_size)
                span.children = []

                if camlipy.DEBUG:
                    log.debug('Transform this span to blobRef, new span: {0}'.format(span))

            # Create a new bytesRef if the span has children
            elif len(span.children):
                children_size = 0
                for c in span.children:
                    children_size += c.size()

                if camlipy.DEBUG:
                    log.debug('Embedding a bytesRef')
                schema.add_bytes_ref(self._bytes_writer(span.children, True), children_size)

            # Make a blobRef with the span data
            schema.add_blob_ref(span.br, span.to - span._from)
            log.info('#'*400)
            log.info(schema.json())

        if camlipy.DEBUG:
            log.debug('Resulting Bytes schema: {0}'.format(schema.json()))

        if to_bytes:
            self.con.put_blobs([schema.json()])

            return camlipy.compute_hash(schema.json())

        return schema.data['parts']

    def check_spans(self):
        """ Debug methods. """
        log.debug(self.spans)
        return self._check_spans(self.spans)

    def _check_spans(self, spans):
        """ Debug methods. """
        for span in spans:
            if span.single_blob():
                yield span.chunk_cnt
            else:
                for sp in self._check_spans(span.children):
                    yield sp
                yield span.chunk_cnt


def put_file(con, path=None, fileobj=None, permanode=False):
    """ Helper for uploading a file to a Camlistore server.

    Specify either a path, or a fileobj.

    Can also create a permanode.

    """
    if path is not None:
        fileobj = open(path, 'rb')

    file_writer = FileWriter(con, fileobj=fileobj)
    file_writer.chunk()
    parts = file_writer.bytes_writer(to_bytes=False)

    file_schema = File(con, path, file_name=fileobj.name)

    blob_ref = file_schema.save(parts, permanode=permanode)

    log.info('Uploaded: {uploaded} blobs, {uploaded_size}bytes. Skipped {skipped} skipped, {skipped_size}bytes.'.format(**file_writer.cnt))

    return blob_ref
