"""
Run post-install tasks for a MS Web Deploy package:

1. set the `APPL_PHYSICAL_PATH` environment variable

2. write variable substitutions into `web.config`

3. install an IIS FastCGI application

4. set up a `virtualenv` isolated Python environment

5. install requirements with `pip` or `easy_install`

Where possible, automatic detection is used when deciding whether to
run a given task.
"""

import os
import sys
import subprocess
import argparse
import logging
import re

from xml.dom import minidom

from iiswsgi import options

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
    try:
        appcmd_exe = appcmd_exe.format(**os.environ)
    except KeyError:
        logger.exception('Could not find: {0}'.format(appcmd_exe))
        return

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
        if os.path.exists(appcmd_exe):
            subprocess.check_call(appcmd_cmd)
        else:
            logger.info('IIS AppCmd.exe does not exist: {0}'.format(
                appcmd_exe))


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


install_fcgi_app_parser = argparse.ArgumentParser(
    description=install_fcgi_app_console.__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
install_fcgi_app_parser.add_argument(
    "-m", "--monitor-changes", metavar="PATH",
    default=app_attr_defaults_init['monitorChangesTo'], help="""\
The path to a file which IIS will monitor and restart the FastCGI \
process when the file is modified.""")
install_fcgi_app_parser.add_argument(
    "-n", "--max-instances", type=int,
    default=app_attr_defaults_init['maxInstances'], help="""\
The maximum number of FastCGI processes which IIS will launch.  For a \
production deployment, it's usually best to set this to \
%%NUMBER_OF_PROCESSORS%%.""")
install_fcgi_app_parser.add_argument(
    "-t", "--activity-timeout", type=int,
    default=app_attr_defaults_init['activityTimeout'], help="""\
Specifies the maximum time, in seconds, that a FastCGI process can \
take to process. Acceptable values are in the range from 10 through \
3600.""")
install_fcgi_app_parser.add_argument(
    "-i", "--idle-timeout", type=int,
    default=app_attr_defaults_init['idleTimeout'], help="""\
Specifies the maximum amount of time, in seconds, that a FastCGI \
process can be idle before the process is shut down. Acceptable values \
are in the range from 10 through 604800.""")
install_fcgi_app_parser.add_argument(
    "-r", "--request-timeout", type=int,
    default=app_attr_defaults_init['requestTimeout'],
    help="""\
Specifies the maximum time, in seconds, that a FastCGI process request \
can take. Acceptable values are in the range from 10 through 604800. \
[default: %(default)s]""")
install_fcgi_app_parser.add_argument(
    "-f", "--full-path", metavar="EXECUTABLE",
    default=app_attr_defaults_init['fullPath'], help="""\
The path to the executable to be launched as the FastCGI process by \
IIS.  This is usually the path to the Python executable.""")
install_fcgi_app_parser.add_argument(
    "-a", "--arguments", default=app_attr_defaults_init['arguments'],
    help="""\
The arguments to be given the executable when invoked as the FastCGI \
process by IIS.""")


class Deployer(object):
    __doc__ = __doc__

    logger = logger
    app_name_pattern = '^{0}[0-9]*$'
    stamp_filename = 'iis_deploy.stamp'
    script_filename = 'iis_deploy.py'
    requirements_filename = 'requirements.txt'
    easy_install_filename = 'easy_install.txt'

    def __init__(self, app_name=None,
                 require_stamp=True, install_fcgi_app=True):
        self.app_name = app_name
        if app_name:
            self.app_name_pattern = re.compile(
                self.app_name_pattern.format(app_name))
        self.require_stamp = require_stamp
        self.install_fcgi_app = install_fcgi_app

        self.executable = sys.executable

    def __call__(self):
        """
        Run all deployment tasks and a custom script as appropriate.

        * `self.get_appl_physical_path()`: determine and set the
          APPL_PHYSICAL_PATH

        * `self.deploy()`: change to APPL_PHYSICAL_PATH and perform
          tasks as appropriate

        * `iis_deploy.py`: run the custom script if present
        """
        appl_physical_path = self.get_appl_physical_path()
        stamp_path = os.path.join(appl_physical_path, self.stamp_filename)
        if os.path.exists(stamp_path):
            # clean up the stamp file regardless, we tried
            os.remove(stamp_path)
        elif self.require_stamp:
            raise ValueError(
                'No IIS deploy stamp file found at {0}'.format(stamp_path))

        cwd = os.getcwd()
        try:
            self.logger.info('Changing to application directory {0}'.format(
                appl_physical_path))
            os.chdir(appl_physical_path)
            self.deploy()
            if os.path.exists(self.script_filename):
                self.run_custom_script()
        finally:
            os.chdir(cwd)

    def deploy(self, *requirements, **substitutions):
        """
        Perform all of the deployment tasks as appropriate.

        `self.write_web_config()`:

            Write variable substitutions into `web.config`.

        `install_fcgi_app()`:

            Install an IIS FastCGI application.

        `self.setup_virtualenv()`:

            If `APPL_PHYSICAL_PATH` has a `requirements.txt` and/or
            `easy_install.txt` file then a `virtualenv` will be setup
            to provide an isolated Python environment.

        `self.pip_install_requirements()`, `self.easy_install_requirements()`:

            Use `pip` or `easy_install` to install requirements into
            the `virtualenv`.
        """
        # TODO move to `setup.py install`?
        self.write_web_config(**substitutions)

        if self.install_fcgi_app:
            install_fcgi_app()

        # vritualenv and requirements
        if (os.path.exists(self.requirements_filename) or
            os.path.exists(self.easy_install_filename)):
            self.executable = self.setup_virtualenv()

            if os.path.exists(self.requirements_filename):
                self.pip_install_requirements()

            if os.path.exists(self.easy_install_filename):
                self.easy_install_requirements(*requirements)

    def write_web_config(self, **kw):
        """
        Write `web.config.in` to `web.config` substituting variables.

        Substitute environment variables overridden by the kwargs
        using the Python Format String Syntax:

        http://docs.python.org/library/string.html#formatstrings

        This is probably most useful to substitute APPL_PHYSICAL_PATH
        to make sure that each app gets unique IIS FastCGI application
        handlers that can each have their own parameters.  If your
        deployment requires that computed values be included in the
        substituted variables, then use the `--delegate` option and
        pass kwargs into `Deployer.deploy()`.
        """
        environ = os.environ.copy()
        environ.update(**kw)
        web_config = open('web.config.in').read()
        self.logger.info('Doing variable substitution in web.config')
        open('web.config', 'w').write(web_config.format(**environ))
        return environ

    def setup_virtualenv(self, directory='.', **opts):
        """
        Set up a virtualenv in the `directory` with options.
        """
        args = [options.get_script_path('virtualenv', self.executable)]
        for option, value in opts.iteritems():
            args += ['--' + option, value]
        args += [directory]
        self.logger.info(
            'Setting up a isolated Python with: {0}'.format(
                ' '.join(args)))
        subprocess.check_call(args, env=os.environ)
        return os.path.abspath(
            os.path.join(options.scripts_name, 'python' + options.script_ext))

    def pip_install_requirements(self, filename=requirements_filename):
        """Use pip to install requirements from the given file."""
        args = [os.path.abspath(options.get_script_path(
            'pip', self.executable)), 'install', '-r', filename]
        self.logger.info(
            'Installing dependencies with pip: {0}'.format(
                ' '.join(args)))
        subprocess.check_call(args, env=os.environ)

    def easy_install_requirements(
        self, filename=easy_install_filename, *requirements):
        """
        Use easy_install to install requirements.

        The requiremensts can be given as arguments or one per-line in
        the `filename`.
        """
        args = [os.path.abspath(
            options.get_script_path('easy_install', self.executable))]
        reqs = requirements
        if not reqs:
            reqs = [line.strip() for line in open(filename)]
        args.extend(reqs)
        self.logger.info(
            'Installing dependencies with easy_install: {0}'
            .format(' '.join(args)))
        subprocess.check_call(args, env=os.environ)

    def run_custom_script(self, *args, executable=None):
        """
        Run the `iis_deploy.py` script.

        Look for a `iis_deploy.py` script in `APPL_PHYSICAL_PATH`.  If
        it is found but `APPL_PHYSICAL_PATH` has no `iis_deploy.stamp`
        file, an error will be raised.  Otherwise the script is
        executed and the stamp file is removed.  The stamp file can be
        ignored if the `Deployer` has been instantiated with
        `Deployer(require_stamp=False)`.
        """
        if not os.path.exists(self.script_filename):
            raise ValueError('Custom deploy script does not exist: {0}'.format(
                self.script_filename))

        if executable is None:
            executable = self.executable
        args = [executable, self.script_filename] + args
        self.logger.info(
            'Running custom deploy script: {0}'.format(' '.join(args)))
        # Raises CalledProcessError if it failes
        subprocess.check_call(args, env=os.environ)

    def get_appl_physical_path(self):
        """
        Set the `APPL_PHYSICAL_PATH` environment variable

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
        `APPL_PHYSICAL_PATH`.  Then change to that directory before
        continuing with the rest of the steps.

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
        """
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
        if iis_sites_home is None:
            raise ValueError(
                'Neither the APPL_PHYSICAL_PATH nor the IIS_SITES_HOME '
                'environment variables are set.')
        elif not os.path.exists(iis_sites_home):
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
            if self._is_appl_physical_path(iis_sites_home, name)]
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

        if 'APPL_PHYSICAL_PATH' not in os.environ:
            os.environ['APPL_PHYSICAL_PATH'] = appl_physical_path
        return appl_physical_path

    def _is_appl_physical_path(self, iis_sites_home, name):
        if self.app_name:
            if self.app_name_pattern.match(name) is None:
                return False
        return (os.path.isdir(os.path.join(iis_sites_home, name))
                and os.path.exists(os.path.join(
                    iis_sites_home, name, self.stamp_filename)))


