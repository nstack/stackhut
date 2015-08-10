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
"""
StackHut interface and modifications to Barrister RPC library
"""
import os
import subprocess
import json
import uuid
import signal
import contextlib
import sh

from .barrister.runtime import contract_from_file, RpcException
from .barrister.runtime import err_response, ERR_PARSE, ERR_INVALID_REQ, ERR_METHOD_NOT_FOUND, \
    ERR_INVALID_PARAMS, ERR_INTERNAL, ERR_UNKNOWN, ERR_INVALID_RESP
from .barrister.parser import parse
from .utils import log

CONTRACTFILE = '.api.json'
IDLFILE = 'api.idl'
REQ_FIFO = 'req.json'
RESP_FIFO = 'resp.json'

def generate_contract():
    """
    Generate the IDL -> JSON Contract file
    main interface into barrister parser
    """
    with open(IDLFILE, 'r') as idl_file:
        parsed = parse(idl_file, IDLFILE)

    with open(CONTRACTFILE, "w") as contract_file:
        contract_file.write(json.dumps(parsed))


####################################################################################################
# Error handling
class ParseError(RpcException):
    def __init__(self, data=None):
        super().__init__(ERR_PARSE, 'Parse Error', data)

class InvalidReqError(RpcException):
    def __init__(self, data=None):
        super().__init__(ERR_INVALID_REQ, 'Invalid Request', data)

class MethodNotFoundError(RpcException):
    def __init__(self, data=None):
        super().__init__(ERR_METHOD_NOT_FOUND, 'Method Not Found', data)

class InternalError(RpcException):
    def __init__(self, data=None):
        super().__init__(ERR_INTERNAL, 'Internal Error', data)

class CustomError(RpcException):
    def __init__(self, code, msg, data=None):
        super().__init__(code, 'Error - {}'.format(msg), data)

class NonZeroExitError(RpcException):
    def __init__(self, exitcode, stderr):
        data = dict(exitcode=exitcode, stderr=stderr)
        super().__init__(-32001, 'Sub-command returned a non-zero exit', data)

def exc_to_json_error(e, req_id=None):
    log.error(e)
    return err_response(req_id, e.code, e.msg, e.data)

from enum import Enum

class SHCmds(Enum):
    startup = 1
    shutdown = 2
    preBatch = 3
    postBatch = 4


class StackHutRPC:
    """
    Alt. implementation of Barrister.server modified for StackHut needs
    Performs
    * 'Type'-checking of requests and responces per interface def
    * loading the lang-specfic shim/client
    * passing messages between the runner and shim/client process
    """

    def __init__(self, backend, shim_cmd):
        self.contract = contract_from_file(CONTRACTFILE)
        self.backend = backend

        # setup fifos
        os.mkfifo(REQ_FIFO)
        os.mkfifo(RESP_FIFO)

        # run the shim
        cmd = sh.Command(shim_cmd[0])
        self.p = cmd(shim_cmd[1:], _bg=True, _out=lambda x: log.debug("Runner - {}".format(x.rstrip())),
                     _err=lambda x: log.error("Runner - {}".format(x.rstrip())))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        def handler(signum, frame):
            log.error("Force-quitting subprocess")
            self.p.kill()
            raise TimeoutError()

        # Set the signal handler and a 5-second alarm
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(5)

        # send shutdown msg to each iface
        for iface in self.contract.interfaces.keys():
            log.debug("Send shutdown to {}".format(iface))
            self._cmd_call('{}.{}'.format(iface, SHCmds.shutdown.name))

        log.debug("Terminating RPC sub-process")
        self.p.terminate()
        self.p.wait()
        signal.alarm(0)

    def call(self, task_req):
        """Make RPC call for given task"""
        # Massage the data
        self._add_id(task_req, 'id')
        self.backend.set_task_id(task_req['id'])

        req = task_req['request']
        if type(req) is list:
            if len(req) < 1:
                return exc_to_json_error(InvalidReqError(data=dict(msg="Empty Batch")))

            # find batch interface
            iface_name = None
            first_method = req[0].get('method', None)
            if first_method:
                iface_name = 'Default' if first_method.find('.') < 0 else first_method.split('.')[0]
            if iface_name:
                self._cmd_call('{}.{}'.format(iface_name, SHCmds.preBatch.name))

            task_resp = [self._req_call(r) for r in req]

            if iface_name:
                self._cmd_call('{}.{}'.format(iface_name, SHCmds.postBatch.name))
        else:
            task_resp = self._req_call(req)
        return task_resp

    def _cmd_call(self, cmd):
        log.debug('Sending cmd message - {}'.format(cmd))
        self._sub_call(cmd, [], 'shcmd')

    def _add_id(self, d, v):
        d[v] = str(uuid.uuid4()) if v not in d else str(d[v])

    def _req_call(self, req):
        """Make RPC call for a single request"""
        req_id = None
        try:
            if type(req) is not dict:
                raise InvalidReqError(dict(msg="%s is not an object.".format(req)))

            # massage the data (if needed)
            self._add_id(req, 'id')
            req_id = req['id']

            if 'jsonrpc' not in req: req['jsonrpc'] = "2.0"
            if "method" not in req:
                raise InvalidReqError(dict(msg="No method"))
            # return the idl - TODO - move into Scala
            if req['method'] == "common.barrister-idl" or req['method'] == "getIdl":
                return self.contract.idl_parsed
            # add the default interface if none exists
            if req['method'].find('.') < 0:
                req['method'] = "{}.{}".format('Default', req['method'])

            # NOTE - would setup context and run pre/post filters here in Barrister
            # Ok, - we're good to go
            method = req["method"]
            iface_name, func_name = method.split('.')
            params = req.get('params', [])

            self.contract.validate_request(iface_name, func_name, params)
            result = self._sub_call(method, params, req_id)
            self.contract.validate_response(iface_name, func_name, result)
            resp = dict(jsonrpc="2.0", id=req_id, result=result)

        except RpcException as e:
            resp = exc_to_json_error(e, req_id)
        except Exception as e:
            _e = InternalError(dict(exception=str(e)))
            resp = exc_to_json_error(_e, req_id)
        return resp

    def _sub_call(self, method, params, req_id):
        """Acutal call to the shim/client subprocess"""
        self.backend.new_request_path(req_id)
        # create the (sub-)req
        sub_req = dict(method=method, params=params, req_id=req_id)
        # blocking-wait to send the request
        with open(REQ_FIFO, "w") as f:
            f.write(json.dumps(sub_req))

        # blocking-wait to read the resp
        with open(RESP_FIFO, "r") as f:
            sub_resp = json.loads(f.read())

        # check the response
        if 'error' in sub_resp:
            code = sub_resp['error']
            if code == ERR_METHOD_NOT_FOUND:
                raise MethodNotFoundError()
            else:
                raise CustomError(code, sub_resp['msg'])

        # validate and return the response
        result = sub_resp['result']
        return result

