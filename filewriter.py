# -*- coding: utf-8 -*-
import logging
MAX_BLOB_SIZE = 1 << 20
FIRST_CHUNK_SIZE = 256 << 10
TOO_SMALL_THRESHOLD = 64 << 10
# Buffer to detect EOF in advance.
bufioReaderSize = 32 << 10

from rollsum import Rollsum
from schema import Bytes
import camlipy

log = logging.getLogger(__name__)

# TODO a buffer to detect EOF
# TODO handle EOF


class Span(object):
    """ Chunk metadata, used to create the tree,
    and compute chunk/bytesRef size. """
    def __init__(self, _from, to, bits=None, children=None, chunk_cnt=0):
        self._from = _from
        self.to = to
        self.bits = bits
        self.br = None
        self.children = children
        self.chunk_cnt = chunk_cnt

    def __repr__(self):
        return '<Span {0}children iter{1}>'.format(len(self.children),
                                                   self.chunk_cnt)

    def single_blob(self):
        return not len(self.children)

    def size(self):
        size = self.to - self._from
        for cs in self.children:
            size += cs['size']
        return size


class FileWriter(object):
    def __init__(self, path):
        self.path = path
        self.handler = open(self.path, 'rb')
        self.rs = Rollsum()
        self.blob_size = 0
        # Store Span the instance of the chunk
        self.spans = []
        # Total size
        self.n = 0
        # buffer to store the chunk
        self.buf = ''

    def upload_last_span(self):
        chunk = self.buf
        self.buf = ''
        blob_ref = 'sha1-{0}'.format(camlipy.compute_hash(chunk))
        self.spans[-1].br = blob_ref

    def chunk(self):
        chunk_cnt = 0
        last = 0
        while 1:
            c = self.handler.read(1)
            self.buf += c
            self.n += 1
            self.blob_size += 1
            self.rs.roll(ord(c))

            on_split = self.rs.on_split()
            bits = 0
            if self.blob_size == MAX_BLOB_SIZE:
                bits = 20
            # check EOF
            elif on_split and self.n > FIRST_CHUNK_SIZE and \
                    self.blob_size > TOO_SMALL_THRESHOLD:
                bits = self.rs.bits()
            # First chink => 262144 bytes
            elif self.n == FIRST_CHUNK_SIZE:
                bits = 18  # 1 << 18
                log
            else:
                continue

            self.blob_size = 0

            # The tricky part, take spans from the end that have
            # smaller bits score, slice them and make them children
            # of the node, that's how we end up with mixed blobRef/bytesRef,
            # And it keep them ordered by creating a kind of depth-first graph
            children = []
            children_from = len(self.spans)

            while children_from > 0 and \
                    self.spans[children_from - 1].bits < bits:
                children_from -= 1

            n_copy = len(self.spans) - children_from
            if n_copy:
                children = self.spans[children_from:]
                self.spans = self.spans[:children_from]

            self.spans.append(Span(last, self.n, bits, children, chunk_cnt))
            last = self.n

            self.upload_last_span()
            chunk_cnt += 1
            if chunk_cnt > 15:
                break

        return chunk_cnt
