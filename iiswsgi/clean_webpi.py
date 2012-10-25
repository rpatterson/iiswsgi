"""
Clean IIS WSGI Web Platform Installer caches:

1. delete old Web Deploy packages from the Web Platform Installer cache

2. delete `iis_install.stamp` files from all installations of any of the
   given packages in `%USERPROFILE%\Documents\My Web Sites`

3. delete copies of the feed from the Web Platform Installer cache
"""

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

logger = logging.getLogger('iiswsgi.webpi')


class clean_webpi(cmd.Command):
    __doc__ = __doc__

    user_options = [
        ('webpi-cache=', 'c',
         "The WebPI cache to clean out. [default: {0}]".format(
             webpi_cache))]

    stamp_filename = options.stamp_filename

    def initialize_options(self):
        self.webpi_cache = None

    def finalize_options(self):
        if self.webpi_cache is None:
            self.webpi_cache = webpi_cache
        self.webpi_cache = os.path.expandvars(self.webpi_cache)
        self.ensure_dirname('webpi_cache')
        options.ensure_verbosity(self)

    def run(self):
        for path in self.distribution.bdist_msdeploy:
            distribution = core.run_setup('setup.py', stop_after='commandline')
            self.delete_installer_cache(distribution)
            self.delete_stamp_files(distribution)
        self.delete_feed_cache()

    def delete_installer_cache(self, distribution):
        installer_dir = os.path.join(
            self.webpi_cache, 'installers', distribution.msdeploy_app_name)
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

    def delete_feed_cache(self):
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