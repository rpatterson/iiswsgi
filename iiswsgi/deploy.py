import os
import sys
import subprocess
import copy
import optparse
import logging

from iiswsgi import parser

root = logging.getLogger()
logger = logging.getLogger('iiswsgi.deploy')

appcmd_args_init = (
    "set", "config", "-section:system.webServer/fastCgi")
app_attr_defaults_init = dict(
    fullPath='{SystemDrive}\\Python27\\python.exe',
    arguments='-u {APPL_PHYSICAL_PATH}\\bin\\iiswsgi-script.py',
    activityTimeout='600', requestTimeout='600', idleTimeout='604800',
    monitorChangesTo='{APPL_PHYSICAL_PATH}\\bin\\iiswsgi-script.py',
    maxInstances=1)


def install_fcgi_app(appcmd_exe=None,
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
    # TODO read from web.config instead?
    app_attrs = app_attr_defaults.copy()
    app_attrs.update(application_attrs)
    appcmd_args = ",".join(
        "{0}='{1}'".format(*item) for item in app_attrs.iteritems())

    if appcmd_exe is None:
        appcmd_exe = '{WINDIR}\\System32\\inetsrv\\appcmd.exe'
        if 'IIS_BIN' in os.environ:
            # IIS Express, under WebPI at least, this is only set when
            # using IIS Express
            appcmd_exe = '{PROGRAMFILES}\\IIS Express\\appcmd.exe'
    appcmd_exe = appcmd_exe.format(**os.environ)

    appcmd_cmd = ((appcmd_exe,) +
                  appcmd_args_init +
                  ('/+[{0}]'.format(appcmd_args), '/commit:apphost'))
    logger.info('Installing IIS FastCGI application: {0!r}'.format(
        ' '.join(appcmd_cmd)))
    subprocess.check_call(appcmd_cmd)


def install_fcgi_app_console(args=None):
    """
    Install an IIS FastCGI application.

    Adds a FastCGI Application to the IIS global config.  Many of the
    options are used as attributes for the <fastCgi><application>
    element installed.  See
    http://www.iis.net/ConfigReference/system.webServer/fastCgi/application
    for more details on the valid attributes and their affects.
    """
    logging.basicConfig(level=logging.INFO)
    options, args = install_fcgi_app_parser.parse_args(args=args)
    install_fcgi_app(**options.__dict__)


install_fcgi_app_parser = optparse.OptionParser(
    description=install_fcgi_app_console.__doc__)
config_option = copy.copy(parser.get_option('--config'))
config_option.default = '{APPL_PHYSICAL_PATH}\\development.ini'
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


class Deployer(object):
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

    logger = logger
    stamp_filename = 'iis_deploy.stamp'
    script_filename = 'iis_deploy.py'

    def __call__(self):
        appl_physical_path = self.get_appl_physical_path()
        stamp_path = os.path.join(appl_physical_path, self.stamp_filename)
        if not os.path.exists(stamp_path):
            raise ValueError(
                'No IIS deploy stamp file found at {0}'.format(stamp_path))

        environ = os.environ.copy()
        if 'APPL_PHYSICAL_PATH' not in environ:
            environ['APPL_PHYSICAL_PATH'] = appl_physical_path

        script_path = os.path.join(appl_physical_path, self.script_filename)
        if os.path.exists(script_path):
            # Raises CalledProcessError if it failes
            # TODO output not being captured in the logs
            subprocess.check_call(
                [sys.executable, script_path] + sys.argv[1:], env=environ)
        else:
            # TODO Default deploy process
            raise NotImplementedError(
                'Default deploy process not defined yet')

        # Success, clean up the stamp file
        os.remove(stamp_path)

    def get_appl_physical_path(self):
        appl_physical_path = os.environ.get('APPL_PHYSICAL_PATH')
        if appl_physical_path is not None:
            if not os.path.exists(appl_physical_path):
                raise ValueError(
                    ('The APPL_PHYSICAL_PATH environment variable value is a '
                     'non-existent path: {0}').format(appl_physical_path))
            else:
                self.logger.info(
                    ('Found IIS app in APPL_PHYSICAL_PATH environment '
                     'variable at {0}').format(appl_physical_path))
                return appl_physical_path
        else:
            self.logger.info(
                'APPL_PHYSICAL_PATH environment variable not set')

        iis_sites_home = os.environ.get('IIS_SITES_HOME')
        if iis_sites_home is not None:
            if not os.path.exists(iis_sites_home):
                raise ValueError(
                    ('The IIS_SITES_HOME environment variable value is a '
                     'non-existent path: {0}').format(iis_sites_home))
            elif not os.path.isdir(iis_sites_home):
                raise ValueError(
                    ('The IIS_SITES_HOME environment variable value is '
                     'not a directory: {0}').format(iis_sites_home))

        self.logger.info(
            'Searching the directory in the IIS_SITES_HOME environment '
            'variable for the app to deploy')
        appl_physical_paths = [
            os.path.join(iis_sites_home, name)
            for name in os.listdir(iis_sites_home)
            if os.path.isdir(os.path.join(iis_sites_home, name))
            and os.path.exists(os.path.join(
                iis_sites_home, name, self.stamp_filename))]
        if not appl_physical_paths:
            raise ValueError(
                ('Found no {0} stamp file in any of the directories in the '
                 'IIS_SITES_HOME environment variable: {0}').format(
                    self.stamp_filename, iis_sites_home))
        elif len(appl_physical_paths) > 1:
            raise ValueError(
                ('Found multiple {0} stamp files in the directories in the '
                 'IIS_SITES_HOME environment variable: {0}').format(
                    self.stamp_filename, iis_sites_home))

        appl_physical_path = appl_physical_paths[0]
        self.logger.info(
            ('Found IIS app with a stamp file in just one of the directories '
             'in the IIS_SITES_HOME environment variable: {0}').format(
                    appl_physical_path))
        return appl_physical_path


def deploy_console():
    logging.basicConfig(level=logging.INFO)
    deployer = Deployer()
    deployer()
