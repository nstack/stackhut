#!/usr/bin/env python3
# TODO - switch to python3 once OSX and Ubuntu/Redhat distros do
import argparse
from stackhut.commands import COMMANDS
import stackhut.utils as utils

if __name__ == "__main__":
    # Parse the cmd args
    parser = argparse.ArgumentParser(description="StackHut CLI",
                                     epilog="Now build some crazy shit :)")
    parser.add_argument('-V', help='StackHut CLI Version',
                        action="version", version="%(prog)s 0.1.0")
    parser.add_argument("--hutfile", help="Path to user-defined hutfile (default: %(default)s)",
                        default=utils.HUTFILE, type=argparse.FileType('r', encoding='utf-8'))
    parser.add_argument('-v', dest='verbose', help="Verbosity level, add multiple times to increase",
                        action='count', default=0)
    # build the subparsers
    subparsers = parser.add_subparsers(title="StackHut Commands", dest='command')
    [cmd.parse_cmds(subparsers) for cmd in COMMANDS]
    # parse the args
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        parser.exit(0, "No command given")

    # General App Setup
    utils.set_log_level(args.verbose)
    utils.log.info("Starting up StackHut")
    utils.log.debug(args)

    # dispatch to correct subfunction - i.e. build, compile, run, etc.
    retval = args.func(args)
    # all done
    exit(retval)
