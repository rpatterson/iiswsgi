from setuptools import setup
import os

setup(name='iiswsgi',
      version='0.2',
      description="Serve WSGI apps using IIS's modified FastCGI support.",
      long_description=(
          open(os.path.join(os.path.dirname(__file__),
                            "README.rst")).read() + '\n\n' +
          open(os.path.join("CHANGES.rst")).read()),
      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='fcgi iis windows',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='http://github.com/rpatterson/iiswsgi',
      license='GPL',
      include_package_data=True,
      dependency_links = [
          "http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20217/pywin32-217.win32-py2.7.exe"
          ],
      setup_requires=['setuptools-git'],
      install_requires=['flup',
                        'pywin32'],
      extras_require=dict(config=['PasteDeploy']),
      scripts=['test.ini'],
      entry_points={'console_scripts':
                        ['iiswsgi = iiswsgi:run',
                         'iiswsgi_deploy = iiswsgi:deploy_console'],
                    'paste.app_factory': ['test_app = iiswsgi:make_test_app']})
