#!/usr/bin/env python2.7

import sys
import os
import subprocess
import logging

logger = logging.getLogger('pyramid.iiswsgi')


def main():
    logging.basicConfig(level=logging.INFO)

    pcreate = os.path.join(os.path.dirname(sys.executable), 'pcreate.exe')
    args = [pcreate, '-s', '__pyramid_scaffold__', '__pyramid_project__']
    logger.info('Creating Pyramid project: {0}'.format(' '.join(args)))
    subprocess.check_call(args)

    cwd = os.getcwd()
    args = [sys.executable, 'setup.py', 'develop']
    logger.info(
        'Installing __pyramid_project__ project for development: {0}'.format(
            ' '.join(args)))
    os.chdir('__pyramid_project__')
    try:
        subprocess.check_call(args)
    finally:
        os.chdir(cwd)

if __name__ == '__main__':
    main()
