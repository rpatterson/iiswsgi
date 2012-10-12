#!/usr/bin/env python2.7

from iiswsgi import deploy


def main():
    deploy.install_fcgi_app(
        fullPath="%SystemDrive%\Python27\python.exe",
        arguments=('-u %SystemDrive%\Python27\Scripts\iiswsgi-script.py '
                   '-c "%IIS_SITES_HOME%\%IISEXPRESS_SITENAME%\iis_fcgi.ini"'),
        # Can't use environment variables in monitorChangesTo
        monitorChangesTo="C:\Python27\Scripts\iiswsgi-script.py",
        maxInstances="1")

if __name__ == '__main__':
    main()
