#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""
import sys
import os
import subprocess
import logging
import argparse
import json
from boto.s3.connection import S3Connection, Location, Key
import requests
import barrister
import uuid
import yaml

from stackhut.utils import *
from stackhut.run_command import RunCmd

# TODO - small commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes

class CompileCmd(BaseCmd):
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

