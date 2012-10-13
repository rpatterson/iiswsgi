import sys
import os
import argparse
import logging

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')


class VerboseAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        root.setLevel(root.level - 10)
        if root.level == logging.DEBUG:
            # Some useful startup debugging info
            logger.debug('os.getcwd(): {0}'.format(os.getcwd()))
            logger.debug('sys.argv: {0}'.format(sys.argv))
            logger.debug('os.environ:\n{0}'.format(
                '\n'.join('{0}={1}'.format(key, value)
                          for key, value in os.environ.iteritems())))
        setattr(namespace, self.dest, root.level)

parent_parser = argparse.ArgumentParser(add_help=False)
verbose = parent_parser.add_argument(
    "-v", "--verbose", nargs=0, action=VerboseAction,
    help=("Increase the verbosity of logging.  "
          "Can be given multiple times.  "
          "Pass before other options to ensure that logging includes "
          "information about processing options."))
