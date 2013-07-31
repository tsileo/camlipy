# -*- coding: utf-8 -*-
import logging
import os

import camlipy
from camlipy.rollsum import Rollsum
from camlipy.schema import Bytes


MAX_BLOB_SIZE = 1 << 20
FIRST_CHUNK_SIZE = 256 << 10
TOO_SMALL_THRESHOLD = 64 << 10
# Buffer to detect EOF in advance.
BUFFER_SIZE = 32 << 10

log = logging.getLogger(__name__)


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
        return '<Span children:{0}, iter:{1}, {2}:{3} {4}bits>'.format(len(self.children),
                                                                       self.chunk_cnt,
                                                                       self._from, self.to,
                                                                       self.bits)

    def single_blob(self):
        return not len(self.children)

    def size(self):
        # TODO faire une vrai size
        size = self.to - self._from
        for cs in self.children:
            size += cs.size()
        return size


class FileWriter(object):
    def __init__(self, path):
        self.path = path
        self.reader = open(self.path, 'rb')
        self.size = os.path.getsize(self.path)
        self.rs = Rollsum()
        self.blob_size = 0
        # Store Span the instance of the chunk
        self.spans = []
        # Total size
        self.n = 0
        # buffer to store the chunk
        self.buf = ''

    def upload_last_span(self):
        if camlipy.DEBUG:
            log.debug('Uploading last span: {0}'.format(self.span[-1]))

        chunk = self.buf
        self.buf = ''
        blob_ref = 'sha1-{0}'.format(camlipy.compute_hash(chunk))
        self.spans[-1].br = blob_ref

    def chunk(self):
        if camlipy.DEBUG:
            log.debug('Start chunking')
        chunk_cnt = 0
        last = 0
        while 1:
            c = self.reader.read(1)
            self.buf += c
            self.n += 1
            self.blob_size += 1
            self.rs.roll(ord(c))

            on_split = self.rs.on_split()
            bits = 0
            if self.blob_size == MAX_BLOB_SIZE:
                bits = 20
            # check EOF
            elif self.n + BUFFER_SIZE > self.size:
                continue
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

            current_span = Span(last, self.n, bits, children, chunk_cnt)

            if camlipy.DEBUG:
                log.debug('Current span: {0}'.format(current_span))

            self.spans.append(current_span)
            last = self.n

            self.upload_last_span()

            chunk_cnt += 1

        return chunk_cnt

    def chunk_to_schema(self):
        if camlipy.DEBUG:
            log.debug('Converting spans to Bytes Schema')


def traverse_tree(spans):
    for span in spans:
        if span.single_blob():
            yield span.chunk_cnt
        else:
            for sp in traverse_tree(span.children):
                yield sp
            yield span.chunk_cnt
