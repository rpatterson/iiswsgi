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

from xml.dom import minidom

from distutils import core
from distutils import cmd

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


class build_webpi(cmd.Command):
    __doc__ = __doc__

    user_options = [
        ('dists=', 'd', "The distributions to include in the feed."),
        ('feed=', 'f', "Write a WebPI feed to the file."),
        ('template=', 't',
         "The zope.pagetemplate file used to render the feed.")]

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
        self.dists = None
        self.feed = None
        self.feed_template = None

    def finalize_options(self):
        self.ensure_string_list('dists')
        self.distributions = []
        self.ensure_filename('feed_template')
        if self.feed_template is None:
            self.feed_template = 'WebPIList.pt'

    def run(self):
        for path in self.dists:
            dist = self.build_package(path)
            self.distributions.append(dist)
            manifest = minidom.parse(os.path.join(path, 'Manifest.xml'))
            dist.msdeploy_app_name = get_app_name(manifest)
            self.delete_installer_cache(dist)
            self.delete_stamp_files(dist)

        if self.feed is not None:
            self.write_feed()
            feed = minidom.parse(self.feed).firstChild
            self.delete_feed_cache(feed)

    def build_package(self, path, *args):
        cwd = os.getcwd()
        try:
            os.chdir(path)
            dist = core.run_setup('setup.py', stop_after='commandline')

            dist.build = dist.get_command_obj('build')
            dist.build.ensure_finalized()
            dist.has_msdeploy_manifest = (
                'build_msdeploy' in dist.build.get_sub_commands())

            dist.bdist_msdeploy = dist.build.get_finalized_command(
                'bdist_msdeploy')
            msdeploy_file = dist.bdist_msdeploy.get_msdeploy_name() + '.zip'
            if dist.has_msdeploy_manifest:
                dist.msdeploy_url = self.msdeploy_url_template.format(
                    VERSION=sysconfig.get_config_var('VERSION'),
                    letter=msdeploy_file[0], name=dist.get_name(),
                    msdeploy_file=msdeploy_file)

            dist.msdeploy_package = os.path.abspath(
                os.path.join('dist', msdeploy_file))

            webpi_size = os.path.getsize(dist.msdeploy_package)
            cmd = ['fciv', '-sha1', dist.msdeploy_package]
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
            os.chdir(self.cwd)

        dist.webpi_size = int(round(webpi_size / 1024.0))
        dist.webpi_sha1 = webpi_sha1
        return dist

    def delete_installer_cache(self, dist):
        if not self.webpi_installer_cache:
            logger.error('No WebPI installer cache')
            return
        installer_dir = os.path.join(self.webpi_installer_cache,
                                     dist.msdeploy_app_name)
        if os.path.exists(installer_dir):
            logger.info('Removing the cached MSDeploy package: {0}'.format(
                installer_dir))
            shutil.rmtree(installer_dir)

    def delete_stamp_files(self, dist):
        """Clean up likely stale stamp files."""
        for appl_physical_path in fcgi.list_stamp_paths(
            dist.msdeploy_app_name, self.stamp_filename):
            stamp_file = os.path.join(
                appl_physical_path, self.stamp_filename)
            if os.path.exists(stamp_file):
                logger.info('Removing stale install stamp file: {0}'.format(
                    stamp_file))
                os.remove(stamp_file)

    def write_feed(self, **kw):
        from zope.pagetemplate import pagetemplatefile
        template = pagetemplatefile.PageTemplateFile(self.feed_template)
        logger.info('Writing Web Platform Installer feed to {0}'.format(
            self.feed))

        view = core.run_setup('setup.py', stop_after='commandline')
        view.context = self
        view.dists = self.distributions
        view.now = datetime.datetime.now()

        open(self.feed, 'w').write(template(view=view, **kw))
        return template

    def delete_feed_cache(self, feed):
        if feed is None:
            return

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
            ids = [node for node in feed.childNodes if node.nodeName == 'id']
            cached_ids = [node for node in cached_feed.childNodes
                          if node.nodeName == 'id']
            if cached_ids and (
                cached_ids[0].firstChild.data == ids[0].firstChild.data):
                logger.info(
                    'Removing the Web Platform Installer cached feed at {0}'
                    .format(cached_feed_path))
                os.remove(cached_feed_path)
                break


cmdclass = dict(build_msdeploy=build_msdeploy.build_msdeploy,
                install_msdeploy=install_msdeploy.install_msdeploy,
                bdist_msdeploy=bdist_msdeploy.bdist_msdeploy,
                build_webpi=build_webpi)
