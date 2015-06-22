#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""

import stackhut.utils as utils
from stackhut.run_command import RunCloudCmd, RunLocalCmd

# TODO - small commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes

class CompileCmd(utils.BaseCmd):
    cmd_name = 'compile'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(CompileCmd, CompileCmd).parse_cmds(subparser, 'compile', "Compile a StackHut service locally", RunLocalCmd)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        pass


# StackHut primary commands
COMMANDS = [RunLocalCmd,
            RunCloudCmd,
            CompileCmd,
            # debug, push, pull, test, etc.
            ]

