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
import json
import subprocess
import uuid
import os
import sh
import shutil
import argparse

from stackhut.common import barrister
from stackhut.common import utils
from stackhut.common.utils import log, CloudStore, LocalStore, HutCmd
from . import shim_server
from stackhut.common.primitives import gen_barrister_contract, stacks

# Module Consts
REQ_FIFO = 'req.json'
RESP_FIFO = 'resp.json'

class RunCmd(HutCmd):
    """Base Run Command functionality"""

    def __init__(self, args):
        super().__init__(args)
        # select the stack
        self.stack = stacks.get(self.hutcfg.stack)
        if self.stack is None:
            log.error("Unknown stack - {}".format(self.hutcfg.stack))
            exit(1)

    def run(self):
        super().run()

        # called by service on startup
        def _startup():
            log.debug('Starting up service')

            # setup the service contracts
            contract = barrister.contract_from_file(utils.CONTRACTFILE)
            self.server = barrister.Server(contract)

            # startup the local helper service
            shim_server.init(self.store)

            # (blocking) get/wait for a request
            try:
                in_str = self.store.get_request()
                input_json = json.loads(in_str)
            except:
                raise utils.ParseError()
            log.info('Input - \n{}'.format(input_json))

            def gen_id(d, v):
                d[v] = str(uuid.uuid4()) if v not in d else str(d[v])

            # massage the JSON-RPC request if we don't receive an entirely valid req
            default_service = 'Default'  # input_json['serviceName']
            gen_id(input_json, 'id')
            self.store.set_task_id(input_json['id'])

            def _make_json_rpc(req):
                if 'jsonrpc' not in req: req['jsonrpc'] = "2.0"
                gen_id(req, 'id')
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
                raise utils.ParseError()

            os.remove(REQ_FIFO) if os.path.exists(REQ_FIFO) else None
            os.remove(RESP_FIFO) if os.path.exists(RESP_FIFO) else None
            os.mkfifo(REQ_FIFO)
            os.mkfifo(RESP_FIFO)

            self.stack.copy_shim()
            return reqs  # anything else

        # called by service on exit - clean the system, write all output data and return control back to docker
        # intended to upload all files into S#
        def _shutdown(res):
            log.info('Output - \n{}'.format(res))
            log.info('Shutting down service')
            # save output and log
            self.store.put_response(json.dumps(res))
            self.store.put_file(utils.LOGFILE)

        def _run_ext(method, params, req_id):
            """Make a pseudo-function call across languages"""
            # TODO - optimise
            # make dir to hold any output
            req_path = os.path.join(utils.STACKHUT_DIR, req_id)
            os.mkdir(req_path) if not os.path.exists(req_path) else None

            # create the req
            req = dict(method=method, params=params, req_id=req_id)

            # run the shim
            # TODO - move this into init so shim is already loadade and waiting
            p = subprocess.Popen(self.stack.shim_cmd, shell=False, stderr=subprocess.STDOUT)

            # blocking-wait to send the request
            with open(REQ_FIFO, "w") as f:
                f.write(json.dumps(req))
            # blocking-wait to read the resp
            with open(RESP_FIFO, "r") as f:
                resp = json.loads(f.read())

            # now wait for completion
            # TODO - is this needed?
            p.wait()
            if p.returncode != 0:
                raise utils.NonZeroExitError(p.returncode, p.stdout)

            log.debug(resp)
            # basic error handling
            if 'error' in resp:
                code = resp['error']
                if code == barrister.ERR_METHOD_NOT_FOUND:
                    raise utils.ServerError(code, "Method or service {} not found".format(method))
                else:
                    raise utils.ServerError(code, resp['msg'])
            # return if no issue
            return resp['result']

        # Now run the main rpc toolkit.commands
        try:
            reqs = _startup()
            resp = self.server.call(reqs, dict(callback=_run_ext))
            _shutdown(resp)
        except Exception as e:
            log.exception("Shit, unhandled error! - {}".format(e))
            exit(1)
        finally:
            # cleanup
            self.stack.del_shim()
            os.remove(REQ_FIFO)
            os.remove(RESP_FIFO)
            os.remove(utils.LOGFILE)

        # quit with correct exit code
        log.info('Service call complete')
        return 0


class RunLocalCmd(RunCmd):
    """"Concrete Run Command using local files for dev"""
    name = 'run'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunLocalCmd, RunLocalCmd).parse_cmds(subparser,
                                                               RunLocalCmd.name,
                                                               "Run StackHut service locally",
                                                               RunLocalCmd)
        subparser.add_argument("reqfile", nargs='?', default='test_request.json',
                               help="Test request file to use")
        subparser.add_argument("--container", '-c', action='store_true',
                               help="Run and test the service inside the container (requires you run build first)")
        subparser.add_argument("--uid", '-u', #default='0:0',
                               help="uid:gid to chown the run_results dir to")
        subparser.add_argument("--server-only", '-s', action='store_true',
                               help="Run and test the stackhut shim server only)")

    def __init__(self, args):
        super().__init__(args)
        self.reqfile = args.reqfile
        self.container = args.container
        self.server_only = args.server_only
        self.uid_gid = args.uid
        self.store = LocalStore(args.reqfile, args.uid)

    def run(self):
        if self.container:
            usercfg = utils.StackHutCfg()
            tag = self.hutcfg.tag(usercfg)
            host_req_file = os.path.abspath(self.reqfile)
            host_store_dir = os.path.abspath(self.store.local_store)
            uid_gid = '{}:{}'.format(os.getuid(), os.getgid())

            log.info("Running service with {} in container - log below...".format(self.reqfile))
            # call docker to run the same command but in the container
            # use data vols for req and run_output

            flag = 'z' if utils.OS_TYPE == 'SELINUX' else 'rw'
            out = sh.docker.run('-v', '{}:/workdir/test_request.json:ro'.format(host_req_file),
                                '-v', '{}:/workdir/{}:{}'.format(host_store_dir, self.store.local_store, flag),
                                '--entrypoint=/usr/bin/stackhut', tag, '-vv', 'run', '--uid', uid_gid,
                                _out=lambda x: print(x, end=''))
            log.info("...finished service in container")

        elif self.server_only:
            # startup the local helper service
            t = shim_server.init(self.store, False)

            self.store.set_task_id(str(uuid.uuid4()))
            self.stack.copy_shim()
#            t.join()

        else:
            if not utils.IN_CONTAINER:
                # make sure have latest idl
                gen_barrister_contract()
            super().run()
            self.store.cleanup()


class RunCloudCmd(RunCmd):
    """Concrete Run Command using Cloud systems for prod"""

    name = 'runcloud'
    visible = False

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunCloudCmd, RunCloudCmd).parse_cmds(subparser,
                                                               RunCloudCmd.name,
                                                               "(internal) Run StackHut service on host",
                                                               RunCloudCmd)

    def __init__(self, args):
        super().__init__(args)
        self.store = CloudStore(self.hutcfg.name)


# StackHut primary run commands
COMMANDS = [
    RunLocalCmd, RunCloudCmd,
]
