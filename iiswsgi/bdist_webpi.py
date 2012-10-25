"""
Build IIS WSGI Web Deploy packages performing the following tasks:

1. build the Web Deploy Package

2. calculate the package size and sha1

3. update the size and sha1 in the Web Platform Installer feed

4. delete old Web Deploy packages from the Web Platform Installer cache

5. delete `iis_install.stamp` files from all installations of any of the
   given packages in `%USERPROFILE%\Documents\My Web Sites`

6. write the Web Platform Installer feed to `web-pi.xml`

7. delete copies of the feed from the Web Platform Installer cache
"""

import os
import subprocess
import shutil
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
from iiswsgi import fcgi
from iiswsgi import build_msdeploy
from iiswsgi import install_msdeploy
from iiswsgi import bdist_msdeploy

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
    webpi_installer_cache = None
    if 'LOCALAPPDATA' in os.environ:
        webpi_installer_cache = os.path.join(
            os.environ['LOCALAPPDATA'],
            'Microsoft', 'Web Platform Installer', 'installers')
    stamp_filename = options.stamp_filename
    feed_dir = None
    if 'LOCALAPPDATA' in os.environ:
        feed_dir = os.path.join(
            os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer')

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

    def run(self):
        for path in self.distribution.bdist_msdeploy:
            distribution = self.add_msdeploy(path)
            self.distributions.append(distribution)
            if not distribution.has_msdeploy_manifest:
                continue
            manifest = minidom.parse(os.path.join(path, 'Manifest.xml'))
            distribution.msdeploy_app_name = get_app_name(manifest)
            self.delete_installer_cache(distribution)
            self.delete_stamp_files(distribution)

        for name in self.distribution.extras_require['bdist_webpi']:
            distribution = self.add_dist(name)
            self.distributions.append(distribution)

        dist_feed = os.path.join(
            self.dist_dir,
            options.get_egg_name(self.distribution) + '.webpi.xml')
        self.write_feed(dist_feed)
        self.distribution.dist_files.append(('webpi', '', dist_feed))
        self.delete_feed_cache()

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

    def delete_installer_cache(self, distribution):
        if not self.webpi_installer_cache:
            logger.error('No WebPI installer cache')
            return
        installer_dir = os.path.join(self.webpi_installer_cache,
                                     distribution.msdeploy_app_name)
        if os.path.exists(installer_dir):
            logger.info('Removing the cached MSDeploy package: {0}'.format(
                installer_dir))
            shutil.rmtree(installer_dir)

    def delete_stamp_files(self, distribution):
        """Clean up likely stale stamp files."""
        for appl_physical_path in fcgi.list_stamp_paths(
            distribution.msdeploy_app_name, self.stamp_filename):
            stamp_file = os.path.join(
                appl_physical_path, self.stamp_filename)
            if os.path.exists(stamp_file):
                logger.info('Removing stale install stamp file: {0}'.format(
                    stamp_file))
                os.remove(stamp_file)

    def write_feed(self, dist_file, **kw):
        logger.info('Writing Web Platform Installer feed to {0}'.format(
            dist_file))

        view = core.run_setup('setup.py', stop_after='commandline')
        view.context = self
        view.dists = self.distributions
        view.now = datetime.datetime.now()

        open(dist_file, 'w').write(self.template(view=view, **kw))
        return dist_file

    def delete_feed_cache(self):
        if not self.feed_dir:
            logger.error('No WebPI feed directory')
            return
        for cached_feed_name in os.listdir(self.feed_dir):
            if not os.path.splitext(cached_feed_name)[1] == '.xml':
                # not a cached feed file
                continue

            # Compare feed/id elements
            cached_feed_path = os.path.join(self.feed_dir, cached_feed_name)
            cached_feed = minidom.parse(cached_feed_path).firstChild
            cached_ids = [node for node in cached_feed.childNodes
                          if node.nodeName == 'id']
            if cached_ids and (
                cached_ids[0].firstChild.data == self.distribution.get_url()):
                logger.info(
                    'Removing the Web Platform Installer cached feed at {0}'
                    .format(cached_feed_path))
                os.remove(cached_feed_path)
                break


cmdclass = dict(build_msdeploy=build_msdeploy.build_msdeploy,
                install_msdeploy=install_msdeploy.install_msdeploy,
                bdist_msdeploy=bdist_msdeploy.bdist_msdeploy,
                bdist_webpi=bdist_webpi)
