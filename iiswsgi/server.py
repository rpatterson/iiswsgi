"""Serve WSGI apps using IIS's modified FastCGI support."""

import sys
import os
import struct
import select
import socket
import errno
import argparse
import logging

from iiswsgi.filesocket import FileSocket
from iiswsgi import options

from flup.server import singleserver
from flup.server import fcgi_base
from flup.server import fcgi_single

if __debug__:
    from flup.server.fcgi_base import _debug

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')

# Global logging objects for manipulation once we know better places to log to.
# log to a file since FCGI is using stdin/stdout
handler = logging.FileHandler(
    '{IIS_USER_HOME}\\Logs\\{IISEXPRESS_SITENAME}\\iiswsgi.log'.format(
        **os.environ))
# Include the time
formatter = logging.Formatter('%(asctime)s:' + logging.BASIC_FORMAT)
handler.setFormatter(formatter)


class IISRecord(fcgi_base.Record):

    def read(self, sock, header_len=None):
        """Read and decode a Record from a socket."""
        if header_len is not None:
            header, length = header_len
        else:
            try:
                header, length = self._recvall(sock, fcgi_base.FCGI_HEADER_LEN)
            except:
                raise EOFError

        if length < fcgi_base.FCGI_HEADER_LEN:
            raise EOFError

        self.version, self.type, self.requestId, self.contentLength, \
            self.paddingLength = struct.unpack(fcgi_base.FCGI_Header, header)

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


class IISConnection(fcgi_base.Connection):

    def __init__(self, sock, addr, init_header, *args):
        super(IISConnection, self).__init__(sock, addr, *args)
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
            except (select.error, socket.error), e:
                if e[0] == errno.EBADF:  # Socket was closed by Request.
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

        if rec.type == fcgi_base.FCGI_GET_VALUES:
            self._do_get_values(rec)
        elif rec.type == fcgi_base.FCGI_BEGIN_REQUEST:
            self._do_begin_request(rec)
        elif rec.type == fcgi_base.FCGI_ABORT_REQUEST:
            self._do_abort_request(rec)
        elif rec.type == fcgi_base.FCGI_PARAMS:
            self._do_params(rec)
        elif rec.type == fcgi_base.FCGI_STDIN:
            self._do_stdin(rec)
        elif rec.type == fcgi_base.FCGI_DATA:
            self._do_data(rec)
        elif rec.requestId == fcgi_base.FCGI_NULL_REQUEST_ID:
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

    def _setupSocket(self):
        try:
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        except ImportError:
            logger.exception('msvcrt module not available')
        stdout = os.fdopen(sys.stdin.fileno(), 'w', 0)
        return FileSocket(None, stdout)

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
            r = sock.recv(fcgi_base.FCGI_HEADER_LEN)

            if r:
                # Hand off to Connection.
                conn = self._jobClass(sock, '<IIS_FCGI>',
                                      (r, fcgi_base.FCGI_HEADER_LEN),
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


def test_app(environ, start_response,
             response_template=response_template, row_template=row_template):
    """Render the WSGI environment as an HTML table."""
    wsgi_rows = '\n'.join(
        (row_template.format(*item)) for item in environ.iteritems())
    response = response_template.format(
        wsgi_environ_table=table_template.format(
            title='WSGI Environment', body=wsgi_rows))
    start_response('200 OK', [('Content-Type', 'text/html'),
                              ('Content-Length', str(len(response)))])
    yield response


def make_test_app(global_config):
    return test_app


def loadapp_option(value):
    from paste.deploy import loadapp
    config = os.path.abspath(value)
    logger.info('Loading WSGI app from config file %r' % config)
    app = loadapp('config:%s' % (config,))
    return app


def ep_app_option(value):
    setattr(parser.values, 'entry_point', value)
    import pkg_resources
    ep = pkg_resources.EntryPoint.parse('app=' + value)
    logger.info('Loading WSGI app from entry_point %r' % value)
    app = ep.load(require=False)
    return app


def run(args=None):
    """Run a WSGI app as an IIS FastCGI process."""
    # Setup logging in case something happens during option parsing
    root.addHandler(handler)

    try:
        args = parser.parse_args(args=args)
    except:
        logger.exception('Error parsing arguments.')
        raise

    server = IISWSGIServer(args.app)

    logger.info('Starting FCGI server with app %r' % args.app)
    try:
        server.run()
    except BaseException:
        logger.exception('server.run() raised an exception')
        raise


parser = argparse.ArgumentParser(description=run.__doc__,
                               parents=[options.parent_parser])
app_group = parser.add_mutually_exclusive_group()
app_group.add_argument(
    "-c", "--config", metavar="FILE", dest='app', type=loadapp_option,
    help="Load the  the WSGI app from paster config FILE.")
app_group.add_argument(
    "-e", "--entry-point", metavar="ENTRY_POINT", default=test_app,
    dest='app', type=ep_app_option,
    help="Load the WSGI app from pkg_resources.EntryPoint.parse(ENTRY_POINT)."
    "  The default is a simple test app that displays the WSGI environment."
    "  [default: iiswsgi:test_app]")


if __name__ == '__main__':
    run()
