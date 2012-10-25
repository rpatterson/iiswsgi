"""
Build IIS WSGI Web Platform Installer feed.

Calculates package sizes and sha1 hashes and renders a Web Platform
Installer feed from that data and distribution metadata.  The
distributions inclued are taken from setup.py keywords:

bdist_msdeploy

    A setup() kwargs containing a list of paths to distributions each
    containing built MSDeploy packages to include in the feed.

extras_require['bdist_webpi']

    A list of depdendencies to retrieve from the environment and for
    which to include entries in the feed.
"""

import os
import subprocess
import logging
import errno
import datetime
import sysconfig
import rfc822
import StringIO

from xml.dom import minidom

import pkg_resources
from distutils import core
from distutils import dist
from distutils import cmd
from distutils import errors

from iiswsgi import options
from iiswsgi import build_msdeploy
from iiswsgi import install_msdeploy
from iiswsgi import bdist_msdeploy
from iiswsgi import clean_webpi

logger = logging.getLogger('iiswsgi.webpi')


def get_app_name(manifest):
    """Return the <iisApp> name from a Manifest.xml DOM."""
    iisapps = manifest.getElementsByTagName('iisApp')
    if not iisapps:
        raise ValueError('No <iisApp> elements found in Manifest.xml')
    elif len(iisapps) > 1:
        raise ValueError('Multiple <iisApp> elements found in Manifest.xml')
    return iisapps[0].getAttribute('path')


class bdist_webpi(cmd.Command):
    __doc__ = __doc__

    user_options = [
        ('template=', 't',
         "The zope.pagetemplate file used to render the feed."),
        ('dist-dir=', 'd',
         "directory to put the source distribution archive(s) in "
         "[default: dist]")]

    pkg_info_attrs = {'summary': 'description',
                      'description': 'long_description',
                      'home-page': 'url',
                      'author-email': 'author_email'}

    msdeploy_url_template = (
        'http://pypi.python.org/packages/{VERSION}/'
        '{letter}/{name}/{msdeploy_file}')

    def initialize_options(self):
        self.template = None
        self.dist_dir = None

    def finalize_options(self):
        self.distributions = []
        self.ensure_filename('template')
        if self.template is None:
            self.template = 'WebPIList.pt'
        from zope.pagetemplate import pagetemplatefile
        self.template = pagetemplatefile.PageTemplateFile(self.template)
        if self.dist_dir is None:
            self.dist_dir = "dist"
        options.ensure_verbosity(self)

    def run(self):
        for path in self.distribution.bdist_msdeploy:
            distribution = self.add_msdeploy(path)
            self.distributions.append(distribution)
            if not distribution.has_msdeploy_manifest:
                continue
            manifest = minidom.parse(os.path.join(path, 'Manifest.xml'))
            distribution.msdeploy_app_name = get_app_name(manifest)

        for name in self.distribution.extras_require['bdist_webpi']:
            distribution = self.add_dist(name)
            self.distributions.append(distribution)

        dist_feed = os.path.join(
            self.dist_dir,
            options.get_egg_name(self.distribution) + '.webpi.xml')
        self.write_feed(dist_feed)
        self.distribution.dist_files.append(('webpi', '', dist_feed))

    def add_msdeploy(self, path, *args):
        cwd = os.getcwd()
        try:
            os.chdir(path)
            # TODO get dist without location?  From path?
            distribution = core.run_setup('setup.py', stop_after='commandline')

            distribution.build = distribution.get_command_obj('build')
            distribution.build.ensure_finalized()
            distribution.has_msdeploy_manifest = (
                'build_msdeploy' in distribution.build.get_sub_commands())
            if not distribution.has_msdeploy_manifest:
                raise errors.DistutilsFileError(
                    'No Web Deploy manifest found for {0}'.format(path))

            distribution.msdeploy_file = options.get_egg_name(
                distribution) + '.msdeploy.zip'
            distribution.msdeploy_package = os.path.abspath(
                os.path.join('dist', distribution.msdeploy_file))

            webpi_size = os.path.getsize(distribution.msdeploy_package)
            cmd = ['fciv', '-sha1', distribution.msdeploy_package]
            webpi_sha1 = ''
            try:
                webpi_sha1_output = subprocess.check_output(cmd)
            except OSError, error:
                if error.errno == errno.ENOENT:
                    logger.exception('Error getting SHA1: {0}'.format(
                        ' '.join(cmd)))
                else:
                    raise
            else:
                webpi_sha1 = webpi_sha1_output.rsplit(
                    '\r\n', 2)[-2].split(' ', 1)[0]
        finally:
            os.chdir(cwd)

        msdeploy_url_template = getattr(
            distribution, 'msdeploy_url_template', None)
        if not msdeploy_url_template:
            msdeploy_url_template = self.msdeploy_url_template
        kwargs = sysconfig.get_config_vars()
        kwargs.update(distribution.metadata.__dict__)
        distribution.msdeploy_url = msdeploy_url_template.format(
            letter=distribution.msdeploy_file[0].lower(),
            msdeploy_file=distribution.msdeploy_file, **kwargs)

        distribution.webpi_size = int(round(webpi_size / 1024.0))
        distribution.webpi_sha1 = webpi_sha1
        return distribution

    def add_dist(self, name):
        pkg_dist = pkg_resources.get_distribution(name)
        pkg_info = pkg_dist.get_metadata('PKG-INFO')
        msg = rfc822.Message(StringIO.StringIO(pkg_info))
        attrs = dict((self.pkg_info_attrs.get(key, key), value)
                     for key, value in msg.items() if value != 'UNKNOWN')
        distribution = dist.Distribution(attrs)
        return distribution

    def write_feed(self, dist_file, **kw):
        logger.info('Writing Web Platform Installer feed to {0}'.format(
            dist_file))

        view = core.run_setup('setup.py', stop_after='commandline')
        view.context = self
        view.dists = self.distributions
        view.now = datetime.datetime.now()

        open(dist_file, 'w').write(self.template(view=view, **kw))
        return dist_file


cmdclass = dict(build_msdeploy=build_msdeploy.build_msdeploy,
                install_msdeploy=install_msdeploy.install_msdeploy,
                bdist_msdeploy=bdist_msdeploy.bdist_msdeploy,
                bdist_webpi=bdist_webpi,
                clean_webpi=clean_webpi.clean_webpi)
