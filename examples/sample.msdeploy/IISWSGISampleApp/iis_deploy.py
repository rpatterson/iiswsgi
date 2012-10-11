#!/usr/bin/env python2.7

from iiswsgi import deploy


def main():
    deploy.install_fcgi_app(
        fullPath="%SystemDrive%\Python27\python.exe",
        arguments=("-u %SystemDrive%\Python27\Scripts\iiswsgi-script.py "
                   "-c %APPL_PHYSICAL_PATH%\iis_fcgi.ini"),
        monitorChangesTo="%SystemDrive%\Python27\Scripts\iiswsgi-script.py",
        maxInstances="1")

if __name__ == '__main__':
    main()
