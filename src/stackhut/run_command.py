import json
import subprocess
import uuid
import os
import shutil

import barrister
import stackhut.utils as utils
from stackhut.utils import log

class RunCmd(utils.BaseCmd):
    cmd_name = 'run'

    def parse_cmds(self, subparsers):
        subparser = super().parse_cmds(subparsers, "Run a StackHut service")
        subparser.add_argument("task_id", help="Id representing the specific task", nargs='?')
        subparser.add_argument("aws_id", help="Key used to communicate with AWS", nargs='?')
        subparser.add_argument("aws_key", help="Key used to communicate with AWS", nargs='?')
        subparser.add_argument("--local", help="Run service locally", action="store_true")

    # called by service on startup
    def _startup(self):
        utils.log.debug('Starting up service')

        try:
            input_json = json.loads(self.file_store.get_string('input.json'))
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
        self.file_store.put_string(json.dumps(res), 'output.json')
        self.file_store.put_file(utils.LOGFILE)

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

    def run(self, args):
        super().run(args)

        # HACK - bail out on args here - should be handled by argparse
        if args.local:
            self.file_store = utils.LocalStore()
        elif args.task_id and args.aws_key and args.aws_key:
            self.file_store = utils.S3Store(args.task_id, args.aws_key, args.aws_id)
        else:
            log.error("Missing arguments, run with --help")
            return 1

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

    # def add_handler(self, iname, impl):
    #     """Add a service handler to the system"""
    #     self.server.add_handler(iname, impl)
