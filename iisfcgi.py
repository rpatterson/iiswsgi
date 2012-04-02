"""Serve WSGI apps using IIS's modified FastCGI support."""

from filesocket import FileSocket

from flup.server import fcgi


class IISWSGIServer(fcgi.WSGIServer):

    def _setupSocket(self):
        return FileSocket()
        
