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
from stackhut_common.commands import CmdRunner
from stackhut_common import utils
from . import __version__, COMMANDS
from .utils import keen_client
from .builder import get_docker

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

        # utils.log.info("Something bad happened - sorry! :|")
        utils.log.info("Please send us an email at toolkit@stackhut.com or open an issue at http://www.github.com/StackHut/stackhut-toolkit - thanks!")

    def custom_shutdown(self):
        keen_client.shutdown()

def main():
    runner = ToolkitRunner("StackHut Toolkit", __version__)
    # register the sub-commands
    runner.register_commands(COMMANDS)
    # start
    retval = runner.start()
    return retval
