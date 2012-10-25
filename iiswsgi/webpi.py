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

import sys
import os
import subprocess
import shutil
import logging
import argparse
import urlparse
import errno

from xml.dom import minidom

from distutils import core

from iiswsgi import options
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


class WebPIBuilder(object):
    __doc__ = __doc__

    feed_name = 'web-pi.xml'
    webpi_installer_cache = None
    if 'LOCALAPPDATA' in os.environ:
        webpi_installer_cache = os.path.join(
            os.environ['LOCALAPPDATA'],
            'Microsoft', 'Web Platform Installer', 'installers')
    iis_sites_home = None
    if 'USERPROFILE' in os.environ:
        iis_sites_home = os.path.join(
            os.environ['USERPROFILE'], 'Documents', 'My Web Sites')
    feed_dir = None
    if 'LOCALAPPDATA' in os.environ:
        feed_dir = os.path.join(
            os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer')

    def __init__(self, packages, feed=None):
        if not packages:
            raise ValueError('At least one MSDeploy package must be given')
        self.packages = packages
        self.feed = feed
        self.cwd = os.getcwd()
        self.dists = []

    def __call__(self, *args):
        for package in self.packages:
            dist = self.build_package(package, *args)
            self.dists.append(dist)
            manifest = minidom.parse(os.path.join(package, 'Manifest.xml'))
            dist.msdeploy_app_name = get_app_name(manifest)
            self.delete_installer_cache(dist)
            self.delete_stamp_files(dist)

        if self.feed is not None:
            self.write_feed()
            feed = minidom.parse(self.feed).firstChild
            self.delete_feed_cache(feed)

    def build_package(self, package, *args):
        try:
            os.chdir(package)

            logger.info('Building package: {0}'.format(' '.join(args)))
            cmd = [sys.executable, 'setup.py']
            cmd.extend(args)
            logger.info('Building package: {0}'.format(' '.join(cmd)))
            subprocess.check_call(cmd)

            dist = core.run_setup('setup.py', stop_after='commandline')
            dist.msdeploy_package = os.path.abspath(os.path.join(
                'dist', '{0}-{1}.zip'.format(
                    dist.get_name(), dist.get_version())))

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
        if not self.iis_sites_home:
            logger.error('No IIS sites directory')
            return
        for name in os.listdir(self.iis_sites_home):
            if not (os.path.isdir(os.path.join(self.iis_sites_home, name)) and
                    name.startswith(dist.msdeploy_app_name)):
                continue
            stamp_file = os.path.join(
                self.iis_sites_home, name, 'iis_install.stamp')
            if os.path.exists(stamp_file):
                logger.info('Removing stale install stamp file: {0}'.format(
                    stamp_file))
                os.remove(stamp_file)

    def write_feed(self, **kw):
        from zope.pagetemplate import pagetemplatefile
        template = pagetemplatefile.PageTemplateFile(self.feed_template)
        logger.info('Writing Web Platform Installer feed to {0}'.format(
            self.feed))
        open(self.feed, 'w').write(template(view=self, **kw))
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


webpi_parser = argparse.ArgumentParser(
    description=WebPIBuilder.__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[options.parent_parser])
webpi_parser.add_argument('-f', '--feed', help="""\
Web Platform Installer atom feed to update.  If a file of the same name but \
with a `*.in` extension exists it will be used as a template.  \
Useful to avoid versioning irrellevant feed changes.""")
webpi_parser.add_argument(
    '-p', '--package', dest='packages', action='append', help="""\
A Web Deploy package directory.  Must contain a `setup.py` file which uses \
the `iiswsgi` `distutils` commands to generate a package.  May be
given multiple times.""")


def webpi_console(args=None):
    logging.basicConfig()
    args, unknown = webpi_parser.parse_known_args(args=args)
    if not unknown:
        unknown = ['-q', 'bdist_msdeploy']
    builder = WebPIBuilder(args.packages, feed=args.feed)
    builder(*unknown)


cmdclass = dict(build_msdeploy=build_msdeploy.build_msdeploy,
                install_msdeploy=install_msdeploy.install_msdeploy,
                bdist_msdeploy=bdist_msdeploy.bdist_msdeploy)
