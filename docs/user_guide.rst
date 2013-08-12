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

	c.put_blobs(['my data', open('myfile', 'rb')])

Files
-----

Directories
-----------

Operations on permanode
-----------------------
