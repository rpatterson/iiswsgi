from setuptools import setup

version = '0.1'

setup(name='WSGISampleIISApp',
      version=version,
      title='IIS WSGI Sample App',
      description="""Sample app demonstrating the use of IISWSGI \
with Microsoft Web Deploy.""",
      classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        ],
      keywords='python IIS FastCGI WSGI',
      author='Ross Patterson',
      author_email='me@rpatterson.net',
      author_url='http://rpatterson.net',
      url='https://github.com/rpatterson/iiswsgi/tree/master/examples/sample.msdeploy',
      license='GPL version 3',
      license_url='http://www.gnu.org/licenses/gpl.txt',
      icon_url='http://www.python.org/community/logos/python-powered-h-100x130.png',
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['iiswsgi'],
      )
