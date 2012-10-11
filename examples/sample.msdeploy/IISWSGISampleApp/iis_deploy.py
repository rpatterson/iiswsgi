#!/usr/bin/env python2.7

from iiswsgi import deploy


def main():
    deploy.install_fcgi_app(
        fullPath="C:\Python27\python.exe",
        arguments="-u C:\Python27\Scripts\iiswsgi-script.py",
        monitorChangesTo="C:\Python27\Scripts\iiswsgi-script.py",
        maxInstances="1")

if __name__ == '__main__':
    main()
