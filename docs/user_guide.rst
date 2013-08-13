.. _user_guide:

============
 User Guide
============

Getting started
===============

First, you need to create a ``Camlistore`` before interacting with the API.

.. code-block:: python

	from camlipy import Camlistore

	c = Camlistore('http://localhost:3179')

In the following examples, ``c`` is always an instance of ``Camlistore``.

Each blob is identified by its unique hash, its blob ref, like sha1-bd7d19bf8cf5fdbe955ac17541e215989f2a9ba7.

Raw blobs
---------

Here is how to put/get raw blobs, i.e. without any schema. You can either put a string, or a fileobj like object.

When you call get blob, you get a `SpooledTemporaryFile <http://docs.python.org/2/library/tempfile.html#tempfile.SpooledTemporaryFile>`_.

.. code-block:: python

	blob_ref = c.put_blob('my data')

	print c.get_blob(blob_ref).read()


You can also upload many blobs at once:

.. code-block:: python

	blob_ref = c.put_blobs(['my data', open('myfile', 'rb')])

Files
-----

Uploading files
~~~~~~~~~~~~~~~

You can either specify the path:

.. code-block:: python

	blob_ref = c.put_file('/path/to/file')

Or directly a fileobj like object:

.. code-block:: python

	with open('/path/to/file', 'rb') as fh:
	    blob_ref = c.put_file(fileobj=fh)

To create a permanode along with the file, just add ``permanode=True``, and optionally a list of ``tags``.

.. code-block:: python

	blob_ref = c.put_file('/path/to/file',
	                      permanode=True,
	                      tags=['list', 'of', 'tags'])

Restoring files
~~~~~~~~~~~~~~~

``get_file`` returns a `SpooledTemporaryFile <http://docs.python.org/2/library/tempfile.html#tempfile.SpooledTemporaryFile>`_ by default.

.. code-block:: python

	fileobj_res = c.get_file('sha1-bd7d19bf8cf5fdbe955ac17541e215989f2a9ba7')

But you can also pass a fileobj directly.

.. code-block:: python

	with open('/path/to/restored_file', 'wb') as fh:
	    fileobj_res = c.get_file('sha1-bd7d19bf8cf5fdbe955ac17541e215989f2a9ba7',
	                             fileobj=fh)


Directories
-----------

Upload directories
~~~~~~~~~~~~~~~~~~

Just specify the path:

.. code-block:: python

	blob_ref = c.put_directory('/path/to/dir')


Like when uploading a file, you create a permanode just by passing ``permanode=True``, and optionally a list of ``tags``.

.. code-block:: python

	blob_ref = c.put_directory('/path/to/dir',
	                           permanode=True,
	                           tags=['my tag'])

Restore directories
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

	c.get_directory('sha1-bd7d19bf8cf5fdbe955ac17541e215989f2a9ba7',
					'/path/to/restored_dir')


Exclude files/directories
~~~~~~~~~~~~~~~~~~~~~~~~~

Camlipy relies on `Dirtools <https://github.com/tsileo/dirtools>`_ to support gitignore like syntax for excluding files/directories, it will looks for a ``.exclude`` file at the root, check out Dirtools documentation for more informations.

Operations on permanode
-----------------------

You can also play directly with the ``Permanode`` object.
