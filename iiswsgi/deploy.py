import os
import sys
import subprocess
import optparse
import logging

from xml.dom import minidom

root = logging.getLogger()
logger = logging.getLogger('iiswsgi.deploy')

app_attr_defaults_init = dict(
    fullPath='%SystemDrive%\\Python27\\python.exe',
    arguments='-u %SystemDrive%\\Python27\\Scripts\\iiswsgi-script.py',
    activityTimeout='600', requestTimeout='600', idleTimeout='604800',
    monitorChangesTo='{SystemDrive}\\Scripts\\iiswsgi-script.py',
    maxInstances=1)


def get_web_config_apps(web_config):
    doc = minidom.parse(web_config)
    for fcgi in doc.getElementsByTagName("fastCgi"):
        for app in doc.getElementsByTagName("application"):
            yield dict((key, value) for key, value in app.attributes.items())


def install_fcgi_app(appcmd_exe=None,
                     web_config=None,
                     app_attr_defaults=app_attr_defaults_init,
                     **application_attrs):
    """
    Install an IIS FastCGI application.

    Since registering FastCGI applications doesn't work through
    `web.config`, this script will install the FastCGI app globally
    into IIS.  The attributes for the FCGI application may be given in
    a `web.config` file or through kwargs.

    If a `web.config` file is used, the `app_attr_defaults` will not
    be used but kwargs will still override `web.config` attributes.
    If a `web_config` argument is not passed, if the `os.getcwd()` or
    the directory in the `APPL_PHYSICAL_PATH` environment variable
    contains a `web.config` file, then that file will be used.  If the
    `web.config` file selected contains
    `configuration/system.webServer/fastCgi/application` elements,
    then IIS FCGI applications will be installed for all of them with
    attributes overridden by kwargs.  If the `web.config` file
    selected contains no such elements then the `app_attr_defaults`
    and kwargs will be used as described below.

    Pass `web_config=False` to disable using a `web.config` file and
    use `app_attr_defaults`.  In that case, kwargs override
    `app_attr_defaults`.

    http://www.iis.net/ConfigReference/system.webServer/fastCgi/application
    for more details on the valid attributes and their affects.
    """
    if appcmd_exe is None:
        appcmd_exe = '{WINDIR}\\System32\\inetsrv\\appcmd.exe'
        if 'IIS_BIN' in os.environ:
            # IIS Express
            # under WebPI at least, this is only set when using IIS Express
            appcmd_exe = '{PROGRAMFILES}\\IIS Express\\appcmd.exe'
    appcmd_exe = appcmd_exe.format(**os.environ)

    if web_config is None:
        # Search for default web.config
        if os.path.exists('web.config'):
            web_config = 'web.config'
        elif 'APPL_PHYSICAL_PATH' in os.environ:
            web_config = os.path.join(
                os.environ['APPL_PHYSICAL_PATH'], 'web.config')

    if web_config:
        apps = get_web_config_apps(web_config)
    else:
        apps = [app_attr_defaults.copy()]

    for app_attrs in apps:
        # Override with kwargs
        app_attrs.update(application_attrs)
        # format attributes for appcmd.exe
        appcmd_args = ",".join(
            "{0}='{1}'".format(*item) for item in app_attrs.iteritems())

        appcmd_cmd = (
            appcmd_exe, "set", "config", "-section:system.webServer/fastCgi",
            '/+[{0}]'.format(appcmd_args), '/commit:apphost')
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
    Run post-install tasks for a MS Web Deploy package.

    The post-install tasks run include:

    Set the `APPL_PHYSICAL_PATH` environment variable:

        If already defined, its value is taken as the location of the
        IIS application.  If not attempt to infer the appropriate
        directory.  Until such a time as Web Platform Installer or Web
        Deploy provide some way to identify the physical path of the
        `iisApp` being installed when the `runCommand` provider is
        used, we have to guess at the physical path.  If
        `IIS_SITES_HOME` is defined, all directories that are direct
        children of the `IIS_SITES_HOME` will be searched for a
        `iis_deploy.stamp` file.  If multiple directories are found
        with the stamp file, an error is raised.  Otherwise, in the
        case where one directory has the stamp file, it is set as the
        `APPL_PHYSICAL_PATH`.

        When installing to "IIS Express", the `IIS_SITES_HOME` environment
        variable should be available and the stamp file search should
        succeed to automatically find the right app for which to run
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
        physical path you will enter when installing via WebPI. Otherwise,
        when installing to full "IIS" you'll have to follow the steps for
        manually running the post-install deployment script after you get
        the error.

    Writing variable substitutions into `web.config`

        The `web.config` file is re-written substituting environment
        variables using the Python Format String Syntax:

        http://docs.python.org/library/string.html#formatstrings

        This is probably most useful to substitute APPL_PHYSICAL_PATH
        to make sure that each app gets unique IIS FastCGI application
        handlers that can each have their own parameters.

    Run the `iis_deploy.py` script

        Look for a `iis_deploy.py` script in `APPL_PHYSICAL_PATH`.  If
        it is found but `APPL_PHYSICAL_PATH` has no `iis_deploy.stamp`
        file, an error will be raised.  Otherwise the script is
        executed.  If it exits with a status code of `0`, then the
        `iis_deploy.stamp` file will be removed.  With any other
        non-zero status code, an error will be raised and the stamp
        file will be left in place.

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

        If you get an error indicating that the correct `iis_deploy.py`
        script could not be found or determined, you may manually run it
        after you recive the error as follows:

        * TODO provide the right variables and context before running
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

        if 'APPL_PHYSICAL_PATH' not in os.environ:
            os.environ['APPL_PHYSICAL_PATH'] = appl_physical_path

        # web.config variable substitution
        web_config_path = os.path.join(
            os.environ['APPL_PHYSICAL_PATH'], 'web.config')
        web_config = open(web_config_path).read()
        open(web_config_path, 'w').write(web_config.format(**os.environ))
        install_fcgi_app()

        script_path = os.path.join(appl_physical_path, self.script_filename)
        if os.path.exists(script_path):
           # Raises CalledProcessError if it failes
            # TODO output not being captured in the logs
            subprocess.check_call(
                [sys.executable, script_path] + sys.argv[1:], env=os.environ)

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
