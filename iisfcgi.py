"""Serve WSGI apps using IIS's modified FastCGI support."""

import sys
import os

from filesocket import FileSocket

from flup.server import threadedserver
from flup.server import fcgi_base
from flup.server import fcgi


class IISWSGIServer(fcgi.WSGIServer):

    def _setupSocket(self):
        return FileSocket()

    def run(self):
        """Support IIS's non-compliant FCGI protocol."""
        self._web_server_addrs = os.environ.get('FCGI_WEB_SERVER_ADDRS')
        if self._web_server_addrs is not None:
            self._web_server_addrs = map(lambda x: x.strip(),
                                         self._web_server_addrs.split(','))

        sock = self._setupSocket()

        ret = self.run_threaded(sock)

        self._cleanupSocket(sock)
        self.shutdown()

        return ret

    def run_threaded(self, sock, timeout=1.0):
        """
        Read from stdin in rather than using `select.select()` because
        Windows only supports `select.select()` on sockets not files.
        Also, pass the FileSocket instance in instead of accepting a
        connection and a child socket because IIS does all
        communication over stdin/stdout.
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
