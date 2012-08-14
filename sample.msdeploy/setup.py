from distutils.core import setup

from iisfcgi import MSDeployBuild

version = '0.1'

try:
    setup(name='IISFCGISampleApp',
          version=version,
          description="""Sample app demonstrating the use of IISFCGI \
    with Microsoft Web Deploy.""",
          classifiers=[
            "Environment :: Web Environment",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            ],
          keywords='python IIS FastCGI',
          author='Ross Patterson',
          author_email='me@rpatterson.net',
          url='http://github.com/rpatterson/iisfcgi',
          license='GPL version 3',
          cmdclass={'build': MSDeployBuild},
          )
except:
    import pdb, sys; pdb.post_mortem(sys.exc_info()[2])
    raise
