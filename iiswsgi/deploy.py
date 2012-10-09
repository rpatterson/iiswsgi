import os
import subprocess
import copy
import optparse
import logging

from iiswsgi import setup_logger
from iiswsgi import parser

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')

appcmd_cmd_init = """\
{IIS_BIN}\AppCmd set config /section:system.webServer/fastCGI /+[{0}]"""
app_attr_defaults_init = dict(
    config='{APPL_PHYSICAL_PATH}\development.ini',
    fullPath='{SystemDrive}\Python27\python.exe',
    arguments='-u {APPL_PHYSICAL_PATH}\bin\iiswsgi-script.py -c {config}',
    activityTimeout='600', requestTimeout='600', idleTimeout='604800',
    monitorChangesTo='{config}', maxInstances=1)


def install_fcgi_app(appcmd_cmd=appcmd_cmd_init,
                     app_attr_defaults=app_attr_defaults_init,
                     **application_attrs):
    """
    Install an IIS FastCGI application.

    Since registering FastCGI applications doesn't work through
    `web.config`, this script will install the FastCGI app globally
    into IIS.

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


def install_fcgi_app_console(args=None):
    """
    Install an IIS FastCGI application.

    Adds a FastCGI Application to the IIS global config.  Many of the
    options are used as attributes for the <fastCgi><application>
    element installed.  See
    http://www.iis.net/ConfigReference/system.webServer/fastCgi/application
    for more details on the valid attributes and their affects.
    """
    root.setLevel(logging.INFO)
    setup_logger('IISWSGI Install FastCGI')
    options, args = install_fcgi_app_parser.parse_args(args=args)
    try:
        install_fcgi_app(**options.__dict__)
    except:
        logger.exception('Exception running %r' % install_fcgi_app)
        raise


install_fcgi_app_parser = optparse.OptionParser(
    description=install_fcgi_app_console.__doc__)
config_option = copy.copy(parser.get_option('--config'))
config_option.default = app_attr_defaults_init['config']
install_fcgi_app_parser.add_option(config_option)
install_fcgi_app_parser.add_option(
    "-m", "--monitor-changes", metavar="PATH",
    default=app_attr_defaults_init['monitorChangesTo'], help="""\
The path to a file which IIS will monitor and restart the FastCGI \
process when the file is modified. [default: %default]""")
install_fcgi_app_parser.add_option(
    "-n", "--max-instances", type="int",
    default=app_attr_defaults_init['maxInstances'], help="""\
The maximum number of FastCGI processes which IIS will launch.  For a \
production deployment, it's usually best to set this to \
%NUMBER_OF_PROCESSORS%. [default: %default]""")
install_fcgi_app_parser.add_option(
    "-t", "--activity-timeout", type="int",
    default=app_attr_defaults_init['activityTimeout'], help="""\
Specifies the maximum time, in seconds, that a FastCGI process can \
take to process. Acceptable values are in the range from 10 through \
3600.  [default: %default]""")
install_fcgi_app_parser.add_option(
    "-i", "--idle-timeout", type="int",
    default=app_attr_defaults_init['idleTimeout'], help="""\
Specifies the maximum amount of time, in seconds, that a FastCGI \
process can be idle before the process is shut down. Acceptable values \
are in the range from 10 through 604800.  [default: %default]""")
install_fcgi_app_parser.add_option(
    "-r", "--request-timeout", type="int",
    default=app_attr_defaults_init['requestTimeout'],
    help="""\
Specifies the maximum time, in seconds, that a FastCGI process request \
can take. Acceptable values are in the range from 10 through 604800. \
[default: %default]""")
install_fcgi_app_parser.add_option(
    "-f", "--full-path", metavar="EXECUTABLE",
    default=app_attr_defaults_init['fullPath'], help="""\
The path to the executable to be launched as the FastCGI process by \
IIS.  This is usually the path to the Python executable. [default: \
%default]""")
install_fcgi_app_parser.add_option(
    "-a", "--arguments", default=app_attr_defaults_init['arguments'],
    help="""\
The arguments to be given the executable when invoked as the FastCGI \
process by IIS.  [default: %default]""")
