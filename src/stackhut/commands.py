#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
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

