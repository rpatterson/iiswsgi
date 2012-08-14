"""Serve WSGI apps using IIS's modified FastCGI support."""

import sys
import os
import struct
import select
import socket
import errno
import copy
import optparse
import subprocess

from distutils.command import build

import logging
from logging import handlers

from filesocket import FileSocket

from flup.server import singleserver
from flup.server import fcgi_base
from flup.server import fcgi_single

if __debug__:
    from flup.server.fcgi_base import _debug

root = logging.getLogger()
logger = logging.getLogger('iisfcgi')


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

        if __debug__: _debug(9, 'read: fd = %d, type = %d, requestId = %d, '
                             'contentLength = %d' %
                             (sock.fileno(), self.type, self.requestId,
                              self.contentLength))
        
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
                if e[0] == errno.EBADF: # Socket was closed by Request.
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
    <table border="1">
      <thead>
        <tr><th>Key</th><th>Value</th></tr>
      </thead>
      <tbody>
%s
      </tbody>
    </table>
  </body>
</html>
"""
row_template = """\
        <tr><th>%s</th><td>%s</td></tr>"""

def test_app(environ, start_response,
             response_template=response_template, row_template=row_template):
    """Render the WSGI environment as an HTML table."""
    rows = '\n'.join((row_template % item) for item in environ.iteritems())
    response = response_template % rows
    start_response('200 OK', [('Content-Type', 'text/html'),
                              ('Content-Length', str(len(response)))])
    yield response


def make_test_app(global_config):
    return test_app


def setup_logger(name):
    handler = handlers.NTEventLogHandler('IISFCGI - %s' % name)
    root.addHandler(handler)


def loadapp_option(option, opt, value, parser):
    from paste.deploy import loadapp
    config = os.path.abspath(value)
    setattr(parser.values, 'config', config)
    setup_logger(config)
    logger.info('Loading WSGI app from config file %r' % config)
    app = loadapp('config:%s'%(config,))
    setattr(parser.values, option.dest, app)


def ep_app_option(option, opt, value, parser):
    setattr(parser.values, 'entry_point', value)
    import pkg_resources
    ep = pkg_resources.EntryPoint.parse('app='+value)
    setup_logger(value)
    logger.info('Loading WSGI app from entry_point %r' % value)
    app = ep.load(require=False)
    setattr(parser.values, option.dest, app)


def run(args=None):
    """Run a WSGI app as an IIS FastCGI process."""
    root.setLevel(logging.INFO)

    options, args = parser.parse_args(args=args)
    if hasattr(options, 'config') and hasattr(options, 'entry_point'):
        parser.error("Use only one of '--config=%s' or '--entry-point=%s'"
                     % (options.config, options.entry_point))
    elif args:
        parser.error('Got unrecognized arugments: %r' % args)

    server = IISWSGIServer(options.app)

    logger.info('Starting FCGI server with app %r' % options.app)
    try:
        server.run()
    except BaseException:
        logger.exception('server.run() raised an exception')
        raise


parser = optparse.OptionParser(description=run.__doc__)
parser.add_option(
    "-c", "--config", metavar="FILE", type="string",
    dest='app', action="callback", callback=loadapp_option,
    help="Load the  the WSGI app from paster config FILE.")
parser.add_option(
    "-e", "--entry-point", metavar="ENTRY_POINT", default=test_app,
    type="string", dest='app', action="callback", callback=ep_app_option,
    help="Load the WSGI app from pkg_resources.EntryPoint.parse(ENTRY_POINT)."
    "  The default is a simple test app that displays the WSGI environment."
    "  [default: iisfcgi:test_app]")


class MSDeployBuild(build.build):
    """Build an MSDeploy zip packages for installation into IIS."""

    def initialize_options(self):
        """Be more discriminating about what to prune."""
        build.build.initialize_options(self)
        self.build_base = 'build/'


appcmd_cmd = "{IIS_BIN}\AppCmd set config /section:system.webServer/fastCGI /+[{0}]"
app_attr_defaults = dict(
    config='{APPL_PHYSICAL_PATH}\development.ini',
    fullPath='{SystemDrive}\Python27\python.exe',
    arguments='-u {APPL_PHYSICAL_PATH}\bin\iisfcgi-script.py -c {config}',
    activityTimeout='600', requestTimeout='600', idleTimeout='604800',
    monitorChangesTo='{config}', maxInstances=1)

msdeploy_cmd = "msdeploy.exe -verb:sync -source:package='{InstallerFile}' -dest:auto"

def deploy(appcmd_cmd=appcmd_cmd, app_attr_defaults=app_attr_defaults,
           msdeploy_cmd=msdeploy_cmd, **application_attrs):
    """
    Install an IIS FastCGI application and deploy a Web Deploy package.

    This is intended to be used as an alternat install command for a
    Web Deploy package such as in a `<installers><installer><cmdline>`
    element in a Web Platform Installer feed.  Since a Web Deploy
    package has no way internally to modify the global IIS config, but
    FastCGI apps need to have a global <fastCgi><application> element
    installled, this script will install the FastCGI app globally into
    IIS and then do what would have otherwise been done with the Web
    Deploy zip package.

    The kwargs will be used as attributes for the
    <fastCgi><application> element installed.  See
    http://www.iis.net/ConfigReference/system.webServer/fastCgi/application
    for more details on the valid attributes and their affects.
    """
    app_attrs = app_attr_defaults.copy()
    app_attrs.update(application_attrs)
    appcmd_cmd = appcmd_cmd.format(",".join(
        "{0}='{1}'".format(*item) for item in app_attrs.iteritems()),
                                   **os.environ)
    logger.info('Installing IIS FastCGI application: {0!r}'.format(appcmd_cmd))
    appcmd = subprocess.Popen(appcmd_cmd, shell=True)
    stdoutdata, stderrdata = appcmd.communicate(None)
    if stdoutdata:
        logger.info(stdoutdata)
    if stderrdata:
        logger.info(stderrdata)

    logger.info('Deploying Web Deploy package: {0!r}'.format(msdeploy_cmd))
    msdeploy = subprocess.Popen(msdeploy_cmd, shell=True)
    stdoutdata, stderrdata = msdeploy.communicate(None)
    if stdoutdata:
        logger.info(stdoutdata)
    if stderrdata:
        logger.info(stderrdata)


def deploy_console(args=None):
    """
    Install an IIS FastCGI application and deploy a Web Deploy package.

    Adds a FastCGI Application to the IIS global config and then
    installs a msdeploy zip file package.  Many of the options are
    used as attributes for the <fastCgi><application> element
    installed.  See
    http://www.iis.net/ConfigReference/system.webServer/fastCgi/application
    for more details on the valid attributes and their affects.
    """
    root.setLevel(logging.INFO)
    setup_logger('IISFCGI Deploy')
    options, args = deploy_parser.parse_args(args=args)
    try:
        deploy(**options.__dict__)
    except:
        logger.exception('Exception running %r' % deploy)
        raise


deploy_parser = optparse.OptionParser(description=deploy_console.__doc__)
config_option = copy.copy(parser.get_option('--config'))
config_option.default = app_attr_defaults['config']
deploy_parser.add_option(config_option)
deploy_parser.add_option(
    "-m", "--monitor-changes", metavar="PATH",
    default=app_attr_defaults['monitorChangesTo'], help="""\
