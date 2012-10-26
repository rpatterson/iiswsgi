import os
import logging
import subprocess
import sysconfig

from distutils import core

from setuptools import setup

from iiswsgi import install_msdeploy

version = '0.1'


class install_pyramid_msdeploy(install_msdeploy.install_msdeploy):

    def run(self):
        """Add a project from a scaffold before testing."""
        self.install()

        logger = logging.getLogger('pyramid.iiswsgi')
        cwd = os.getcwd()

        scaffold = '__pyramid_scaffold__'
        if scaffold == '__' + 'pyramid_scaffold' + '__':
            # Testing outside of WebPI
            scaffold = "starter"

        pcreate = os.path.join(
            sysconfig.get_path('scripts', vars=dict(base=cwd)),
            'pcreate' + sysconfig.get_config_var('EXE'))
        cmd = [pcreate, '-s', scaffold, '__pyramid_project__']
        logger.info('Creating Pyramid project: {0}'.format(' '.join(cmd)))
        subprocess.check_call(cmd)

        logger.info(
            'Installing __pyramid_project__ project for development')
        try:
            os.chdir('__pyramid_project__')
            return core.run_setup('setup.py', script_args=['develop'])
        finally:
            os.chdir(cwd)

        self.test()


setup(name='PyramidApp',
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
      setup_requires=['setuptools-git',
                      'iiswsgi'],
      install_msdeploy=['virtualenv'],
      cmdclass=dict(install_msdeploy=install_pyramid_msdeploy),
      )
