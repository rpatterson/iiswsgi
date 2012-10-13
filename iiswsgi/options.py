import sys
import os
import argparse
import logging

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')


def verbose_option(value):
    root.setLevel(root.level - 10)
    if root.level == logging.DEBUG:
        # Some useful startup debugging info
        logger.debug('os.getcwd(): {0}'.format(os.getcwd()))
        logger.debug('sys.argv: {0}'.format(sys.argv))
        logger.debug('os.environ:\n{0}'.format(
            '\n'.join('{0}={1}'.format(key, value)
                      for key, value in os.environ.iteritems())))
    return root.level

parent_parser = argparse.ArgumentParser(add_help=False)
verbose = parent_parser.add_argument(
    "-v", "--verbose", default=root.level, dest='verbose', type=verbose_option,
    help=("Increase the verbosity of logging.  "
          "Can be given multiple times.  "
          "Pass before other options to ensure that logging includes "
          "information about processing options."))
