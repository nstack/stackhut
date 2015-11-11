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
import sys
from . import __version__
from .common.commands import CmdRunner
from .common import utils
from .toolkit_utils import keen_client
from .builder import get_docker

from .commands import COMMANDS
from .run_commands import COMMANDS as RUN_COMMANDS

class ToolkitRunner(CmdRunner):
    def custom_error(self, e):
        import traceback
        # exception analytics
        try:
            dv = get_docker(_exit=False, verbose=False).client.version().get('Version')
        except:
            dv = None

        keen_client.send('cli_exception',
                         dict(cmd=self.args.command,
                              exception=repr(e),
                              stackhut_version=__version__,
                              docker_version=dv,
                              os=sys.platform,
                              python_version=sys.version,
                              traceback=traceback.format_exc()))

        utils.log.info(":( If this reoccurs please open an issue at https://github.com/stackhut/stackhut "
                       "or email toolkit@stackhut.com - thanks!")

    def custom_shutdown(self):
        keen_client.shutdown()

def main():
    runner = ToolkitRunner("StackHut Toolkit", __version__)
    # register the sub-commands
    runner.register_commands(COMMANDS + RUN_COMMANDS)
    # start
    retval = runner.start()
    return retval
