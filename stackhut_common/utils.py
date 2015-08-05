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
import logging
import sys
import os
import json
from colorlog import ColoredFormatter
from . import barrister

####################################################################################################
# App Config
# global constants
CONTRACTFILE = '.api.json'
IDLFILE = 'api.idl'
DEBUG = None
IN_CONTAINER = os.path.exists('/workdir')
VERBOSE = False
ROOT_DIR = os.getcwd()

# Logging
# LOGFILE = '.stackhut.log'
logging.getLogger().disabled = True
logging.getLogger('werkzeug').disabled = True

log = logging.getLogger('stackhut')
def setup_logging(verbose_mode):
    global VERBOSE
    global log
    VERBOSE = verbose_mode
    log.propagate = False
    log.setLevel(logging.DEBUG if verbose_mode else logging.INFO)

    logFormatter = ColoredFormatter(
        '%(blue)s%(asctime)s%(reset)s [%(log_color)s%(levelname)-5s%(reset)s] %(message)s',
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # file output
    # fileHandler = logging.FileHandler(LOGFILE, mode='w')
    # fileHandler.setFormatter(logFormatter)
    # log.addHandler(fileHandler)

    # console
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)

####################################################################################################
# Error handling
class ParseError(barrister.RpcException):
    def __init__(self, data=None):
        code = -32700
        msg = 'Parse Error'
        data = {} if data is not None else data
        super().__init__(code, msg, data)

class InternalError(barrister.RpcException):
    def __init__(self, data=None):
        code = -32603
        msg = 'Internal Error'
        data = {} if data is not None else data
        super().__init__(code, msg, data)

class ServerError(barrister.RpcException):
    def __init__(self, code, msg, data=None):
        code = code
        msg = 'Internal Service Error - {}'.format(msg)
        data = {} if data is not None else data
        super().__init__(code, msg, data)

class NonZeroExitError(barrister.RpcException):
    def __init__(self, exitcode, stderr):
        code = -32001
        msg = 'Service sub-command returned a non-zero exit'
        data = dict(exitcode=exitcode, stderr=stderr)
        super().__init__(code, msg, data)

def gen_error_resp(req_id, e):
    resp = barrister.err_response(req_id, e.code, e.msg, e.data)
    return json.dumps(resp)
