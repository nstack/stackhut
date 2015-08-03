#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 StackHut Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys
from stackhut_common import utils
from stackhut_common.utils import log, keen_client
from stackhut_common.primitives import get_docker
from stackhut_toolkit import __version__
from .commands import COMMANDS

def register_commands(parser, cmds):
    metavar = '{{{}}}'.format(str.join(',', [cmd.name for cmd in cmds if cmd.visible]))
    subparsers = parser.add_subparsers(title="StackHut Commands", dest='command', metavar=metavar)

    for cmd in cmds:
        if cmd.visible:
            sp = subparsers.add_parser(cmd.name, help=cmd.description, description=cmd.description)
        else:
            sp = subparsers.add_parser(cmd.name)

        sp.set_defaults(func=cmd)
        cmd.register(sp)

def main():
    # Parse the cmd args
    parser = argparse.ArgumentParser(description="StackHut Toolkit",
                                     epilog="Have fun :)")
    parser.add_argument('-V', '--version', help='StackHut Toolkit Version',
                        action="version", version="%(prog)s {}".format(__version__))
    parser.add_argument('-v', dest='verbose', help="Verbose mode", action='store_true')
    parser.add_argument('-d', dest='debug', help=argparse.SUPPRESS)

    # register the sub-commands
    register_commands(parser, COMMANDS)

    # parse the args
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        parser.exit(0, "No command given\n")

    # General App Setup
    utils.DEBUG = args.debug
    utils.set_log_level(args.verbose)
    log.info("Starting up StackHut")
    log.debug(args)

    try:
        # dispatch to correct cmd class - i.e. build, compile, run, etc.
        subfunc = args.func(args)
        retval = subfunc.run()
    except Exception as e:
        import traceback

        if len(e.args) > 0:
            [log.error(x) for x in e.args]

        # exception analytics
        try:
            dv = get_docker(_exit=False).version().get('Version')
        except:
            dv = None

        keen_client.send('cli_exception',
                         dict(cmd=args.command,
                              exception=repr(e),
                              stackhut_version=__version__,
                              docker_version=dv,
                              os=sys.platform,
                              python_version=sys.version,
                              traceback=traceback.format_exc()))

        if args.verbose:
            raise e
        else:
            log.info("Exiting (run in verbose mode for more information)")
        return 1

    finally:
        keen_client.shutdown()

    # all done
    return retval
