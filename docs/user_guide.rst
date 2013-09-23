.. _user_guide:

============
 User Guide
============

Installation
============

	$ sudo pip install camlipy


Getting started
===============

First, you need to create a ``Camlistore`` before interacting with the API.

.. code-block:: python

	from camlipy import Camlistore

	c = Camlistore('http://localhost:3179')

If you have authentication enabled, just provide a tuple ``('username', 'password')``.

.. code-block:: python

	from camlipy import Camlistore

	c = Camlistore('http://localhost:3179', auth=('username', 'password'))


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

Schema
------

Schema attribute are stored in a dict under the data attribute.
You can retrieve data attribute like standard attribute, i.e. ``permanode.data['claimData']`` or ``permanode.claimData`` is the same.


Permanode
~~~~~~~~~

You can play directly with the ``Permanode`` object.

.. code-block:: python

	# Create a new permanode
	permanode = c.permanode()
	permanode.save(camli_content, title='My Title', tags=['list', 'of', 'tags'])
	# Or load an existing one
	permanode = c.permanode(permanode_blob_ref)

	# Get/set the camliContent blob ref
	blob_ref = permanode.get_camli_content()

	permanode.set_camli_content(new_camli_content)

	# Also handle camliMember
	# Get/set the camliMember blob ref
	blob_ref = permanode.get_camli_member()

	permanode.add_camli_member(new_camli_member)

	# You can also set/get any attribute
	permanode.set_attr('title', 'My New Title')
	permanode.get_attr('title')

	# Fetch the claims history
	claims = permanode.claims()

	# Fetch a permanode by title
	p = c.permanode_by_title('title')

Planned permanode
~~~~~~~~~~~~~~~~~

A planned permanode is like a standard permanode except it must have a meaningful ``key`` and ``claim_date``.

.. code-block:: python

	# Create a new planned permanode
	permanode = c.planned_permanode()
	permanode.save(camli_content, key='permanode_key', claim_date=datetime(2013, 9, 23, 13, 3, 10))
	# Or load an existing one
	permanode = c.planned_permanode(permanode_blob_ref)

	# Get/set the camliContent blob ref
	blob_ref = permanode.get_camli_content()


Static set
~~~~~~~~~~

You can also create static set easily.

.. code-block:: python

	static_set = c.static_set()
	static_set_br = static_set.save([br1, br2, br3])

Or you can use the ``add_to_static_set`` shortcut:

.. code-block:: python

	static_set_br = c.add_to_static_set([br1, br2, br3])

Load an existing static set:

.. code-block:: python

	static_set = c.static_set(static_set_br)
	members = static_set.members

You can create a new static while updating its members:

.. code-block:: python

	static_set = c.static_set(static_set_br)
	new_static_set_br = static_set.update([c.put_blob('my new blob')])
