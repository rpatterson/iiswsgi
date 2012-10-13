#!/usr/bin/env python2.7

import sys
import os
import subprocess
import shutil
import logging

from xml.dom import minidom

logger = logging.getLogger('iiswsgi.build')


def build():
    """
    Helper for building IIS WSGI Web Deploy packages.

    TODO
    """
    cwd = os.getcwd()

    feed_path = os.path.join(cwd, 'web-pi.xml')
    doc = minidom.parse(feed_path + '.in')

    for name in os.listdir(cwd):
        if os.path.splitext(name)[1] != '.msdeploy':
            # not an msdeploy package
            continue

        try:
            os.chdir(os.path.join(cwd, name))
            subprocess.check_call([sys.executable, 'setup.py', 'sdist'])
            os.chdir('dist')
            latest_package = max(
                (package for package in os.listdir('.')
                 if os.path.splitext(package)[1] == '.zip'),
                key=os.path.getmtime)
            package_size = os.path.getsize(latest_package)
            package_sha1 = subprocess.check_output([
                'fciv', '-sha1', latest_package])
        finally:
            os.chdir(cwd)

        package_name = latest_package.split('-', 1)[0]

        installer_dir = os.path.join(
            os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer',
            'installers', package_name)
        if os.path.exists(installer_dir):
            logger.info('Removing the cached MSDeploy package: {0}'.format(
                installer_dir))
            shutil.rmtree(installer_dir)

        package_size_kb = int(round(package_size / 1024.0))
        for entry in doc.getElementsByTagName('entry'):
            productIds = entry.getElementsByTagName("productId")
            if productIds and productIds[0].firstChild.data == package_name:
                break
        else:
            raise ValueError('Could not find <entry> for {0} in {1}'.format(
                package_name, feed_path))

        size_elem = entry.getElementsByTagName('fileSize')[0]
        size_elem.firstChild.data = u'{0}'.format(package_size_kb)
        logger.info('Set Web Platform Installer <fileSize> to {0}'.format(
            package_size_kb))

        package_sha1_value = package_sha1.rsplit(
            '\r\n', 2)[-2].split(' ', 1)[0]
        sha1_elem = entry.getElementsByTagName('sha1')[0]
        sha1_elem.firstChild.data = u'{0}'.format(package_sha1_value)
        logger.info('Set Web Platform Installer <sha1> to {0}'.format(
            package_sha1_value))

    doc.writexml(open(feed_path, 'w'))

    feed_dir = os.path.join(
        os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer')
    for feed in os.listdir(feed_dir):
        if not os.path.splitext(feed)[1] == '.xml':
            # not a cached feed file
            continue
        feed_path = os.path.join(feed_dir, feed)
        cached_doc = minidom.parse(feed_path)
        links = cached_doc.getElementsByTagName("link")
        if (links and
            links[0].getAttribute('href') ==
            doc.getElementsByTagName("link")[0].getAttribute('href')):
            logger.info(
                'Removing the Web Platform Installer cached feed at {0}'
                .format(feed_path))
            os.remove(feed_path)

    # Clean up likely stale stamp files
    iis_sites_home = os.path.join(
        os.environ['USERPROFILE'], 'Documents', 'My Web Sites')
    for name in os.listdir(iis_sites_home):
        if not os.path.isdir(os.path.join(iis_sites_home, name)):
            continue
        stamp_file = os.path.join(iis_sites_home, name, 'iis_deploy.stamp')
        if os.path.exists(stamp_file):
            logger.info(
                'Removing stale deploy stamp file: {0}'.format(stamp_file))
            os.remove(stamp_file)


def build_console(args=None):
    logging.basicConfig(level=logging.INFO)
    build()
