import sys
import os
import argparse
import logging

import pkg_resources
import distutils.sysconfig
from distutils import errors

stamp_filename = 'iis_install.stamp'

default_level = logging.INFO
logger = logging.getLogger('iiswsgi')


def assert_string(dist, attr, value):
    if not isinstance(value, str):
        raise errors.DistutilsOptionError(
            'The {0} option must be a string: {1}'.format(attr, value))


def assert_list(dist, attr, value):
    if not isinstance(value, list):
        raise errors.DistutilsOptionError(
            'The {0} option must be a list: {1}'.format(attr, value))


def debug_environ():
    """Log useful debug information."""
    # Some useful startup debugging info
    logger.debug('os.getcwd(): {0}'.format(os.getcwd()))
    logger.debug('sys.argv: {0}'.format(sys.argv))
    logger.debug('os.environ:\n{0}'.format(
        '\n'.join('{0}={1}'.format(key, value)
                  for key, value in os.environ.iteritems())))


def ensure_verbosity(self, level=default_level):
    """Ensure that logging is configured per the verbosity setting."""
    if self.verbose == 0:
        level += 10
    elif self.verbose == 2:
        level -= 10
    logging.basicConfig(level=level)
    if level == logging.DEBUG:
        debug_environ()


def increase_verbosity():
    root = logging.getLogger()
    root.setLevel(root.level - 10)
    if root.level == logging.DEBUG:
        debug_environ()
    return root.level


class VerboseAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, increase_verbosity())

parent_parser = argparse.ArgumentParser(add_help=False)
verbose = parent_parser.add_argument(
    "-v", "--verbose", nargs=0, action=VerboseAction,
    help=("Increase the verbosity of logging.  "
          "Can be given multiple times.  "
          "Pass before other options to ensure that logging includes "
          "information about processing options."))


def get_egg_name(dist):
    pkg_dist = pkg_resources.Distribution(
        None, None, dist.get_name(), dist.get_version(),
        distutils.sysconfig.get_python_version(),
        pkg_resources.get_build_platform())
    return pkg_dist.egg_name()
