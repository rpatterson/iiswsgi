#!/usr/bin/env python2.7

import os
import subprocess
import shutil
import logging

from xml.dom import minidom

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('iisfcgi.build_package')

cwd = os.getcwd()

try:
    os.chdir('sample.msdeploy')
    subprocess.check_call([
        os.path.join('..', 'Scripts', 'python.exe'),
        'setup.py', 'sdist'])
    package_size = os.path.getsize(
        os.path.join('dist', 'IISFCGISampleApp-0.1.zip'))
    package_sha1 = subprocess.check_output([
        'fciv', '-sha1', os.path.join('dist', 'IISFCGISampleApp-0.1.zip')])
finally:
    os.chdir(cwd)

feed_file = os.path.join(
    os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer',
    '-1373627273.xml')
if os.path.exists(feed_file):
    logger.info('Removing the Web Platform Installer cached feed')
    os.remove(feed_file)
installer_dir = os.path.join(
    os.environ['LOCALAPPDATA'], 'Microsoft', 'Web Platform Installer',
    'installers', 'IISFCGISampleApp')
if os.path.exists(installer_dir):
    logger.info('Removing the cached MSDeploy package')
    shutil.rmtree(installer_dir)

doc = minidom.parse('web-pi.xml')

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

doc.writexml(open('web-pi.xml', 'w'))
