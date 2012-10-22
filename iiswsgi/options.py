import sys
import os
import argparse
import logging

root = logging.getLogger()
logger = logging.getLogger('iiswsgi')

lib_name = 'Lib'
scripts_name = 'Scripts'
script_ext = '.exe'
if not sys.platform.startswith('win'):
    lib_name = 'lib'
    scripts_name = 'bin'
    script_ext = ''


def get_script_path(script, executable=None):
    """
    Get a path to a script in a cross-platform compatible way.
    """
    if executable is None:
        executable = sys.executable

    scripts_dir = os.path.dirname(executable)
    if os.path.exists(os.path.join(scripts_dir, scripts_name)):
        # Real python, not a virtualenv
        scripts_dir = os.path.join(scripts_dir, scripts_name)

    return os.path.join(scripts_dir, script + script_ext)


def increase_verbosity():
    root.setLevel(root.level - 10)
    if root.level == logging.DEBUG:
        # Some useful startup debugging info
        logger.debug('os.getcwd(): {0}'.format(os.getcwd()))
        logger.debug('sys.argv: {0}'.format(sys.argv))
        logger.debug('os.environ:\n{0}'.format(
            '\n'.join('{0}={1}'.format(key, value)
                      for key, value in os.environ.iteritems())))
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
