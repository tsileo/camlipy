from schema import Bytes
from camlipy import Camlistore, compute_hash

con = Camlistore('http://localhost:3179')


def span_to_bytes(spans):
    for span in spans:
        if span.single_blob():
            b = Bytes(con)
            b.add_blob_ref(span.br, int(span.to - span._from))
            yield span.br, b.json()
        else:
            for sp in span_to_bytes(span.children):
                yield sp
            yield span.br, span.chunk_cnt

def span2(spans, _root=True):
    """ bytesRef before the blobRef. """
    root = Bytes(con)
    for span in spans:
        if len(span.children) == 1 and span.children[0].single_blob():
            root.add_blob_ref(span.children[0].br, int(span.children[0].to - span.children[0]._from))
            span.children = []
        if len(span.children):
            children_size = 0
            for c in span.children:
                children_size += c.size()
            root.add_bytes_ref(span2(span.children, False), children_size)
        
        root.add_blob_ref(span.br, int(span.to - span._from))
    if not _root:
        print "NOROOT", root.json()
    if _root:
        print root.json()
    return 'sha1-{0}'.format(compute_hash(root.json()))