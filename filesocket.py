"""
The `filesocket` module implements socket behavior backed by two
file-like object to and from which the actual data is read and
written.
"""

import sys
import os
import socket


class FileSocket(object):

    def __init__(self, in_file=None, out_file=None,
                 use_out_fileno=False):
        # Default to sys.stdin and sys.stdout unbuffered
        if in_file is None:
            in_file = os.fdopen(sys.stdin.fileno(), sys.stdin.mode, 0)
        if out_file is None:
            out_file = os.fdopen(sys.stdout.fileno(), sys.stdout.mode, 0)

        self.in_file = in_file
        self.out_file = out_file

        fileno_file = in_file
        if use_out_fileno:
            fileno_file = out_file
        if hasattr(fileno_file, 'fileno'):
            self.fileno = fileno_file.fileno

        self.recv = in_file.read

    def send(self, string):
        self.out_file.write(string)
        return len(string)

    def shutdown(self, how):
        if how in (socket.SHUT_RD, socket.SHUT_RDWR):
            self.in_file.close()
        if how in (socket.SHUT_WR, socket.SHUT_RDWR):
            self.out_file.close()

    def close(self):
        del self.in_file
        del self.recv
        del self.out_file
