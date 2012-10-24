"""Distutils command for installing dependencies into a virtualenv."""

import sys
import os
import sysconfig

from distutils import errors

from setuptools.command import develop

virtualenv_script = 'bootstrap-virtualenv.py'


class develop_virtualenv(develop.develop):

    user_options = develop.develop.user_options + [
        ('virtualenv-script=', 'v',
         "Use a virtualenv bootstrap script if present. [default: {0}]"
         .format(virtualenv_script))]

    def initialize_options(self):
        develop.develop.initialize_options(self)
        self.virtualenv_script = virtualenv_script

    def run(self):
        """Set up the virtualenv before installing dependencies."""
        self.setup_virtualenv()
        develop.develop.run(self)

    def setup_virtualenv(
        self, home_dir=os.curdir, bootstrap=None, **opts):
        """
        Set up a virtualenv in the `directory` with options.

        If a `bootstrap` file is provided or the `virtualenv_script`
        exists, it is run as a script with positional `args` inserted
        into `sys.argv`.  Otherwise, `virtualenv` is imported and
        `create_environment()` is called with any kwargs.
        """
        if bootstrap is None and os.path.exists(self.virtualenv_script):
            bootstrap = self.virtualenv_script

        if bootstrap:
            argv = [bootstrap]
            for option, value in opts.iteritems():
                argv.extend(['--' + option, value])
            argv.append(home_dir)
            self.logger.info(
                'Setting up a isolated Python with bootstrap script: {0}'
                .format(' '.join(argv)))
            orig_argv = sys.argv[:]
            try:
                sys.argv[:] = argv
                bootstrap_globals = dict(__file__=bootstrap)
                execfile(bootstrap, bootstrap_globals)
                bootstrap_globals['main']()
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
                '{0}, {1}'.format(virtualenv, opts))
            virtualenv.create_environment(home_dir, **opts)

        activate_this = os.path.join(
            sysconfig.get_path('scripts', vars=dict(base=home_dir)),
            'activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))


def has_virtualenv_bootstrap(self):
    cmd = self.distribution.get_command_obj('virtualenv')
    cmd.ensure_finalized()
    return os.path.exists(cmd.virtualenv_script)
