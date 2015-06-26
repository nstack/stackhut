#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""
import os
import shutil
import sh

import stackhut.utils as utils
from stackhut.utils import log
from stackhut.run_command import RunCloudCmd, RunLocalCmd
from stackhut.build_commands import StackBuildCmd, HutBuildCmd

# TODO - small commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes



# StackHut primary commands
COMMANDS = [RunLocalCmd,
            RunCloudCmd,
            HutBuildCmd,
            StackBuildCmd,
            # debug, push, pull, test, etc.
            ]

