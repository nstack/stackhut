#!/usr/bin/env python2
# TODO - switch to python3 once OSX and Ubuntu/Redhat distros do
from __future__ import (unicode_literals, print_function, division, absolute_import)
from future import standard_library
standard_library.install_aliases()
from builtins import *

import argparse
from stackhut.commands import COMMANDS
import stackhut.utils as utils
from stackhut.utils import log

if __name__ == "__main__":
    # Parse the cmd args
    parser = argparse.ArgumentParser(description="StackHut CLI",
                                     epilog="Now build some crazy shit :)")
    parser.add_argument('-V', help='StackHut CLI Version',
                        action="version", version="%(prog)s 0.1.0")
#    parser.add_argument("--hutfile", help="Path to user-defined hutfile (default: %(default)s)",
#                        default=utils.HUTFILE, type=argparse.FileType('r', encoding='utf-8'))
    parser.add_argument('-v', dest='verbose', help="Verbosity level, add multiple times to increase",
                        action='count', default=0)
    # build the subparsers
    subparsers = parser.add_subparsers(title="StackHut Commands", dest='command')
    [cmd.parse_cmds(subparsers) for cmd in COMMANDS]
    # parse the args
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        parser.exit(0, "No command given\n")

    # General App Setup
    utils.set_log_level(args.verbose)
    log.info("Starting up StackHut")
    log.debug(args)

    # dispatch to correct subfunction - i.e. build, compile, run, etc.
    subfunc = args.func(args)
    retval = subfunc.run()

    # all done
    exit(retval)
