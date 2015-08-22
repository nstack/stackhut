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
"""
Module performs basic command handling infrastructure for subcommands
"""
import os
import abc
import argparse
from . import utils
from .config import HutfileCfg


class CmdRunner:
    def __init__(self, title, version):
        self.title = title
        self.args = None
        # Parse the cmd args
        self.parser = argparse.ArgumentParser(description=title)
        self.parser.add_argument('-V', '--version', help="{} Version".format(title),
                                 action="version", version="%(prog)s {}".format(version))
        self.parser.add_argument('-v', dest='verbose', help="Verbose mode", action='store_true')
        self.parser.add_argument('-s', dest='server', help=argparse.SUPPRESS)

    def register_commands(self, cmds):
        metavar = '{{{}}}'.format(str.join(',', [cmd.name for cmd in cmds if cmd.visible]))
        subparsers = self.parser.add_subparsers(title="{} Commands".format(self.title), dest='command', metavar=metavar)

        for cmd in cmds:
            if cmd.visible:
                sp = subparsers.add_parser(cmd.name, help=cmd.description, description=cmd.description)
            else:
                sp = subparsers.add_parser(cmd.name)

            sp.set_defaults(func=cmd)
            cmd.register(sp)

    def custom_error(self, e):
        pass

    def custom_shutdown(self):
        pass

    def start(self):
        # parse the args
        self.args = self.parser.parse_args()
        if self.args.command is None:
            self.parser.print_help()
            self.parser.exit(0, "No command given\n")

        # General App Setup
        if self.args.server:
            utils.SERVER_URL = self.args.server

        utils.setup_logging(self.args.verbose)
        utils.log.info("Starting {}".format(self.title))

        try:
            # dispatch to correct cmd class - i.e. build, compile, run, etc.
            subfunc = self.args.func(self.args)
            retval = subfunc.run()
        except Exception as e:

            if len(e.args) > 0:
                [utils.log.error(x) for x in e.args]

            self.custom_error(e)

            if self.args.verbose:
                raise e
            else:
                utils.log.info("Exiting (run in verbose mode for more information)")
            return 1

        finally:
            self.custom_shutdown()

        # all done
        return retval if retval else 0


###################################################################################################
# StackHut Commands Handling
class BaseCmd:
    """The Base Command implementing common func"""
    visible = True
    name = ''
    description = ""

    @staticmethod
    def register(sp):
        pass

    def __init__(self, args):
        self.args = args

    @abc.abstractmethod
    def run(self):
        """Main entry point for a command with parsed cmd args"""
        pass

class HutCmd(BaseCmd):
    """Hut Commands are run from a Hut stack dir requiring a Hutfile"""
    def __init__(self, args):
        super().__init__(args)
        # import the hutfile
        self.hutcfg = HutfileCfg()
        # create stackhut dir if not present
        # os.mkdir(utils.STACKHUT_DIR) if not os.path.exists(utils.STACKHUT_DIR) else None
