from setuptools import setup, find_packages
import os

setup(name='iiswsgi',
      version='0.2',
      title="WSGI on IIS",
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
      author_url='http://rpatterson.net',
      url='http://github.com/rpatterson/iiswsgi',
      license='GPL',
      license_url='http://www.gnu.org/licenses/gpl.txt',
      icon_url='http://www.python.org/community/logos/python-powered-h-100x130.png',
      packages=find_packages(),
      include_package_data=True,
      setup_requires=['setuptools-git'],
      install_requires=['flup>=1.0.3.dev_20110405'],
      extras_require=dict(config=['PasteDeploy'],
                          webpi=['zope.pagetemplate'],
                          bdist_webpi=['virtualenv']),
      bdist_msdeploy=['examples/sample.msdeploy',
                      'examples/pyramid.msdeploy'],
      scripts=['test.ini'],
      entry_points={
          'console_scripts':
          ['iiswsgi = iiswsgi.server:run',
           'iiswsgi_install = iiswsgi.install_msdeploy:install_console',
           'iiswsgi_install_fcgi_app = iiswsgi.fcgi:install_fcgi_app_console'],
          'paste.app_factory': ['test_app = iiswsgi.server:make_test_app'],
          "distutils.commands": [
            "install_virtualenv = "
              "iiswsgi.install_virtualenv:install_virtualenv",
            "build_msdeploy = iiswsgi.build_msdeploy:build_msdeploy",
            "install_msdeploy = iiswsgi.install_msdeploy:install_msdeploy",
            "bdist_msdeploy = iiswsgi.bdist_msdeploy:bdist_msdeploy",
            "build_webpi = iiswsgi.build_webpi:build_webpi",
            "bdist_webpi = iiswsgi.bdist_webpi:bdist_webpi",
            "clean_webpi = iiswsgi.clean_webpi:clean_webpi"],
          "distutils.setup_keywords": [
            "title = iiswsgi.options:assert_string",
            "author_url = iiswsgi.options:assert_string",
            "license_url = iiswsgi.options:assert_string",
            "display_url = iiswsgi.options:assert_string",
            "published = iiswsgi.options:assert_string",
            "icon_url = iiswsgi.options:assert_string",
            "screenshot_url = iiswsgi.options:assert_string",
            "discovery_file = iiswsgi.options:assert_string",
            "msdeploy_url_template = iiswsgi.options:assert_string",
            "bdist_msdeploy = iiswsgi.options:assert_editable_dists"]},
      )
