=======
iisfcgi
=======

The `iisfcgi` module implements a FastCGI to WSGI gateway that is
compatible with IIS's variation of the FastCGI protocol.  In
particular, it supports using STDIN_FILENO opened twice, once each
approximating the recv and send end of a socket as is specified in
FastCGI.

