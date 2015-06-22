#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""
import sh

import stackhut.utils as utils
from stackhut.run_command import RunCloudCmd, RunLocalCmd

# TODO - small commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes

class BuildCmd(utils.BaseCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(BuildCmd, BuildCmd).parse_cmds(subparser, 'build',
                                                         "Build a StackHut service", BuildCmd)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        super().run()
        # move barrister call into process as running on py2.7 ?
        sh.barrister(['-z', '-Gsize=8,5 -Glayout=twopi', '-d', 'service.html', '-p', 'service.png',
                      '-t', self.hutfile['desc'], '-j', 'service.json', 'service.idl'])
        sh.docker(['build', '-t', "{}:{}".format(self.hutfile['name'], self.hutfile['version']), '--rm', '.'])






# StackHut primary commands
COMMANDS = [RunLocalCmd,
            RunCloudCmd,
            BuildCmd,
            # debug, push, pull, test, etc.
            ]

