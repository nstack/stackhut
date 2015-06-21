from boto.s3.connection import S3Connection, Key
import json
import subprocess
import uuid

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
        log.debug('Starting up service')

        # get input
        input_json_str = self.file_store.get_string('input.json')
        try:
            input_json = json.loads(input_json_str)
        except:
            raise utils.ParseError()
        log.info('Input - \n{}'.format(input_json))

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
            raise utils.ParseError()

        return reqs  # anything else

    # called by service on exit - clean the system, write all output data and return control back to docker
    # intended to upload all files into S#
    def _shutdown(self, res):
        log.info('Shutting down service')
        output_json = json.dumps(res)
        log.info('Output - \n{}'.format(output_json))
        # save output and log
        self.file_store.put_string(output_json, 'output.json')
        self.file_store.put_file(utils.LOGFILE)

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
            raise utils.NonZeroExitError(e.returncode, e.output)

        # read and return the resp
        with open("./service_resp.json", "r") as f:
            resp = json.loads(f.read())
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
        if args.local:
            self.file_store = utils.LocalStore()
        else:
            self.file_store = utils.S3Store(args.task_id, args.aws_key, args.aws_id)

        # setup the service contracts
        self.contract = barrister.contract_from_file(utils.CONTRACTFILE)
        self.server = barrister.Server(self.contract)

        # Now run the main rpc commands
        try:
            req = self._startup()
            resp = self.server.call(req, dict(callback=self.run_ext))
            self._shutdown(resp)
        except Exception as e:
            log.exception("Shit, unhandled error! - {}".format(e))
            exit(1)

        # quit with correct exit code
        log.info('Service call complete')
        return 0

    # def add_handler(self, iname, impl):
    #     """Add a service handler to the system"""
    #     self.server.add_handler(iname, impl)
