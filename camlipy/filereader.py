# -*- coding: utf-8 -*-
import logging
import tempfile

from camlipy.schema import Schema
from camlipy.filewriter import Span

log = logging.getLogger(__name__)


class FileReader(object):
    def __init__(self, con, blob_ref):
        self.con = con
        self.blob_ref = blob_ref
        self.spans = None

    def load_spans(self):
        self.spans = self._load_spans(self.blob_ref)

    def _load_spans(self, blob_ref):
        spans = []
        parts = Schema(self.con, blob_ref).data['parts']
        for index, part in enumerate(parts):
            if 'bytesRef' in part:
                # The associated blobRef => the span
                blob_ref = parts[index + 1]
                parts.remove(blob_ref)
                # If a the blob ref is followed by a bytesRef,
                # it represents the same Span
                children = self._load_spans(part['bytesRef'])
                spans.append(Span(br=blob_ref['blobRef'],
                                  children=children))
            elif 'blobRef' in part:
                # If the blobRef is alone, just append it
                spans.append(Span(br=part['blobRef'], size=part['size']))
            else:
                raise Exception('Part lost: {0}'.format(part))
        return spans

    def spans_to_br(self):
        return self._spans_to_br(self.spans)

    def _spans_to_br(self, spans):
        """ Debug methods. """
        for span in spans:
            if span.single_blob():
                yield span.br
            else:
                for sp in self._spans_to_br(span.children):
                    yield sp
                yield span.br

    def build(self):
        out = tempfile.TemporaryFile()
        for br in self.spans_to_br():
            blob = self.con.get_blob(br)
            out.write(blob.read())
        out.seek(0)
        return out

    def build_old(self):
        out = tempfile.TemporaryFile()
        for br in self.spans_to_br():
            blob = self.con.get_blob(br)
            while 1:
                buf = blob.read(4096)
                if buf:
                    out.write(buf)
                else:
                    break
        out.seek(0)
        return out
