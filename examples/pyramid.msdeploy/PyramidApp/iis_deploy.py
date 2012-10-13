#!/usr/bin/env python2.7

import sys
import os
import subprocess


def main():
    subprocess.check_call(
        [os.path.join(os.path.dirname(
            sys.executable), 'Scripts', 'pcreate.exe'), '-s',
         '__pyramid_scaffold__', '__pyramid_project__'])

if __name__ == '__main__':
    main()
