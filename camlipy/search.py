# -*- coding: utf-8 -*-

""" Search API wrapper. """

__author__ = 'Thomas Sileo (thomas@trucsdedev.com)'

import logging
import urlparse

import requests

log = logging.getLogger(__name__)


class Search(object):
    """ Basic search wrapper around the API. """
    def __init__(self, con):
        self.con = con
        self.search_url = urlparse.urljoin(self.con.url_searchRoot,
                                           'camli/search/permanodeattr')
        self.search_params = {'signer': self.con.public_key_blob_ref}

    def search(self, value, attr='', fuzzy=False, max=100):
        """ Perform query with the same syntax as Camistore ui.

        Examples of queries:
        - tag:mytag
        - title:my_text_file.txt
        - my query

        """
        values = value.split(':')
        if len(values) == 2:
            value = values[1]
            attr = values[0]

        params = self.search_params.copy()
        params.update({'attr': attr, 'value': value,
                       'fuzzy': fuzzy, 'max': max})
        r = requests.get(self.search_url, params=params)

        return r.json()
