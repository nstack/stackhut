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
from boto.s3.connection import Key, S3Connection
import sys
import abc
import os
import stat
import threading
import shutil
from itertools import cycle
import codecs
import sh
import redis
import yaml
import json
from . import barrister
# import pyconfig

####################################################################################################
# App Config
# global constants
STACKHUT_DIR = '.stackhut'
CFGFILE = os.path.expanduser(os.path.join('~', '.stackhut.cfg'))
LOGFILE = '.stackhut.log'
HUTFILE = 'Hutfile'
CONTRACTFILE = os.path.join('.api.json')
IDLFILE = 'api.idl'
S3_BUCKET = 'stackhut-payloads'
ROOT_DIR = os.getcwd()
DEBUG = None
IN_CONTAINER = os.path.exists('/workdir')
VERBOSE=False

# OS Types - for docker flags
OS_TYPE = None
try:
    os_str = (str(sh.lsb_release('-i', '-s'))).strip()
    if os_str in ['Fedora']:
        OS_TYPE = 'SELINUX'
    else:
        OS_TYPE = 'UNKNOWN'
except sh.CommandNotFound as e:
    OS_TYPE = 'UNKNOWN'

# Logging
def setup_logging():
    log = logging.getLogger('stackhut')
    log.propagate = False
    logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')
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

def set_log_level(verbose_mode):
    global log
    global VERBOSE
    VERBOSE = verbose_mode
    log.setLevel(logging.DEBUG if verbose_mode else logging.INFO)

# Setup app paths
# src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
sys_dir = None
if getattr(sys, 'frozen', False):
    # The application is frozen
    sys_dir = os.path.dirname(sys.executable)
else:
    # The application is not frozen
    sys_dir = os.path.dirname(__file__)
res_dir = os.path.normpath(os.path.join(sys_dir, '../res'))
# f = open(os.path.join(os.path.dirname(__file__),'templates','file1.txt'))
#log.debug("StackHut src dir is {}".format(src_dir))
log.debug("StackHut res dir is {}".format(res_dir))
#pyconfig.set('src_dir', src_dir)
#pyconfig.set('res_dir', res_dir)

def get_res_path(res_name):
    return os.path.join(res_dir, res_name)

def get_req_dir(req_id):
    return os.path.join(STACKHUT_DIR, req_id)

def get_req_file(req_id, fname):
    return os.path.join(STACKHUT_DIR, req_id, fname)

