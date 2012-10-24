import os
import logging

from distutils import core

from setuptools import setup

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

        from pyramid.scripts import pcreate
        argv = ['pcreate', '-s', scaffold, '__pyramid_project__']
        logger.info('Creating Pyramid project: {0}'.format(' '.join(argv)))
        pcreate.main(argv, quiet=(self.verbose == 0))

        cwd = os.getcwd()
        logger.info(
            'Installing __pyramid_project__ project for development')
        os.chdir('__pyramid_project__')
        try:
            return core.run_setup('setup.py', script_args=['develop'])
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
      install_requires=['iiswsgi', 'pyramid'],
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['setuptools-git',
                      'iiswsgi'],
      cmdclass=dict(install_msdeploy=install_pyramid_msdeploy),
      )
