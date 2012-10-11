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


def deploy():
    """
    Run arbitrary post-install tasks as defined in an `iis_deploy.py` script.

    The script is often used to build an isolated Python environment
    for the application (such as with virtualenv or buildout).  Since
    typically the package will be installed using a Web Platform
    Installer feed defining IISWSGI as a dependency, the script will
    be executed with the system Python.  As such, if some of your
    post-install deployment requires steps to be executed under the
    applications isolated environment, be sure that your
    `iis_deploy.py` script uses the Python `subprocess` module to
    invoke your isolated Python environment as appropriate once its
    been set up.

    Try to infer the appropriate `iis_deploy.py` script to run to do
    arbitrary post WebPI/MSDeploy installation tasks.  Until such a
    time as Web Platform Installer or Web Deploy provide some way to
    identify the physical path of the `iisApp` being installed when
    the `runCommand` provider is used, we have to guess at the
    physical path as follows:

    `APPL_PHYSICAL_PATH` environment variable

        If defined, its value is taken as the location of a single IIS
        application.  If a `iis_deploy.py` script is found as
        described below but no `iis_deploy.stamp` file is found, an
        error will be raised.  Otherwise the `iis_deploy.py` script
        will be run.  If there isn't such a script in that directory,
        an error will be raised.  None of the steps below will be done if
        this variable is set.

    `IIS_SITES_HOME` environment variable

        If defined, its value is taken as the location of a directory
        containing one or more IIS applications.  All directories that
        are direct children of the `IIS_SITES_HOME` will be searched
        for an `iis_deploy.py` script and a `iis_deploy.stamp` file.
        If multiple directories are found with both the script and the
        stamp file, an error is raised.  Otherwise, in the case where
        one directory has the script and stamp file, it is taken as
        the app directory and the `iis_deploy.py` script is run.

    `iis_deploy.py` script

        Once the `iis_deploy.py` script is found as described above,
        it is executed.  If it exits with a status code of `0`, then
        the `iis_deploy.stamp` file will be removed.  With any other
        non-zero status code, an error will be raised.

    When installing to "IIS Express", the `IIS_SITES_HOME` environment
    variable should be available and the script and stamp file search
    should succeed to automatically find the right app for which to run
    post-install script.  In the case of installing to full "IIS",
    however, neither the `APPL_PHYSICAL_PATH` nor the `IIS_SITES_HOME`
    environment variables are available and the post-install deploy
    script won't be run and WebPI will report an error.  The best way
    to workaround this limitation is to adopt a convention of putting
    all your IIS apps installed via WebPI in one directory and then
    set the `IIS_SITES_HOME` enviornment variable.  Then when
    installing a new IIS app be sure to give a physical path within
    that directory when prompted to by WebPI.  If that's not possible
    you can set the `APPL_PHYSICAL_PATH` environment variable to the
    physical path you will enter when installing via WebPI.
    Otherwise, when installing to full "IIS" you'll have to follow the
    steps for manually running the post-install deployment script
    after you get the error.

    If you get an error indicating that the correct `iis_deploy.py`
    script could not be found or determined, you may manually run it
    after you recive the error as follows:

    * TODO
    """