The path to a file which IIS will monitor and restart the FastCGI \
process when the file is modified. [default: %default]""") 
deploy_parser.add_option(
    "-n", "--max-instances", type="int",
    default=app_attr_defaults['maxInstances'], help="""\
The maximum number of FastCGI processes which IIS will launch.  For a \
production deployment, it's usually best to set this to \
%NUMBER_OF_PROCESSORS%. [default: %default]""")
deploy_parser.add_option(
    "-t", "--activity-timeout", type="int",
    default=app_attr_defaults['activityTimeout'], help="""\
Specifies the maximum time, in seconds, that a FastCGI process can \
take to process. Acceptable values are in the range from 10 through \
3600.  [default: %default]""")
deploy_parser.add_option(
    "-i", "--idle-timeout", type="int",
    default=app_attr_defaults['idleTimeout'], help="""\
Specifies the maximum amount of time, in seconds, that a FastCGI \
process can be idle before the process is shut down. Acceptable values \
are in the range from 10 through 604800.  [default: %default]""")
deploy_parser.add_option(
    "-r", "--request-timeout", type="int",
    default=app_attr_defaults['requestTimeout'],
    help="""\
Specifies the maximum time, in seconds, that a FastCGI process request \
can take. Acceptable values are in the range from 10 through 604800. \
[default: %default]""")
deploy_parser.add_option(
    "-f", "--full-path", metavar="EXECUTABLE",
    default=app_attr_defaults['fullPath'], help="""\
The path to the executable to be launched as the FastCGI process by \
IIS.  This is usually the path to the Python executable. [default: \
%default]""") 
deploy_parser.add_option(
    "-a", "--arguments", default=app_attr_defaults['arguments'],
    help="""\
The arguments to be given the executable when invoked as the FastCGI \
process by IIS.  [default: %default]""") 


if __name__ == '__main__':
    run()
