==========
filesocket
==========

The `filesocket` module implements socket behavior backed by two
file-like object to and from which the actual data is read and
written.

Create a filesocket wrapper using the FileSocket class.

    >>> import sys
    >>> from filesocket import FileSocket
    >>> fsocket = FileSocket(None, sys.stdout)

By default, the socket uses `sys.stdin` for reading and `sys.stdout`
for writing.

    >>> fsocket.send('foo')
    foo3
    >>> fsocket.recv(0)
    ''

File sockets can also be given specific file objects to use.

    >>> from StringIO import StringIO
    >>> in_file = StringIO('bar')
    >>> out_file = StringIO()

    >>> fsocket = FileSocket(in_file, out_file)
    >>> fsocket.send('foo')
    3
    >>> out_file.getvalue()
    'foo'
    >>> fsocket.recv(3)
    'bar'

The socket can be shutdown.  The `how` argument controls whether the
`in_file`, `out_file` or both are closed.

    >>> in_file.closed
    False
    >>> out_file.closed
    False

    >>> import socket
    >>> fsocket.shutdown(socket.SHUT_RD)
    >>> in_file.closed
    True
    >>> out_file.closed
    False

    >>> fsocket.shutdown(socket.SHUT_WR)
    >>> in_file.closed
    True
    >>> out_file.closed
    True

    >>> in_file = StringIO('bar')
    >>> out_file = StringIO()
    >>> fsocket = FileSocket(in_file, out_file)
    >>> in_file.closed
    False
    >>> out_file.closed
    False
    >>> fsocket.shutdown(socket.SHUT_RDWR)
    >>> in_file.closed
    True
    >>> out_file.closed
    True

The `close()` method just deletes the references to the files but
doesn't necessarily close them.

    >>> in_file = StringIO('bar')
    >>> out_file = StringIO()
    >>> fsocket = FileSocket(in_file, out_file)
    >>> in_file.closed
    False
    >>> out_file.closed
    False
    >>> fsocket.in_file is in_file
    True
    >>> fsocket.out_file is out_file
    True
    >>> fsocket.close()
    >>> in_file.closed
    False
    >>> out_file.closed
    False
    >>> hasattr(fsocket, 'in_file')
    False
    >>> hasattr(fsocket, 'out_file')
    False

The `fileno()` method returns the file descriptor for the `in_file` by
default.

    >>> import tempfile
    >>> in_file = tempfile.TemporaryFile()
    >>> out_file = tempfile.TemporaryFile()
    >>> fsocket = FileSocket(in_file, out_file)
    >>> fsocket.fileno() == in_file.fileno()
    True
    >>> fsocket.fileno() == out_file.fileno()
    False

If the `use_out_fileno` argument is `True`, then the descriptor of
the `out_file` will be returned instead.

    >>> fsocket = FileSocket(in_file, out_file, use_out_fileno=True)
    >>> fsocket.fileno() == in_file.fileno()
    False
    >>> fsocket.fileno() == out_file.fileno()
    True

The `fileno` method is only available if the specified file has a
`fileno` attribute itself.

    >>> in_file = StringIO('bar')
    >>> out_file = StringIO()

    >>> fsocket = FileSocket(in_file, out_file)
    >>> hasattr(fsocket, 'fileno')
    False

    >>> fsocket = FileSocket(in_file, out_file, use_out_fileno=True)
    >>> hasattr(fsocket, 'fileno')
    False

As a slight optimization, underlying files' `read()` method is used
directly for the file socket's `recv()` and methods.

    >>> in_file = StringIO('bar')
    >>> out_file = StringIO()
    >>> fsocket = FileSocket(in_file, out_file)

    >>> fsocket.recv.im_func is in_file.read.im_func
    True

    >>> fsocket.recv(3)
    'bar'

`FileSocket`s cannot support the `flags` argument to `recv`.

    >>> fsocket.recv(3, 0)
    Traceback (most recent call last):
    TypeError: read() takes at most 2 arguments (3 given)
    
