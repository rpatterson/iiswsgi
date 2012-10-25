from setuptools import setup

from iiswsgi import install_msdeploy

version = '0.1'


class install_pyramid_msdeploy(install_msdeploy.install_msdeploy):

    def run(self):
        """Add a project from a scaffold before testing."""
        self.install()

        import os
        import logging

        from distutils import core
        from distutils import errors

        logger = logging.getLogger('pyramid.iiswsgi')

        scaffold = '__pyramid_scaffold__'
        if scaffold == '__' + 'pyramid_scaffold' + '__':
            # Testing outside of WebPI
            scaffold = "starter"

        from pyramid.scripts import pcreate
        argv = ['pcreate', '-s', scaffold, '__pyramid_project__']
        logger.info('Creating Pyramid project: {0}'.format(' '.join(argv)))
        returncode = pcreate.main(argv, quiet=(self.verbose == 0))
        if returncode:
            raise errors.DistutilsError(
                "Pyramid's pcreate returned an error: {0}".format(returncode))

        cwd = os.getcwd()
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
      install_requires=['pyramid'],
      extras_require=dict(install_msdeploy=['virtualenv', 'iiswsgi']),
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['setuptools-git',
                      'iiswsgi'],
      cmdclass=dict(install_msdeploy=install_pyramid_msdeploy),
      )
