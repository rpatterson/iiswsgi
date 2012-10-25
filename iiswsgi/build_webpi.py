"""
Build all MSDeploy packages to be included in a WebPI feed.

The packages are defined in the bdist_msdeploy setup() kwarg
containing a list of paths to distributions each containing built
MSDeploy packages to include in the feed.
"""

import sys
import os
import logging
import subprocess

from distutils import cmd

from iiswsgi import options

setup_args = ['bdist_msdeploy']

logger = logging.getLogger('iiswsgi.webpi')


class build_webpi(cmd.Command):
    __doc__ = __doc__

    user_options = [
        ('setup-args=', 'a',
         "The arguments to pass to setup.py including commands. [default: {0}]"
         .format(setup_args))]

    stamp_filename = options.stamp_filename

    def initialize_options(self):
        self.setup_args = None

    def finalize_options(self):
        self.ensure_string_list('setup_args')
        if self.setup_args is None:
            self.setup_args = setup_args
            if self.verbose == 0:
                self.setup_args = ['-q'] + setup_args
            elif self.verbose == 2:
                self.setup_args = ['-v'] + setup_args
        options.ensure_verbosity(self)

    def run(self):
        cwd = os.getcwd()
        for path in self.distribution.bdist_msdeploy:
            cmd = [sys.executable, 'setup.py'] + self.setup_args
            logger.info('Running setup for {0}: {1}'.format(
                path, ' '.join(cmd)))
            try:
                os.chdir(path)
                subprocess.check_call(cmd)
            finally:
                os.chdir(cwd)
