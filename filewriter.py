# -*- coding: utf-8 -*-
MAX_BLOB_SIZE = 1 << 20
FIRST_CHUNK_SIZE = 256 << 10
TOO_SMALL_THRESHOLD = 64 << 10
"""
// bufioReaderSize is an explicit size for our bufio.Reader,
// so we don't rely on NewReader's implicit size.
// We care about the buffer size because it affects how far
// in advance we can detect EOF from an io.Reader that doesn't
// know its size. Detecting an EOF bufioReaderSize bytes early
// means we can plan for the final chunk.
bufioReaderSize = 32 << 10
"""
from rollsum import Rollsum

fh = open('', 'rb')
rs = Rollsum()

blob_size = 0
spans = []
n = 0
buf = ''

class Span(object):
    def __init__(self, _from, to, bits=None, children=None, itter=0):
        self._from = _from
        self.to = to
        self.bits = bits
        self.br = None
        self.children = children
        self.itter = itter

    def __repr__(self):
        return '<Span {0}children iter{1}>'.format(len(self.children), self.itter)

    def single_blob(self):
        return not len(self.children)

    def size(self):
        size = self.to - self._from
        for cs in self.children:
            size += cs['size']
        return size




def upload_last_span():
    global buf
    print len(buf)
    chunk = buf
    buf = ''
    br = 'sha1-{0}'.format(camlipy.compute_hash(chunk))
    spans[len(spans) -1].br = br
    print br, len(chunk)

itter = 0
last = 0
print spans
while 1:
    c = fh.read(1)
    buf += c
    n += 1
    blob_size += 1
    rs.roll(ord(c))

    on_split = rs.on_split()
    bits = 0
    if blob_size == MAX_BLOB_SIZE:
        bits = 20
    # check EOF
    elif on_split and n > FIRST_CHUNK_SIZE and blob_size > TOO_SMALL_THRESHOLD:
        bits = rs.bits()
    elif n == FIRST_CHUNK_SIZE:
        bits = 18
    else:
        continue

    print "YAH"
    blob_size = 0

    children  = []
    children_from = len(spans)
    print "ACTUAL", itter
    while children_from > 0 and spans[children_from - 1].bits < bits:
        print "TRANSFERED", spans[children_from - 1].itter
        children_from -= 1

    n_copy = len(spans) - children_from
    if n_copy:
        children = spans[children_from:]
        spans = spans[:children_from]
        print children

    spans.append(Span(last, n, bits, children, itter))
    last = n

    upload_last_span()

    if itter > 15:
        break
    itter += 1
    print itter

print n, spans
