from setuptools import setup
import os

setup(name='iisfcgi',
      version='0.1',
      description="Serve WSGI apps using IIS's modified FastCGI support.",
      long_description=(
          open(os.path.join(os.path.dirname(__file__),
                            "README.rst")).read() + '\n\n' +
          open(os.path.join("CHANGES.rst")).read()),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='fcgi iis windows',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      url='http://github.com/rpatterson/iisfcgi',
      license='GPL',
      install_requires=['flup'],
      extras_require=dict(config=['PasteDeploy']),
      entry_points={'console_scripts':
                        ['iisfcgi = iisfcgi:run',
                         'iisfcgi_deploy = iisfcgi:deploy_console'],
                    'paste.app_factory': ['test_app = iisfcgi:make_test_app']})
