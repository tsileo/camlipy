==========
 CamliPy
==========

Unofficial Python client for `Camlistore <http://camlistore.org/>`_.

This is a work in progress.

Camlipy try to behave exactly the same way that the original Camlistore Go client.
It means you can donwload file uploaded with ``camput`` or the web ui, and file uploaded with Camlipy works well with the ui and camget.


TODO
====

- Integration test
- Better schema
- Download big files uploaded with filewriter.
- Handle symlink/hard link (inode)
- Handle multi-claim in ``Claim``
- Streaming in ``Camlistore.get_blob``

License (MIT)
=============

Copyright (c) 2013 Thomas Sileo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
