# -*- coding: utf-8 -*-
import logging


from camlipy.schema import Schema
from camlipy.filewriter import Span

log = logging.getLogger(__name__)


class FileReader(object):
    def __init__(self, con, blob_ref):
        self.con = con
        self.blob_ref = blob_ref

    def load_spans(self):
        return self._load_spans(self.blob_ref)

    def _load_spans(self, blob_ref):
        spans = []
        parts = Schema(self.con, blob_ref).data['parts']
        for index, part in enumerate(parts):
            if 'bytesRef' in part:
                log.debug('bytesRef in part')
                if index <= len(parts) and 'blobRef' in parts[index + 1]:
                    # If a the blob ref is followed by a bytesRef,
                    # it represents the same Span
                    children = self._load_spans(part['bytesRef'])
                    spans.append(Span(br=parts[index + 1]['blobRef'],
                                      children=children))
            elif 'blobRef' in part:
                if index >= 0 and not 'bytesRef' in parts[index - 1]:
                    # If the blobRef is alone, just append it
                    spans.append(Span(br=part['blobRef'], size=part['size']))
        return spans
