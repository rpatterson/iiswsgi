"""Test a WSGI app prior to completing installation."""

import os
import subprocess
import logging
import sysconfig

from distutils.cmd import Command

from iiswsgi import options

root = logging.getLogger()
logger = logging.getLogger('iiswsgi.test')


class test_msdeploy(Command):
    description = __doc__ = __doc__

    config_file = 'development.ini'
    url = '/'
    paster = os.path.join(sysconfig.get_path('scripts'),
                          'paster' + sysconfig.get_config_var('EXE'))

    user_options = [
        ('config-file=', 'c',
         "Path to a PasteDeploy INI file defining a WSGI app."),
        ('url=', 'u',
         "The URL given to 'paster request'.  [default: {0}]".format(url)),
        ('paster=', 'p',
         "The path to the paster script.  [default: {0}]".format(paster))]

    logger = logger

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.ensure_filename('config_file')
        self.ensure_string('url')
        self.ensure_filename('paster')
        options.ensure_verbosity(self)

    def run(self):
        cmd = [self.paster, 'request', '-v', self.config_file, self.url]
        self.logger.info('Testing WSGI app: {0}'.format(' '.join(cmd)))
        subprocess.check_call(cmd)