deploy_parser = argparse.ArgumentParser(add_help=False)
deploy_parser.add_argument(
    '-a', '--app-name', help="""\
When APPL_PHYSICAL_PATH is not set, narrow the search \
in IIS_SITES_HOME to apps with this name .""")
deploy_parser.add_argument(
    '-i', '--ignore-stamp', dest='require_stamp', action='store_false',
    help="""\
Run the deploy process even if the `iis_deploy.stamp` file is not present.  \
This can be usefule to manually re-run the deployment after an error that \
stopped a previous run has been addressed.""")
deploy_parser.add_argument(
    '-s', '--skip-fcgi-app-install', dest='install_fcgi_app',
    action='store_false', help="""\
Run the deploy process even if the `iis_deploy.stamp` file is not present.  \
This can be usefule to manually re-run the deployment after an error that \
stopped a previous run has been addressed.""")
deploy_parser.add_argument(
    '-d', '--delegate', action='store_true', help="""\
Only run the custom `iis_deploy.py` script, don't perform any of the default \
tasks.  When used it is up to the custom script to use `iiswsgi.deploy` to \
perform any needed tasks.  Useful if the app deployment process needs \
fine-grained control, such as passing computed arguments into the deployment \
tasks.""")
deploy_console_parser = argparse.ArgumentParser(
    description=Deployer.__doc__,
    parents=[options.parent_parser, deploy_parser],
    formatter_class=argparse.RawDescriptionHelpFormatter)


def deploy_console(args=None):
    logging.basicConfig()
    args = deploy_console_parser.parse_args(args=args)
    deployer = Deployer(
        args.app_name, args.require_stamp, args.install_fcgi_app)
    if args.delegate:
        deployer.run_custom_script(sys.argv[1:])
        return
    deployer()
