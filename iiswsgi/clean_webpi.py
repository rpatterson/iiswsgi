"""Clean WebPI caches for the bdist_webpi msdeploy dists."""

import os
import shutil
import logging

from xml.dom import minidom

from distutils import core
from distutils import cmd

from iiswsgi import options
from iiswsgi import fcgi

webpi_cache = os.path.join(
    '%LOCALAPPDATA%', 'Microsoft', 'Web Platform Installer')
bdist_msdeploy_opt = (
    'msdeploy-bdists=', 'm',
    'Paths to dists containing built MSDeploy packages to include in the feed.'
    )

logger = logging.getLogger('iiswsgi.webpi')


def get_app_name(path):
    """Return the <iisApp> name from a Manifest.xml DOM."""
    manifest = minidom.parse(os.path.join(path, 'Manifest.xml'))
    iisapps = manifest.getElementsByTagName('iisApp')
    if not iisapps:
        raise ValueError('No <iisApp> elements found in Manifest.xml')
    elif len(iisapps) > 1:
        raise ValueError('Multiple <iisApp> elements found in Manifest.xml')
    return iisapps[0].getAttribute('path')


class clean_webpi(cmd.Command):
    description = __doc__ = __doc__

    user_options = [
        bdist_msdeploy_opt,
        ('webpi-cache=', 'c',
         "The WebPI cache to clean out. [default: {0}]".format(
             webpi_cache))]

    stamp_filename = options.stamp_filename

    def initialize_options(self):
        self.msdeploy_bdists = None
        self.webpi_cache = None

    def finalize_options(self):
        self.set_undefined_options(
            'bdist_webpi', ('msdeploy_bdists', 'msdeploy_bdists'))
        if self.webpi_cache is None:
            self.webpi_cache = webpi_cache
        self.webpi_cache = os.path.expandvars(self.webpi_cache)
        self.ensure_dirname('webpi_cache')
        options.ensure_verbosity(self)

    def run(self):
        for path in self.msdeploy_bdists:
            distribution = core.run_setup('setup.py', stop_after='commandline')
            distribution.msdeploy_app_name = get_app_name(path)
            self.delete_installer_cache(distribution)
            self.delete_stamp_files(distribution)
        self.delete_feed_cache()
        # TODO DL all new resources in IE?

    def delete_installer_cache(self, distribution):
        """Delete old Web Deploy packages from the WebPI cache."""
        installer_dir = os.path.join(
            self.webpi_cache, 'installers', distribution.msdeploy_app_name)
        if os.path.exists(installer_dir):
            logger.info('Removing the cached MSDeploy package: {0}'.format(
                installer_dir))
            shutil.rmtree(installer_dir)

    def delete_stamp_files(self, distribution):
        """
        Clean up likely stale iis_install.stamp files for bdist_webpi packages.
        """
        for appl_physical_path in fcgi.list_appl_paths(
            distribution.msdeploy_app_name):
            if not os.path.exists(os.path.join(
                appl_physical_path, self.stamp_filename)):
                continue
            stamp_file = os.path.join(
                appl_physical_path, self.stamp_filename)
            if os.path.exists(stamp_file):
                logger.info('Removing stale install stamp file: {0}'.format(
                    stamp_file))
                os.remove(stamp_file)

    def delete_feed_cache(self):
        """Delete copies of the feed from the Web Platform Installer cach."""
        for cached_feed_name in os.listdir(self.webpi_cache):
            if not os.path.splitext(cached_feed_name)[1] == '.xml':
                # not a cached feed file
                continue

            # Compare feed/id elements
            cached_feed_path = os.path.join(self.webpi_cache, cached_feed_name)
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
