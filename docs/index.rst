.. Camlipy documentation master file, created by
   sphinx-quickstart on Mon Aug 12 19:30:29 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=========
 Camlipy
=========

Unofficial Python client for `Camlistore <http://camlistore.org/>`_.

Camlipy try to behave exactly the same way that the original Camlistore Go client.
It means you can download file uploaded with ``camput`` or the web ui, and file uploaded with Camlipy works well with the ui and camget.

Quickstart
==========

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


User Guide
==========

.. toctree::
   :maxdepth: 3

   user_guide


Command-line tool
=================

.. toctree::
   :maxdepth: 3

   command-line_tool


API Documentation
=================

.. toctree::
   :maxdepth: 2

   api
