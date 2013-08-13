.. _command-line_tool:

===================
 Command-line tool
===================

Camlipy is bundled with a basic command-line tool, ``camlipy`` that let put/get blobs. It supports raw blob, file and directory.

.. code-block:: console

	$ camlipy config https://mycamlistorehost.com
	$ camlipy put /path/to/file
	$ camlipy put /this/path --permanode
	$ camlipy get sha1-0d31c43041edf303d9d136c918a1337abc9bde97
	$ camlipy get sha1-0d31c43041edf303d9d136c918a1337abc9bde97 --contents
	$ echo 'My Blob' | camlipy put -

