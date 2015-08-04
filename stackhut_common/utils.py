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
from . import barrister
import abc
import os
from colorlog import ColoredFormatter

####################################################################################################
# App Config
# global constants
STACKHUT_DIR = '.stackhut'
CONTRACTFILE = os.path.join('.api.json')
IDLFILE = 'api.idl'
DEBUG = None
IN_CONTAINER = os.path.exists('/workdir')
VERBOSE = False
ROOT_DIR = os.getcwd()
S3_BUCKET = 'stackhut-payloads'

# Logging
# LOGFILE = '.stackhut.log'
log = logging.getLogger('stackhut')
def setup_logging(verbose_mode):
    global VERBOSE
    global log
    VERBOSE = verbose_mode
    log.propagate = False
    #logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')

    logFormatter = ColoredFormatter(
        # "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
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
    log.setLevel(logging.DEBUG if verbose_mode else logging.INFO)

####################################################################################################
# Error handling
class ParseError(barrister.RpcException):
    def __init__(self, data=None):
        code = -32700
        msg = 'Parse Error'
        data = {} if data is not None else data
        super(ParseError, self).__init__(code, msg, data)

class InternalError(barrister.RpcException):
    def __init__(self, data=None):
        code = -32603
        msg = 'Internal Error'
        data = {} if data is not None else data
        super(InternalError, self).__init__(code, msg, data)

class ServerError(barrister.RpcException):
    def __init__(self, code, msg, data=None):
        code = code
        msg = 'Internal Service Error - {}'.format(msg)
        data = {} if data is not None else data
        super(ServerError, self).__init__(code, msg, data)

class NonZeroExitError(barrister.RpcException):
    def __init__(self, exitcode, stderr):
        code = -32001
        msg = 'Service sub-command returned a non-zero exit'
        data = dict(exitcode=exitcode, stderr=stderr)
        super(NonZeroExitError, self).__init__(code, msg, data)


###################################################################################################
# StackHut IO Handling on local and cloud backends

def get_req_dir(req_id):
    return os.path.join(STACKHUT_DIR, req_id)

def get_req_file(req_id, fname):
    return os.path.join(STACKHUT_DIR, req_id, fname)

class IOStore:
    """A base wrapper wrapper around common IO task state"""
    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    def get_file(self, name):
        raise NotImplementedError("IOStore.get_file called")

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    def set_task_id(self, task_id):
        log.debug("Task id is {}".format(task_id))
        self.task_id = task_id

