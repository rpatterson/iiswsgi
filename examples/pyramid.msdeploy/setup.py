import sys
import os
import logging
import subprocess
import sysconfig

from distutils import cmd

from setuptools import setup

version = '0.2'


class install_pyramid(cmd.Command):

    scaffold = 'starter'
    project = 'MyProject'

    user_options = [
        ('scaffold', 's',
         'The Pyramid scaffold to use to create the project. [default: {0}]'
         .format(scaffold)),
        ('project', 's',
         'The name of the project to create. [default: {0}]'
         .format(project))]

    def initialize_options(self):
        self.scaffold = None

    def finalize_options(self):
        """Handle unreplaced parameters when testing locally."""
        if not self.scaffold or self.scaffold == '__msdeploy_scaffold__':
            self.scaffold = 'starter'

    def run(self):
        """Add a project from a scaffold."""
        logger = logging.getLogger('pyramid.iiswsgi')
        cwd = os.getcwd()

        pcreate = os.path.join(
            sysconfig.get_path('scripts', vars=dict(base=cwd)),
            'pcreate' + sysconfig.get_config_var('EXE'))
        cmd = [pcreate, '-s', self.scaffold, self.project]
        logger.info('Creating Pyramid project: {0}'.format(' '.join(cmd)))
        subprocess.check_call(cmd)

        cmd = [sys.executable, 'setup.py', '-v', 'develop']
        logger.info(
            'Installing {0} project for development: {1}'.format(
                self.project, ' '.join(cmd)))
        try:
            os.chdir(self.project)
            subprocess.check_call(cmd)
        finally:
            os.chdir(cwd)


setup(name='PyramidIISApp',
      version=version,
      title="Pyramid Application",
      description="""Pyramid application project.""",
      classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        ],
      keywords='python Pyramid IIS FastCGI WSGI',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      author_url='http://rpatterson.net',
      url='http://www.pylonsproject.org/projects/pyramid/about',
      license='GPL version 3',
      license_url='http://www.gnu.org/licenses/gpl.txt',
      icon_url='http://www.pylonsproject.org/static/images/pyramid.png',
      install_requires=['iiswsgi', 'pyramid'],
      setup_requires=['iiswsgi'],
      install_msdeploy=['virtualenv'],
      cmdclass=dict(install_pyramid=install_pyramid),
      )
