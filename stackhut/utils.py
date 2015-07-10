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
import subprocess
import logging
from boto.s3.connection import Key, S3Connection
import sys
import abc
import os
import stat
import shutil
from itertools import cycle
import codecs
import redis
import pyconfig
import yaml
import json

from stackhut import barrister

# global constants
STACKHUT_DIR = '.stackhut'
CFGFILE = os.path.expanduser(os.path.join('~', '.stackhut.cfg'))
LOGFILE = '.stackhut.log'
HUTFILE = 'Hutfile'
CONTRACTFILE = os.path.join(STACKHUT_DIR, 'service.json')
IDLFILE = 'service.idl'
S3_BUCKET = 'stackhut-payloads'
ROOT_DIR = os.getcwd()

# Logging
def setup_logging():
    log = logging.getLogger('stackhut')
    log.propagate = False
    logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s', '%H:%M:%S')
    # file output
    fileHandler = logging.FileHandler(LOGFILE, mode='w')
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)
    # console
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
    return log

log = setup_logging()

def set_log_level(args_level):
    global log
    # setup the logger
    loglevel = logging.WARN
    if args_level == 1:
        loglevel = logging.INFO
    elif args_level >= 2:
        loglevel = logging.DEBUG
    log.setLevel(loglevel)


# setup app paths
# src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
res_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), './res'))
# f = open(os.path.join(os.path.dirname(__file__),'templates','file1.txt'))
#log.debug("StackHut src dir is {}".format(src_dir))
log.debug("StackHut res dir is {}".format(res_dir))
#pyconfig.set('src_dir', src_dir)
pyconfig.set('res_dir', res_dir)

def get_res_path(res_name):
    return (os.path.join(res_dir, res_name))


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


class IOStore:
    """A base wrapper wrapper around common IO task state"""
    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    @abc.abstractmethod
    def get_file(self, name):
        pass

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    def set_task_id(self, task_id):
        log.debug("Task id is {}".format(task_id))
        self.task_id = task_id


class CloudStore(IOStore):
    def __init__(self, service_name, aws_id, aws_key):
        self.service_name = service_name
        # open connection to AWS
        self.conn = S3Connection(aws_id, aws_key)
        self.bucket = self.conn.get_bucket(S3_BUCKET)

        redis_url = os.environ.get('REDIS_URL', 'localhost')
        log.debug("Connecting to Redis at {}".format(redis_url))
        self.redis = redis.StrictRedis(host=redis_url, port=6379, db=0, password=None,
                                       socket_timeout=None, connection_pool=None, charset='utf-8',
                                       errors='strict', unix_socket_path=None)
        self.redis.ping()
        log.debug("Connected to Redis")

    def get_request(self):
        """Get the request JSON"""
        log.debug("Waiting on queue for service - {}".format(self.service_name))
        x = self.redis.blpop(self.service_name, 0)[1].decode('utf-8')
        log.debug("Received message {}".format(x))
        return x

    def put_response(self, s):
        """Save the response JSON"""
        log.debug("Pushing task result")
        self.redis.lpush(self.task_id, s.encode('utf-8'))

    def _create_key(self, name):
        k = Key(self.bucket)
        k.key = '{}/{}'.format(self.task_id, name)
        return k

    def get_file(self, name):
        # k = self._create_key(name)
        # s = k.get_contents_as_string(encoding='utf-8')
        # log.info("Downloaded {} from S3".format(name))
        # return s
        pass

    def put_file(self, fname, req_id='', make_public=True):
        """Upload file to S3"""
        log.info("Uploading to S3")
        req_fname = os.path.join(req_id, fname)
        k = self._create_key(req_fname)
        k.set_contents_from_filename(req_fname)
        log.info("Uploaded {} to {} in S3".format(req_fname, k))

        if make_public:
            k.set_acl('public-read')
            k.make_public()
            return k.generate_url(expires_in=0, query_auth=False)
        else:
            return k.key

