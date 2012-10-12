#!/usr/bin/env python2.7

import sys
import os
import subprocess
import shutil
import logging

from xml.dom import minidom

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('iiswsgi.build_package')

cwd = os.getcwd()

try:
    os.chdir(os.path.join(os.path.dirname(__file__), 'sample.msdeploy'))
    subprocess.check_call([sys.executable, 'setup.py', 'sdist'])
    package_size = os.path.getsize(
        os.path.join('dist', 'IISWSGISampleApp-0.1.zip'))
    package_sha1 = subprocess.check_output([
        'fciv', '-sha1', os.path.join('dist', 'IISWSGISampleApp-0.1.zip')])
finally:
    os.chdir(cwd)

feed_dir = os.path.join(
    os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer')
for feed in os.listdir(feed_dir):
    if not os.path.splitext(feed)[1] == '.xml':
        # not a cached feed file
        continue
    feed_path = os.path.join(feed_dir, feed)
    doc = minidom.parse(feed_path)
    links = doc.getElementsByTagName("link")
    if links and 'iiswsgi' in links[0].getAttribute('href'):
        logger.info(
            'Removing the Web Platform Installer cached feed at {0}'.format(
                feed_path))
        os.remove(feed_path)

installer_dir = os.path.join(
    os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer',
    'installers', 'IISWSGISampleApp')
if os.path.exists(installer_dir):
    logger.info('Removing the cached MSDeploy package: {0}'.format(
        installer_dir))
    shutil.rmtree(installer_dir)

feed_path = os.path.join(os.path.dirname(__file__), 'web-pi.xml')
doc = minidom.parse(feed_path + '.in')

package_size_kb = int(round(package_size / 1024.0))
size_elem = doc.getElementsByTagName('fileSize')[0]
size_elem.firstChild.data = u'{0}'.format(package_size_kb)
logger.info('Set Web Platform Installer <fileSize> to {0}'.format(
    package_size_kb))

package_sha1_value = package_sha1.rsplit('\r\n', 2)[-2].split(' ', 1)[0]
sha1_elem = doc.getElementsByTagName('sha1')[0]
sha1_elem.firstChild.data = u'{0}'.format(package_sha1_value)
logger.info('Set Web Platform Installer <sha1> to {0}'.format(
    package_sha1_value))

doc.writexml(open(feed_path, 'w'))
