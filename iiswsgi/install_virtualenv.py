"""Set up the virtualenv before installing dependencies."""

import sys
import os
import logging
import sysconfig

import distutils.sysconfig
from distutils import errors
from distutils import cmd

from iiswsgi import options

virtualenv_script = 'bootstrap-virtualenv.py'

logger = logging.getLogger('install_virtualenv')


class install_virtualenv(cmd.Command):
    description = __doc__ = __doc__

    user_options = [
        ('virtualenv-script=', 'v',
         "Use a virtualenv bootstrap script if present. [default: {0}]"
         .format(virtualenv_script))]

    def initialize_options(self):
        self.virtualenv_script = None
        self.logger = logger

    def finalize_options(self):
        if self.virtualenv_script is None:
            self.virtualenv_script = virtualenv_script
        options.ensure_verbosity(self)

    def run(self):
        self.setup_virtualenv()

    def setup_virtualenv(
        self, home_dir=os.curdir, bootstrap=None, **opts):
        """
        Set up a virtualenv in the `directory` with options.

        If a `bootstrap` file is provided or the `virtualenv_script`
        exists, it is run as a script with positional `args` inserted
        into `sys.argv`.  Otherwise, `virtualenv` is imported and
        `create_environment()` is called with any kwargs.

        Following the run of this command, dependencies can
        automatically be installed with the develop command.
        """
        if bootstrap is None and os.path.exists(self.virtualenv_script):
            bootstrap = self.virtualenv_script

        if bootstrap:
            virtualenv_globals = dict(__file__=bootstrap)
            execfile(bootstrap, virtualenv_globals)

            argv = [bootstrap]
            if self.verbose == 0:
                argv.append('--quiet')
            elif self.verbose == 2:
                argv.append('--verbose')
            for option, value in opts.iteritems():
                argv.extend(['--' + option, value])
            argv.append(home_dir)

            self.logger.info(
                'Setting up a isolated Python with bootstrap script: {0}'
                .format(' '.join(argv)))
            orig_argv = sys.argv[:]
            try:
                sys.argv[:] = argv
                virtualenv_globals['main']()
            finally:
                sys.argv[:] = orig_argv
        else:
            try:
                import virtualenv
            except ImportError:
                raise errors.DistutilsModuleError(
                    'The virtualenv module must be available if no virtualenv '
                    'bootstrap script is given: {0}'.format(bootstrap))
            self.logger.info(
                'Setting up a isolated Python with module: '
                '{0}.create_environment({1} {2})'.format(
                    virtualenv, repr(home_dir), ' '.join(
                        '{0}={1}'.format(item) for item in opts.items())))
            virtualenv.logger = virtualenv.Logger([(
                virtualenv.Logger.level_for_integer(2 - self.verbose),
                sys.stdout)])

            virtualenv.create_environment(home_dir, **opts)

        activate_this = os.path.join(
            sysconfig.get_path('scripts', vars=dict(base=home_dir)),
            'activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))

        # Reinitialize much of distutils since many of the command
        # objects have prefix related value stored locally
        reload(distutils.sysconfig)
        for command in self.distribution.command_obj.itervalues():
            finalized = command.finalized
            self.reinitialize_command(command)
            if finalized:
                command.ensure_finalized()


def has_virtualenv_bootstrap(self):
    cmd = self.distribution.get_command_obj('virtualenv')
    cmd.ensure_finalized()
    return os.path.exists(cmd.virtualenv_script)
