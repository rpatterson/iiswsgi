"""Serve WSGI apps using IIS's modified FastCGI support."""

import sys
import os
import logging

from struct import unpack
from select import error as select_error
from socket import error as socket_error
from errno import EBADF

from flup.server.fcgi_base import Record
from flup.server.fcgi_base import Connection
from flup.server.fcgi_base import (
    FCGI_HEADER_LEN, FCGI_Header, FCGI_NULL_REQUEST_ID,
    FCGI_ABORT_REQUEST, FCGI_BEGIN_REQUEST, FCGI_DATA, FCGI_PARAMS,
    FCGI_STDIN, FCGI_GET_VALUES,
    )
from flup.server import fcgi_single
from flup.server import singleserver

if __debug__:
    from flup.server.fcgi_base import _debug

from iiswsgi.filesocket import FileSocket

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')


class IISRecord(Record):

    def read(self, sock, header_len=None):
        """Read and decode a Record from a socket."""
        if header_len is not None:
            header, length = header_len
        else:
            try:
                header, length = self._recvall(sock, FCGI_HEADER_LEN)
            except:
                raise EOFError

        if length < FCGI_HEADER_LEN:
            raise EOFError

        self.version, self.type, self.requestId, self.contentLength, \
            self.paddingLength = unpack(FCGI_Header, header)

        if __debug__:
            _debug(9, 'read: fd = %d, type = %d, requestId = %d, '
                   'contentLength = %d' % (sock.fileno(), self.type,
                                           self.requestId, self.contentLength))

        if self.contentLength:
            try:
                self.contentData, length = self._recvall(sock,
                                                         self.contentLength)
            except:
                raise EOFError

            if length < self.contentLength:
                raise EOFError

        if self.paddingLength:
            try:
                self._recvall(sock, self.paddingLength)
            except:
                raise EOFError


class IISConnection(Connection):

    def __init__(self, sock, addr, init_header, server, timeout):
        super(IISConnection, self).__init__(sock, addr, server, timeout)
        self._init_header = init_header

    def run(self):
        """Begin processing data from the socket."""
        self._keepGoing = True
        init_header = self._init_header
        while self._keepGoing:
            try:
                self.process_input(init_header)
            except (EOFError, KeyboardInterrupt):
                break
            except (select_error, socket_error), e:
                if e[0] == EBADF:  # Socket was closed by Request.
                    break
                raise

            init_header = None

        self._cleanupSocket()

    def process_input(self, init_header=None):
        """Attempt to read a single Record from the socket and process it."""
        # Currently, any children Request threads notify this Connection
        # that it is no longer needed by closing the Connection's socket.
        # We need to put a timeout on select, otherwise we might get
        # stuck in it indefinitely... (I don't like this solution.)
        if not self._keepGoing:
            return
        rec = IISRecord()
        rec.read(self._sock, init_header)

        if rec.type == FCGI_GET_VALUES:
            self._do_get_values(rec)
        elif rec.type == FCGI_BEGIN_REQUEST:
            self._do_begin_request(rec)
        elif rec.type == FCGI_ABORT_REQUEST:
            self._do_abort_request(rec)
        elif rec.type == FCGI_PARAMS:
            self._do_params(rec)
        elif rec.type == FCGI_STDIN:
            self._do_stdin(rec)
        elif rec.type == FCGI_DATA:
            self._do_data(rec)
        elif rec.requestId == FCGI_NULL_REQUEST_ID:
            self._do_unknown_type(rec)
        else:
            # Need to complain about this.
            pass


class IISWSGIServer(fcgi_single.WSGIServer):

    def __init__(self, *args, **kw):
        """Use the modified Connection class that doesn't use `select()`"""
        super(IISWSGIServer, self).__init__(*args, **kw)
        self._jobClass = IISConnection

        # XXX conflict between single and connnection class on the
        # timeout argument
        self._jobArgs = self._jobArgs + (None,)

        self.fcgi_listensock_fileno = sys.stdin.fileno()

    def _setupSocket(self):
        try:
            import msvcrt
            msvcrt.setmode(self.fcgi_listensock_fileno, os.O_BINARY)
        except ImportError:
            logger.exception('msvcrt module not available')
        stdin = os.fdopen(self.fcgi_listensock_fileno, 'r', 0)
        stdout = os.fdopen(self.fcgi_listensock_fileno, 'w', 0)
        return FileSocket(stdin, stdout)

    def run(self):
        """Support IIS's non-compliant FCGI protocol."""
        self._web_server_addrs = os.environ.get('FCGI_WEB_SERVER_ADDRS')
        if self._web_server_addrs is not None:
            self._web_server_addrs = map(lambda x: x.strip(),
                                         self._web_server_addrs.split(','))

        sock = self._setupSocket()

        ret = self.run_single(sock)

        self._cleanupSocket(sock)
        self.shutdown()

        return ret

    def run_single(self, sock, timeout=1.0):
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
        singleserver.setCloseOnExec(sock)

        # Main loop.
        while self._keepGoing:
            r = sock.recv(FCGI_HEADER_LEN)

            if r:
                # Hand off to Connection.
                conn = self._jobClass(sock, '<IIS_FCGI>',
                                      (r, FCGI_HEADER_LEN),
                                      *self._jobArgs)
                conn.run()

            self._mainloopPeriodic()

        # Restore signal handlers.
        self._restoreSignalHandlers()

        # Return bool based on whether or not SIGHUP was received.
        return self._hupReceived

    def _sanitizeEnv(self, environ):
        """Make IIS provided environment sane for WSGI."""
        super(IISWSGIServer, self)._sanitizeEnv(environ)
        # IIS pases the path as the script name
        environ['SCRIPT_NAME'] = ''


