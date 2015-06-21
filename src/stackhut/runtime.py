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

# TODO - add more service handling here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes
class BaseCmd:
    cmd_name = ''

    def __init__(self):
        pass

    def parse_cmds(self, subparsers, description):
        sp = subparsers.add_parser(self.cmd_name, help=description, description=description)
        sp.set_defaults(func=self.run)
        return sp

    def run(self, args):
        """Main entry point for a command with parsed cmd args"""
        pass

class RunCmd(BaseCmd):
    cmd_name = 'run'

    def __init__(self):
        super(RunCmd).__init__()

    def parse_cmds(self, subparsers):
        subparser = super(RunCmd, self).parse_cmds(subparsers, "Run a StackHut service")
        subparser.add_argument('--foo')
        subparser.add_argument("task_id", help="Id representing the specific task", type=str)
        subparser.add_argument("aws_id", help="Key used to communicate with AWS", type=str)
        subparser.add_argument("aws_key", help="Key used to communicate with AWS", type=str)
        # subparser.add_argument("--local", help="Run system locally", action="store_true")

    def run(self, args):
        super(RunCmd, self).run(args)
        self.aws_id = args.aws_id
        self.aws_key = args.aws_key
        self.task_id = args.task_id
        global LOCAL
        LOCAL = args.local

class CompileCmd(BaseCmd):
    cmd_name = 'compile'

    def __init__(self):
        super(BaseCmd).__init__()

    def parse_cmds(self, subparsers):
        subparser = super(CompileCmd, self).parse_cmds(subparsers, "Compile a StackHut service")
        subparser.add_argument('--bar')

    def run(self, args):
        pass


# StackHut primary commands
COMMANDS = [RunCmd(),
            CompileCmd(),
            # debug, push, pull, test, etc.
            ]

class RunCmd1(BaseCmd):
    def __init__(self):
        # setup AWS
        self.conn = S3Connection(self.aws_id, self.aws_key)
        self.bucket = self.conn.get_bucket('stackhut-payloads')

        # setup the service contracts
        self.contract = barrister.contract_from_file('./service.json')
        self.server = barrister.Server(self.contract)


    # called by service on startup
    #
    def _startup(self):
        logging.debug('Starting up service')

        if LOCAL:
            with open("./input.json", "r") as f:
                input_json_str = f.read()
        else:
            # download input.json from S3
            k = Key(self.bucket)
            k.key = '{}/input.json'.format(self.task_id)
            input_json_str = k.get_contents_as_string(encoding='UTF-8')
            logging.info("Downloaded input.json from S3")

        # now parse the json
        try:
            input_json = json.loads(input_json_str)
        except:
            raise ParseError()
        logging.info('Input - \n{}'.format(input_json))

        # using json, download any referenced files from s3 bucket? (or are they already there and we download bucket?)
        # in_filepaths = []

        # massage the JSON-RPC request
        # NOTE - this may not be entirely valid JSON-RPC - if so add the correct tags as needed
        default_service = input_json['serviceName']
        def _make_json_rpc(req):
            if 'jsonrpc' not in req:
                req['jsonrpc'] = "2.0"
            if 'id' not in req:
                req['id'] = str(uuid.uuid4())
            # add the default interface if none exists
            if req['method'].find('.') < 0:
                req['method'] = "{}.{}".format(default_service, req['method'])
            return req

        if 'req' in input_json:
            reqs = input_json['req']
            if type(reqs) is list:
                reqs = [_make_json_rpc(req) for req in reqs]
            else:
                reqs = _make_json_rpc(reqs)
        else:
            raise ParseError()

        return reqs  # anything else

    # called by service on exit - clean the system, write all output data and return control back to docker
    # intended to upload all files into S#
    def _shutdown(self, res):
        logging.info('Shutting down service')

        output_json = json.dumps(res)
        logging.info('Output - \n{}'.format(output_json))

        if LOCAL:
            with open("./output.json", "w") as f:
                f.write(output_json)
        else:
            # upload output.json to S3
            k = Key(self.bucket)
            k.key = '{}/output.json'.format(self.task_id)
            k.set_contents_from_string(output_json)
            logging.info("Uploaded output.json to S3")

            # upload output files to S3

            # send completion message to SQS ?

            # upload log to S3
            k.key = '{}/{}'.format(self.task_id, LOG_NAME)
            k.set_contents_from_filename(LOG_NAME)

    def add_handler(self, iname, impl):
        """Add a service handler to the system"""
        self.server.add_handler(iname, impl)

    def run_ext(self, method, params):
        """Make a pseudo-function call across languages"""
        # TODO - optimise
        # write the req
        req = dict(method=method, params=params)
        with open("./service_req.json", "w") as f:
            f.write(json.dumps(req))

        # select the stack
        stack = self.hutfile['stack']
        if stack == 'python3':
            shim_exe = '/usr/bin/python3'
        elif stack == 'nodejs':
            shim_exe = '/usr/bin/node'
        shim_cmd = [shim_exe, self.hutfile['entrypoint']]

        # call out to sub process
        try:
            subprocess.check_output(shim_cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise NonZeroExitError(e.returncode, e.output)

        # read and return the resp
        with open("./service_resp.json", "r") as f:
            resp = json.loads(f.read())
        # basic error handling
        if 'error' in resp:
            code = resp['error']
            if code == barrister.ERR_METHOD_NOT_FOUND:
                raise ServerError(code, "Method or service {} not found".format(method))
            else:
                raise ServerError(code, resp['msg'])
        # return if no issue
        return resp['result']

    def run(self):
        """Run the main rpc commands"""
        try:
            req = self._startup()
            resp = self.server.call(req, dict(callback=self.run_ext))
            self._shutdown(resp)
        except Exception as e:
            logging.exception("Shit, unhandled error! - {}".format(e))
            exit(1)

        # quit with correct exit code
        logging.info('Service call complete')
        exit(0)
