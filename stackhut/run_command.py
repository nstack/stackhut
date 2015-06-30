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
from __future__ import (unicode_literals, print_function, division, absolute_import)
from future import standard_library

standard_library.install_aliases()
from builtins import *
import json
import subprocess
import uuid
import os
import shutil

from stackhut import barrister
from stackhut import utils
from stackhut.utils import log, HutCmd, CloudStore, LocalStore


# Module Consts
REQ_FIFO = 'req.json'
RESP_FIFO = 'resp.json'

class RunCmd(HutCmd):
    """Base Run Command functionality"""
    def __init__(self, args):
        HutCmd.__init__(self, args)

        # setup the service contracts
        contract = barrister.contract_from_file(utils.CONTRACTFILE)
        self.server = barrister.Server(contract)

        # select the stack
        stack = self.hutfile['stack']
        if stack == 'python':
            self.shim_exe = ['/usr/bin/env', 'python3']
            self.shim_file = 'stackrun3.py'
        elif stack == 'python2':
            self.shim_exe = ['/usr/bin/env', 'python2']
            self.shim_file = 'stackrun2.py'
        elif stack == 'nodejs':
            self.shim_exe = ['/usr/bin/env', 'iojs', '--harmony']
            self.shim_file = 'stackrun.js'
        else:
            log.error("Unknown stack")
            exit(1)
        # copy across the shim file
        shutil.copy(os.path.join(utils.get_res_path('shims'), self.shim_file), os.getcwdu())
        self.shim_cmd = self.shim_exe + [self.shim_file]

    def run(self):
        super().run()

        # called by service on startup
        def _startup():
            log.debug('Starting up service')

            try:
                in_str = self.get_request()
                input_json = json.loads(in_str)
            except:
                raise utils.ParseError()
            log.info('Input - \n{}'.format(input_json))

            # massage the JSON-RPC request if we don't receieve an entirely valid req
            default_service = input_json['serviceName']
            self.set_task_id(input_json['id'])

            def _make_json_rpc(req):
                req['jsonrpc'] = "2.0" if 'jsonrpc' not in req else req['jsonrpc']
                req['id'] = str(uuid.uuid4()) if 'id' not in req else req['id']
                # add the default interface if none exists
                if req['method'].find('.') < 0:
                    req['method'] = "{}.{}".format(default_service, req['method'])
                return req

            if 'req' in input_json:
                reqs = input_json['req']
                if isinstance(reqs, list): # HACK
                    reqs = [_make_json_rpc(req) for req in reqs]
                else:
                    reqs = _make_json_rpc(reqs)
            else:
                raise utils.ParseError()

            os.remove(REQ_FIFO) if os.path.exists(REQ_FIFO) else None
            os.remove(RESP_FIFO) if os.path.exists(RESP_FIFO) else None
            os.mkfifo(REQ_FIFO)
            os.mkfifo(RESP_FIFO)

            return reqs  # anything else

        # called by service on exit - clean the system, write all output data and return control back to docker
        # intended to upload all files into S#
        def _shutdown(res):
            log.info('Output - \n{}'.format(res))
            log.info('Shutting down service')
            # save output and log
            self.put_response(json.dumps(res))
            self.put_file(utils.LOGFILE)
            # cleanup
            os.remove(REQ_FIFO)
            os.remove(RESP_FIFO)
            os.remove(utils.LOGFILE)

        def _run_ext(method, params):
            """Make a pseudo-function call across languages"""
            # TODO - optimise
            # write the req
            req = dict(method=method, params=params)

            # call out to sub process
            p = subprocess.Popen(self.shim_cmd, shell=False, stderr=subprocess.STDOUT)
            # blocking-wait to send the request
            with open(REQ_FIFO, "w") as f:
                f.write(unicode(json.dumps(req)))
            # blocking-wait to read the resp
            with open(RESP_FIFO, "r") as f:
                resp = json.loads(f.read())

            # now wait for completion
            # TODO - is this needed?
            p.wait()
            if p.returncode != 0:
                raise utils.NonZeroExitError(p.returncode, p.stdout)

            # basic error handling
            if 'error' in resp:
                code = resp['error']
                if code == barrister.ERR_METHOD_NOT_FOUND:
                    raise utils.ServerError(code, "Method or service {} not found".format(method))
                else:
                    raise utils.ServerError(code, resp['msg'])
            # return if no issue
            return resp['result']

        # Now run the main rpc commands
        try:
            req = _startup()
            resp = self.server.call(req, dict(callback=_run_ext))
            _shutdown(resp)
        except Exception as e:
            log.exception("Shit, unhandled error! - {}".format(e))
            exit(1)
        finally:
            os.remove(os.path.join(os.getcwdu(), self.shim_file))

        # quit with correct exit code
        log.info('Service call complete')
        return 0


class RunLocalCmd(RunCmd, LocalStore):
    """"Concrete Run Command using local files for dev"""

    def __init__(self, args):
        LocalStore.__init__(self, args.infile)
        RunCmd.__init__(self, args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunLocalCmd, RunLocalCmd).parse_cmds(subparser,
                                                               'runlocal', "Run a StackHut service locally", RunLocalCmd)
        subparser.add_argument("--infile", '-i', default='example_request.json',
                               help="Local file to use for input")

class RunCloudCmd(RunCmd, CloudStore):
    """Concrete Run Command using Cloud systems for prod"""

    def __init__(self, args):
        RunCmd.__init__(self, args)
        CloudStore.__init__(self, self.hutfile['name'], args.aws_id, args.aws_key)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunCloudCmd, RunCloudCmd).parse_cmds(subparser, 'run', "Run a StackHut service", RunCloudCmd)
        subparser.add_argument("aws_id", help="Key used to communicate with AWS")
        subparser.add_argument("aws_key", help="Key used to communicate with AWS")