response_template = """\
<html>
  <head>
    <title>Test IIS FastCGI WSGI Application</title>
  </head>
  <body>
    <h1>Test IIS FastCGI WSGI Application</h1>
{wsgi_environ_table}
  </body>
</html>
"""
table_template = """\
    <table border="1">
      <thead>
        <tr><th colspan="2">{title}</th></tr>
        <tr><th>Key</th><th>Value</th></tr>
      </thead>
      <tbody>
{body}
      </tbody>
    </table>
"""
row_template = """\
        <tr><th>{0}</th><td>{1}</td></tr>"""


def serve(app, handler=None, log_dir='%TEMP%'):
    if handler:
        # Include the time
        formatter = logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT)
        handler.setFormatter(formatter)

        # Find a better log file
        if 'IIS_USER_HOME' in os.environ:
            log_dir = os.path.join(os.environ['IIS_USER_HOME'], 'Logs')
        if 'IISEXPRESS_SITENAME' in os.environ:
            log_dir = os.path.join(log_dir, os.environ['IISEXPRESS_SITENAME'])
        if not os.path.exists(log_dir):
            # Directory doesn't exist until IIS logs the first request
            os.makedirs(log_dir)
        new_log = os.path.join(
            log_dir, os.path.basename(handler.stream.name))
        if new_log != handler.stream.name:
            new_handler = logging.FileHandler(new_log)
            new_handler.setFormatter(formatter)
            root.addHandler(new_handler)
            root.removeHandler(handler)

    server = IISWSGIServer(app)
    logger.info('Starting FCGI server with app %r' % app)
    try:
        server.run()
    except KeyboardInterrupt:
        # allow CTRL+C to shutdown
        pass
    except BaseException:
        logger.exception('server.run() raised an exception')
        raise
    return server


def server_runner(app, global_conf, *args, **kw):
    # Need to setup file logging as soon as possible as IIS seems to
    # swallow everything on startup, safest fallback possible
    handler = log_dir = None
    try:
        log_dir = os.environ.get('TEMP', os.sep)
        handler = logging.FileHandler(os.path.join(log_dir, 'iiswsgi.log'))
        root.addHandler(handler)
    except BaseException:
        # Better to keep running than to fail silently
        pass

    try:
        serve(app, *args, **kw)
    except BaseException, exc:
        logger.exception('Exception starting FCGI server:')
        # Don't print traceback twice when logging to stdout
        sys.exit(getattr(exc, 'code', 1))


def server_factory(global_conf, *args, **kw):
    def serve(app):
        server_runner(app, global_conf, *args, **kw)
    return serve


def test_app(environ, start_response,
             response_template=response_template, row_template=row_template):
    """Render the WSGI environment as an HTML table."""
    import pprint
    logger.debug('Recieved WSGI request with environ:\n{0}'.format(
        pprint.pformat(environ)))
    wsgi_rows = '\n'.join(
        (row_template.format(*item)) for item in environ.iteritems())
    response = response_template.format(
        wsgi_environ_table=table_template.format(
            title='WSGI Environment', body=wsgi_rows))
    status = '200 OK'
    headers = [('Content-Type', 'text/html'),
               ('Content-Length', str(len(response)))]
    logger.debug('Starting WSGI response: {0}\n{1}'.format(
        status, pprint.pformat(dict(headers))))
    start_response(status, headers)
    logger.debug('Returning WSGI response body')
    yield response
    logger.debug('Returning WSGI response finished')


def make_test_app(global_config):
    return test_app


if __name__ == '__main__':
    serve(test_app)
