"""Serve WSGI apps using IIS's modified FastCGI support."""

import sys

from filesocket import FileSocket

from flup.server import threadedserver
from flup.server import fcgi_base
from flup.server import fcgi


class IISWSGIServer(fcgi.WSGIServer):

    def _setupSocket(self):
        return FileSocket()

    def run(self, sock, timeout=1.0):
        """
        The main loop. Pass a socket that is ready to accept() client
        connections. Return value will be True or False indiciating whether
        or not the loop was exited due to SIGHUP.
        """
        # Set up signal handlers.
        self._keepGoing = True
        self._hupReceived = False

        # Might need to revisit this?
        if not sys.platform.startswith('win'):
            self._installSignalHandlers()

        # Set close-on-exec
        threadedserver.setCloseOnExec(sock)
        
        # Main loop.
        while self._keepGoing:
            r = sock.recv(fcgi_base.FCGI_HEADER_LEN)

            if r:
                # Hand off to Connection.
                conn = self._jobClass(sock, '<IIS_FCGI>', *self._jobArgs)
                self._threadPool.addJob(conn, allowQueuing=False)

            self._mainloopPeriodic()

        # Restore signal handlers.
        if not sys.platform.startswith('win'):
            self._restoreSignalHandlers()

        # Return bool based on whether or not SIGHUP was received.
        return self._hupReceived