def create_stackhut_dir():
    os.mkdir(STACKHUT_DIR) if not os.path.exists(STACKHUT_DIR) else None

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
class ControlListener(threading.Thread):
    """Listener listens for requests on Redis Control channel common to all services"""
    def __init__(self, store, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.pubsub = store.redis.pubsub()
        self.pubsub.subscribe(['{}-control'.format(store.service_fullname)])
        self.can_quit = True
        self.cv = threading.Condition()

    def run(self):
        # infinite loop on listen channel generator
        for item in self.pubsub.listen():
            log.debug(item)
            if item['type'] == 'message':
                if item['data'] == b"KILL":
                    self.pubsub.unsubscribe()
                    with self.cv:
                        self.cv.wait_for(lambda: self.can_quit)
                        log.debug("Shutting down on KILL request")
                        os._exit(os.EX_OK)
                else:
                    log.error("Got unknown message on control channel - \n\t{}".format(item))
                    os._exit(os.EX_DATAERR)

    # NOTE - this is not thread-safe in case of control msg received 1st, then data msg on blpop
    # channel during shutdown itself - will result in a lost message but unlikely to occur.
    # Solve by putting blpop on another thread and sync between them
    def stop(self):
        with self.cv:
            self.can_quit = False
            self.cv.notify_all()  # this is not needed - as will never run again

class IOStore:
    """A base wrapper wrapper around common IO task state"""
    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    def get_file(self, name):
        log.error("Store.get_file called")

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    def set_task_id(self, task_id):
        log.debug("Task id is {}".format(task_id))
        self.task_id = task_id

class CloudStore(IOStore):
    """Main storage subsytem for use in prod env"""
    def _get_env(self, k):
        v = os.environ.get(k, None)
        del os.environ[k]
        return v

    def __init__(self, service_fullname):
        self.service_fullname = service_fullname

        # open connection to AWS
        aws_id = self._get_env('AWS_ID')
        aws_key = self._get_env('AWS_KEY')
        self.conn = S3Connection(aws_id, aws_key)
        self.bucket = self.conn.get_bucket(S3_BUCKET)
        log.debug("Connected to AWS S3")

        # open connection to Redis
        redis_url = self._get_env('REDIS_URL')
        self.redis = redis.StrictRedis(host=redis_url, port=6379, db=0, password=None,
                                       socket_timeout=None, connection_pool=None, charset='utf-8',
                                       errors='strict', unix_socket_path=None)
        self.redis.ping()
        log.debug("Connected to Redis")

        # setup control listener on sep thread
        self.control = ControlListener(self, daemon=True)
        self.control.start()

    def get_request(self):
        """Get the request JSON"""
        log.debug("Waiting on queue for service - {}".format(self.service_fullname))
        x = self.redis.blpop(self.service_fullname, 0)[1].decode('utf-8')
        # shutdown control listener
        self.control.stop()
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

    # def get_file(self, name):
    #     # k = self._create_key(name)
    #     # s = k.get_contents_as_string(encoding='utf-8')
    #     # log.info("Downloaded {} from S3".format(name))
    #     # return s

    def put_file(self, fname, req_id='', make_public=True):
        """Upload file to S3"""
        log.info("Uploading to S3")
        k = self._create_key(os.path.join(req_id, fname))

        if req_id == '':
            req_fname = fname
        else:
            req_fname = get_req_file(req_id, fname)

        k.set_contents_from_filename(req_fname)

        log.info("Uploaded {} to {} in S3".format(req_fname, k))

        if make_public:
            k.set_acl('public-read')
            k.make_public()
            return k.generate_url(expires_in=0, query_auth=False)
        else:
            return k.key

class LocalStore(IOStore):
    """Mock storage system for local testing"""
    local_store = "run_result"

    def _get_path(self, name):
        return "{}/{}".format(self.local_store, name)

    def __init__(self, request_file, uid_gid=None):
        self.uid_gid = uid_gid
        # delete and recreate local_store
        shutil.rmtree(self.local_store, ignore_errors=True)
        if not os.path.exists(self.local_store):
            os.mkdir(self.local_store)

        # copy any files that should be there into the dir
        shutil.copy(request_file, self.local_store)
        self.request_file = self._get_path(request_file)

    def cleanup(self):
        # change the results owner
        if self.uid_gid is not None:
            sh.chown('-R', self.uid_gid, self.local_store)

    def get_request(self):
        with open(self.request_file, "r") as f:
            x = f.read()
        return x

    def put_response(self, s):
        with open(self._get_path('response.json'), "w") as f:
            f.write(s)

    # def get_file(self, name):
    #     pass

    def put_file(self, fname, req_id='', make_public=True):
        """Put file into a subdir keyed by req_id in local store"""
        if req_id == '':
            req_fname = fname
        else:
            req_fname = get_req_file(req_id, fname)

        local_store_dir = self._get_path(req_id)

        os.mkdir(local_store_dir) if not os.path.exists(local_store_dir) else None
        shutil.copy(req_fname, local_store_dir)
        return os.path.join(local_store_dir, fname)

class UserCfg(dict):
    """
    UserConfig configuration handling
    Wrapper class around dict that uses a json backing store
    """
    def __init__(self):
        super().__init__()

        if os.path.exists(CFGFILE):
            with open(CFGFILE, 'r') as f:
                self.update(json.load(f))
                for v in self.encrypt_vals:
                    if v in self:
                        self[v] = self.xor_decrypt_string(self[v])

    # Yes - this is shit crypto but just so we don't store plaintext on the fileystem
    # hash sent via HTTPS to web regardless
    key = 'stackhut_is_G_dawg'
    encrypt_vals = ['hash']
    basic_vals = ['username', 'docker_username']

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

    def wipe(self):
        """blank out the cfg file"""
        self.clear()

    @property
    def logged_in(self):
        return 'username' in self

    def assert_logged_in(self):
        if not self.logged_in:
            log.error("Please login first - run 'stackhut login'")
            raise AssertionError()

    def assert_user_is_author(self, hutcfg):
        if self.username != hutcfg.author:
            log.error("StackHut username ({}) not equal to service author ({})\n"
                      "Please login as a different user or edit the Hutfile as required"
                      .format(self.username, hutcfg.author))
            raise AssertionError()

    @property
    def username(self):
        self.assert_logged_in()
        return self['username']

    @property
    def docker_username(self):
        self.assert_logged_in()
        log.debug("Using docker username '{}'".format(self['docker_username']))
        return self['docker_username']

class HutfileCfg:
    """Hutfile configuration file handling"""
    def __init__(self):
        # import the hutfile
        with open(HUTFILE, 'r') as f:
            hutfile = yaml.safe_load(f)

        # TODO - validation
        # get vals from the hutfile
        self.name = hutfile['name'].lower()
        self.author = hutfile['author']
        self.version = 'latest'

        # self.email = hutfile['contact']
        self.description = hutfile['description']
        self.github_url = hutfile.get('github_url', None)

        # copy files and dirs separetly
        files = hutfile.get('files', [])
        self.files = [f for f in files if os.path.isfile(f)]
        self.dirs = [d for d in files if os.path.isdir(d)]

        self.os_deps = hutfile.get('os_deps', [])
        self.docker_cmds = hutfile.get('docker_cmds', [])
        self.baseos = hutfile['baseos']
        self.stack = hutfile['stack']

    @property
    def from_image(self):
        return "{}-{}".format(self.baseos, self.stack)

    @property
    def service_fullname(self):
        """Returns the StackHut service name for the image"""
        return "{}/{}:{}".format(self.author, self.name, self.version)

    def docker_fullname(self, usercfg):
        """Returns the DockerHub name for the image"""
        return "{}/{}:{}".format(usercfg.docker_username, self.name, self.version)

    def docker_repo(self, usercfg):
        """Returns the DockerHub repo for the image"""
        return self.docker_fullname(usercfg).split(':')[0]



###################################################################################################
# StackHut Commands Handling
class BaseCmd:
    """The Base Command implementing common func"""
    visible = True
    name = ''

    @staticmethod
    def parse_cmds(subparsers, cmd_name, description, cls):
        if cls.visible:
            sp = subparsers.add_parser(cmd_name, help=description, description=description)
        else:
            sp = subparsers.add_parser(cmd_name)

        sp.set_defaults(func=cls)
        return sp

    def __init__(self, args):
        self.args = args

    @abc.abstractmethod
    def run(self):
        """Main entry point for a command with parsed cmd args"""
        pass

class HutCmd(BaseCmd):
    """Hut Commands are run from a Hut stack dir requiring a Hutfile"""
    def __init__(self, args):
        super().__init__(args)
        # import the hutfile
        self.hutcfg = HutfileCfg()
        # create stackhut dir if not present
        create_stackhut_dir()


###################################################################################################
# StackHut server comms
def secure_url_prefix():
    return "http://{}/".format(DEBUG) if DEBUG is not None else "https://api.stackhut.com/"

def unsecure_url_prefix():
    return "http://{}/".format(DEBUG) if DEBUG is not None else "http://api.stackhut.com/"

headers = {'content-type': 'application/json'}

import urllib.parse
import requests

def stackhut_api_call(endpoint, msg, secure=True):
    url_prefix = secure_url_prefix() if secure else unsecure_url_prefix()
    log.debug(url_prefix)
    url = urllib.parse.urljoin(url_prefix, endpoint)
    log.debug("Calling Stackhut {} with \n\t{}".format(endpoint, json.dumps(msg)))
    r = requests.post(url, data=json.dumps(msg), headers=headers)

    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        log.error("Error {} talking to stackhut server".format(r.status_code))
        log.error(r.text)
        r.raise_for_status()

def stackhut_api_user_call(endpoint, data, usercfg):
    auth = dict(username=usercfg.username, hash=usercfg['hash'])
    message = dict(auth=auth, data=data)
    return stackhut_api_call(endpoint, message)