class LocalStore(IOStore):
    local_store = "local_task"

    def _get_path(self, name):
        return "{}/{}".format(self.local_store, name)

    def __init__(self, request_file):
        shutil.rmtree(self.local_store, ignore_errors=True)
        os.mkdir(self.local_store)
        # copy any files that should be there into the dir
        shutil.copy(request_file, self.local_store)
        self.request_file = self._get_path(request_file)

    def get_request(self):
        with open(self.request_file, "r") as f:
            x = f.read()
        return x

    def put_response(self, s):
        with open(self._get_path('output.json'), "w") as f:
            f.write(s)

    def get_file(self, name):
        pass

    def put_file(self, fname, req_id='', make_public=True):
        """Put file into a subdir keyed by req_id in local store"""
        req_fname = os.path.join(req_id, fname)
        local_store_dir = os.path.join(self.local_store, req_id)

        os.mkdir(local_store_dir) if not os.path.exists(local_store_dir) else None
        shutil.copy(req_fname, local_store_dir)
        return os.path.join(self.local_store, req_fname)


class StackHutCfg(dict):
    """Wrapper calss around dict that uses a json backing store"""
    def __init__(self):
        super().__init__()

        if os.path.exists(CFGFILE):
            with open(CFGFILE, 'r') as f:
                self.update(json.load(f))
                for v in self.encrypt_vals:
                    if v in self:
                        self[v] = self.xor_decrypt_string(self[v])
                        print(self[v])

    # Yes - this is shit crypto but jsut so we don't store plaintext on the fileystem
    # password sent over SSL to web regardless
    key = 'stackhut_is_G_dawg'
    encrypt_vals = ['password', 'token']

    def xor_crypt_string(self, plaintext):
        ciphertext = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(plaintext, cycle(self.key)))
        return (codecs.encode(ciphertext.encode('utf-8'), 'hex')).decode('utf-8')

    def xor_decrypt_string(self, ciphertext):
        ciphertext = (codecs.decode(ciphertext.encode('utf-8'), 'hex')).decode('utf-8')
        return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(ciphertext, cycle(self.key)))

    def save(self):
        for v in self.encrypt_vals:
            if v in self:
                self[v] = self.xor_crypt_string(self[v])

        # set cfg file permissions
        if not os.path.exists(CFGFILE):
            open(CFGFILE, 'w').close()
            os.chmod(CFGFILE, stat.S_IRUSR | stat.S_IWUSR)

        with open(CFGFILE, 'w') as f:
            json.dump(self, f)


class HutfileCfg:
    def __init__(self):
        # import the hutfile
        with open(HUTFILE, 'r') as f:
            hutfile = yaml.safe_load(f)

        # TODO - validatdation

        # get vals from the hutfile
        self.name = hutfile['name'].lower()
        self.author = hutfile['author'].lower()
        self.version = 'latest'
        self.email = hutfile['contact']
        self.description = hutfile['description']

        # copy files and dirs separetly
        files = hutfile.get('files', [])
        self.files = [f for f in files if os.path.isfile(f)]
        self.dirs = [d for d in files if os.path.isdir(d)]

        self.os_deps = hutfile.get('os_deps', [])
        self.docker_cmds = hutfile.get('docker_cmds', [])
        self.baseos = hutfile['baseos']
        self.stack = hutfile['stack']
        self.from_image = "{}-{}".format(self.baseos, self.stack)
        self.tag = "{}/{}:{}".format(self.author, self.name, self.version)


secure_url_prefix = "https://api.stackhut.com/"
unsecure_url_prefix = "http://api.stackhut.com/"
headers = {'content-type': 'application/json'}

import urllib.parse
import requests

def stackhut_api_call(endpoint, body, secure=False):
    url_prefix = secure_url_prefix if secure else unsecure_url_prefix
    url = urllib.parse.urljoin(url_prefix, endpoint)
    log.debug("Calling Stackhut {} with \n\t{}".format(endpoint, json.dumps(body)))
    r = requests.post(url, data=json.dumps(body), headers=headers)

    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        log.error("Error {} talking to stackhut server".format(r.status_code))
        log.error(r.text)
        r.raise_for_status()

def stackhut_api_secure_call(endpoint, body, usercfg):
    body['userName'] = usercfg['username']
    body['password'] = usercfg['password']
    return stackhut_api_call(endpoint, body, secure=True)
