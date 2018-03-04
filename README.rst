=========
 CamliPy
=========

Unofficial Python client for `Camlistore <http://camlistore.org/>`_.

Camlipy try to behave exactly the same way that the original Camlistore Go client.
It means you can download file uploaded with ``camput`` or the web ui, and file uploaded with Camlipy works well with the ui and camget.


.. image:: https://img.shields.io/pypi/v/camlipy.svg
        :target: https://crate.io/packages/camlipy

.. image:: https://img.shields.io/pypi/dm/camlipy.svg
        :target: https://crate.io/packages/camlipy


Installation
============

	$ sudo pip install camlipy


TODO
====

- Handle symlink/hard link (inode)
- Sharing support
- Handle multi-claim in ``Claim``
- Check out Keep schema
- A read-only FUSE support?

Getting Started
===============

.. code-block:: python

	from camlipy import Camlistore

	c = Camlistore('http://localhost:3179')

	# Basic put/get
	my_blob = 'my blob'
	blob_ref = c.put_blob(my_blob)

	restored_blob = c.get_blob(blob_ref)

	# Retrieve a blob
	c.get_blob('sha1-0d31c43041edf303d9d136c918a1337abc9bde97')

	# Dump blobs without metadata
	c.put_blobs(['My Blob'])
	# or
	with open('/path/to/file', 'rb') as fh:
	    c.put_blobs([fh])

	# Put/restore files
	c.put_file('/path/to/myfile')
	# or
	c.put_file(fileobj=open('/path/to/myfile'), permanode=True)

	# Get as a fileobj (temporary file)
	c.get_file('sha1-0d31c43041edf303d9d136c918a1337abc9bde97')
	# Or get directly in a file
	with open('/path/to/restored_file', 'wb') as fh:
	    c.get_file('sha1-0d31c43041edf303d9d136c918a1337abc9bde97', fh)

	# Put/restore directories
	blob_ref = c.put_directory('/path/to/my/dir')
	c.get_directory(blob_ref)

	# Search blobs
	c.search('tag:mytag')


Working the command line tool
-----------------------------

Camlipy provide a basic command line utility, that let put/get blobs. It supports raw blob, file and directory.

.. code-block:: console

	$ camlipy config https://mycamlistorehost.com
	$ camlipy put /path/to/file
	$ camlipy put /this/path --permanode
	$ camlipy get sha1-0d31c43041edf303d9d136c918a1337abc9bde97
	$ camlipy get sha1-0d31c43041edf303d9d136c918a1337abc9bde97 --contents
	$ echo 'My Blob' | camlipy put -


Changelog
=========

0.2.0
-----

**September 23 2013**

- Ported rollsum to a C extension with swig, 30 seconds speedup for a 5MB files.
- Now uses ujson (faster) instead of simplejson.
- Skip file chunking for small files that fit in one chunk.
- New ``PlannedPermanode`` schema.


Development
===========

Tests runs with ``devcam server`` (Camlistore development server), see `HACKING <https://github.com/bradfitz/camlistore/blob/master/HACKING>`_ from Camlistore.

To execute the tests, just run:

	$ python setup.py test


Contribution
------------

Feel free to submit a pull request!


License (MIT)
=============

Copyright (c) 2013 Thomas Sileo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
