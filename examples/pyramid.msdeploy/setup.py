import os
import subprocess
import logging

from distutils.core import setup

from iiswsgi import options
from iiswsgi import install_msdeploy

version = '0.1'
logger = logging.getLogger('pyramid.iiswsgi')


class install_pyramid_msdeploy(install_msdeploy.install_msdeploy):

    def run(self):
        """Add a project from a scaffold before testing."""
        self.install()

        scaffold = '__pyramid_scaffold__'
        if scaffold == '__' + 'pyramid_scaffold' + '__':
            # Testing outside of WebPI
            scaffold = "starter"
        pcreate = options.get_script_path('pcreate', self.executable)
        args = [pcreate, '-s', scaffold, '__pyramid_project__']
        logger.info('Creating Pyramid project: {0}'.format(' '.join(args)))
        subprocess.check_call(args)

        cwd = os.getcwd()
        args = [self.executable, 'setup.py', 'develop']
        logger.info(
            'Installing __pyramid_project__ project for development: {0}'
            .format(' '.join(args)))
        os.chdir('__pyramid_project__')
        try:
            subprocess.check_call(args)
        finally:
            os.chdir(cwd)

        self.test()


setup(name='PyramidApp',
      version=version,
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
      url='http://www.pylonsproject.org/projects/pyramid/about',
      license='GPL version 3',
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['setuptools-git',
                      'iiswsgi'],
      cmdclass=dict(install_msdeploy=install_pyramid_msdeploy),
      )
