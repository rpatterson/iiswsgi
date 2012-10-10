from distutils.core import setup

try:
    from iiswsgi.setup import cmdclass
    cmdclass  # pyflakes
except ImportError:
    cmdclass = dict()

version = '0.1'

setup(name='IISWSGISampleApp',
      version=version,
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
      url='http://github.com/rpatterson/iiswsgi',
      license='GPL version 3',
      # TODO get the custom commands to work without iiswsgi installed
      # in the python
      setup_requires=['setuptools-git',
                      'iiswsgi'],
      cmdclass=cmdclass,
      )
