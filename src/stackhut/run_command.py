import json
import subprocess
import uuid
import os
import shutil

import barrister
import stackhut.utils as utils
from stackhut.utils import log

class RunCmd(utils.BaseCmd):
    # called by service on startup
    def _startup(self):
        utils.log.debug('Starting up service')

        try:
            input_json = json.loads(self.get_request())
        except:
            raise utils.ParseError()
        log.info('Input - \n{}'.format(input_json))

        # massage the JSON-RPC request if we don't receieve an entirely valid req
        default_service = input_json['serviceName']

        def _make_json_rpc(req):
            req['jsonrpc'] = "2.0" if 'jsonrpc' not in req else req['jsonrpc']
            req['id'] = str(uuid.uuid4()) if 'id' not in req else req['id']
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

        return reqs  # anything else

    # called by service on exit - clean the system, write all output data and return control back to docker
    # intended to upload all files into S#
    def _shutdown(self, res):
        log.info('Shutting down service')
        log.info('Output - \n{}'.format(res))
        # save output and log
        self.put_response(json.dumps(res))
        self.put_file(utils.LOGFILE)

    service_req_json = 'service_req.json'
    service_resp_json = 'service_resp.json'

    def run_ext(self, method, params):
        """Make a pseudo-function call across languages"""
        # TODO - optimise
        # write the req
        req = dict(method=method, params=params)
        with open(self.service_req_json, "w") as f:
            f.write(json.dumps(req))

        # call out to sub process
        try:
            subprocess.check_output(self.shim_cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise utils.NonZeroExitError(e.returncode, e.output)

        # read and return the resp
        with open(self.service_resp_json, "r") as f:
            resp = json.loads(f.read())

        # cleanup
        os.remove(self.service_req_json)
        os.remove(self.service_resp_json)

        # basic error handling
        if 'error' in resp:
            code = resp['error']
            if code == barrister.ERR_METHOD_NOT_FOUND:
                raise utils.ServerError(code, "Method or service {} not found".format(method))
            else:
                raise utils.ServerError(code, resp['msg'])
        # return if no issue
        return resp['result']

    def run(self):
        super().run()

        # setup the service contracts
        self.contract = barrister.contract_from_file(utils.CONTRACTFILE)
        self.server = barrister.Server(self.contract)

        # select the stack
        stack = self.hutfile['stack']
        shim_file = None
        if stack == 'python3':
            shim_exe = ['/usr/bin/python3']
            shim_file = 'stackrun.py'
        elif stack == 'nodejs':
            shim_exe = ['/usr/bin/iojs', '--harmony']
            shim_file = 'stackrun.js'
        else:
            log.error("Unknown stack")
            return 1

        shutil.copy(os.path.join(self.shim_dir, shim_file), os.getcwd())
        self.shim_cmd = shim_exe + [shim_file]

        # Now run the main rpc commands
        try:
            req = self._startup()
            resp = self.server.call(req, dict(callback=self.run_ext))
            self._shutdown(resp)
        except Exception as e:
            log.exception("Shit, unhandled error! - {}".format(e))
            exit(1)
        finally:
            os.remove(os.path.join(os.getcwd(), shim_file))

        # quit with correct exit code
        log.info('Service call complete')
        return 0


class RunLocalCmd(RunCmd, utils.LocalStore):
    cmd_name = 'runlocal'

    def __init__(self, args):
        utils.LocalStore.__init__(self, args.infile)
        RunCmd.__init__(self, args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunLocalCmd, RunLocalCmd).parse_cmds(subparser, 'runlocal', "Run a StackHut service locally", RunLocalCmd)
        subparser.add_argument("--infile", '-i', default='input.json',
                               help="Local file to use for input")

class RunCloudCmd(RunCmd, utils.CloudStore):
    cmd_name = 'run'

    def __init__(self, args):
        super(RunCmd, self).__init__(args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(RunCloudCmd, RunCloudCmd).parse_cmds(subparser, 'run', "Run a StackHut service", RunCloudCmd)
        subparser.add_argument("task_id", help="Id representing the specific task")
        subparser.add_argument("aws_id", help="Key used to communicate with AWS")
        subparser.add_argument("aws_key", help="Key used to communicate with AWS")


