#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""

import stackhut.utils as utils
from stackhut.run_command import RunCmd

# TODO - small commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes

class CompileCmd(utils.BaseCmd):
    cmd_name = 'compile'

    def parse_cmds(self, subparsers):
        subparser = super().parse_cmds(subparsers, "Compile a StackHut service")

    def run(self, args):
        pass


# StackHut primary commands
COMMANDS = [RunCmd(),
            CompileCmd(),
            # debug, push, pull, test, etc.
            ]

