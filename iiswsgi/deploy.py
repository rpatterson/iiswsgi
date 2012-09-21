import os
import subprocess
import copy
import optparse
import logging

from iiswsgi import setup_logger
from iiswsgi import parser

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')

appcmd_cmd = """\
{IIS_BIN}\AppCmd set config /section:system.webServer/fastCGI /+[{0}]"""
app_attr_defaults = dict(
    config='{APPL_PHYSICAL_PATH}\development.ini',
    fullPath='{SystemDrive}\Python27\python.exe',
    arguments='-u {APPL_PHYSICAL_PATH}\bin\iiswsgi-script.py -c {config}',
    activityTimeout='600', requestTimeout='600', idleTimeout='604800',
    monitorChangesTo='{config}', maxInstances=1)

msdeploy_cmd = """\
msdeploy.exe -verb:sync -source:package='{InstallerFile}' -dest:auto"""


def deploy(appcmd_cmd=appcmd_cmd, app_attr_defaults=app_attr_defaults,
           msdeploy_cmd=msdeploy_cmd, **application_attrs):
    """
    Install an IIS WSGI application and deploy a Web Deploy package.

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
    setup_logger('IISWSGI Deploy')
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
