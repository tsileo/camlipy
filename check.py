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
    	# Don't create a bytesRef fi there is only one child,
    	# make it a blobRef instead.
        if len(span.children) == 1 and span.children[0].single_blob():
            children_size = int(span.children[0].to - span.children[0]._from)
            root.add_blob_ref(span.children[0].br,
                              children_size)
            span.children = []
        # Create a new bytesRef
        if len(span.children):
            children_size = 0
            for c in span.children:
                children_size += c.size()
            root.add_bytes_ref(span2(span.children, False), children_size)
        # Make a blobRef with the span data.
        root.add_blob_ref(span.br, int(span.to - span._from))
    return 'sha1-{0}'.format(compute_hash(root.json()))
