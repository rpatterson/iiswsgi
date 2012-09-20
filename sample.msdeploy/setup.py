from distutils.core import setup

import iiswsgi

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
      cmdclass={'build': iiswsgi.MSDeployBuild,
                'sdist': iiswsgi.MSDeploySDist},
      )
