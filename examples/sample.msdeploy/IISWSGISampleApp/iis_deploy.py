#!/usr/bin/env python2.7

from iiswsgi import deploy


def main():
    deploy.install_fcgi_app()

if __name__ == '__main__':
    main()
