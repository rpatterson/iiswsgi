import sys
import os
import logging
import subprocess
import sysconfig

from setuptools import setup

from iiswsgi import install_msdeploy

version = '0.1'


class install_pyramid_msdeploy(install_msdeploy.install_msdeploy):
    # NameError under distutils.core.run_setup
    from iiswsgi import install_msdeploy

    scaffold = 'starter'
    project = 'MyProject'

    user_options = install_msdeploy.install_msdeploy.user_options + [
        ('scaffold', 's',
         'The Pyramid scaffold to use to create the project. [default: {0}]'
         .format(scaffold)),
        ('project', 's',
         'The name of the project to create. [default: {0}]'
         .format(project))]

    def finalize_options(self):
        """Handle unreplaced parameters when testing locally."""
        install_msdeploy.install_msdeploy.finalize_options(self)
        if self.scaffold == '__msdeploy_scaffold__':
            self.scaffold = 'starter'

    def run(self):
        """Add a project from a project before testing."""
        self.pre_install()

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

        self.post_install()


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
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['iiswsgi'],
      install_msdeploy=['virtualenv'],
      cmdclass=dict(install_msdeploy=install_pyramid_msdeploy),
      )
