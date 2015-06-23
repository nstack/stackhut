import subprocess
import logging
from boto.s3.connection import Key, S3Connection
import requests
import barrister
import yaml
import sys
import abc
import uuid
import os
import shutil
import redis


# global constants
LOGFILE = 'service.log'
HUTFILE = 'Hutfile'
CONTRACTFILE = 'service.json'
S3_BUCKET = 'stackhut-payloads'

# Logging
def setup_logging():
    log = logging.getLogger('stackhut')
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


# Base command implementing common func
class BaseCmd:
    """The Base Command"""
    @staticmethod
    def parse_cmds(subparsers, cmd_name, description, cls):
        sp = subparsers.add_parser(cmd_name, help=description, description=description)
        sp.set_defaults(func=cls)
        return sp

    def __init__(self, args):
        self.args = args

        # import the hutfile
        self.hutfile = yaml.load(args.hutfile)

        self.src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
        self.shim_dir = os.path.normpath(os.path.join(self.src_dir, '../res/shims'))
        log.debug("StackHut src dir is {}".format(self.src_dir))
        log.debug("StackHut shims dir is {}".format(self.shim_dir))

    @abc.abstractmethod
    def run(self):
        """Main entry point for a command with parsed cmd args"""
        pass


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
    def put_file(self, fname):
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
        self.redis = redis.StrictRedis(host=redis_url, port=6379, db=0, password=None,
                                       socket_timeout=None, connection_pool=None, charset='utf-8',
                                       errors='strict', unix_socket_path=None)

    def get_request(self):
        """Get the request JSON"""
        log.debug("Waiting for task")
        return self.redis.blpop(self.service_name, 0)[1].decode('utf-8').

    def put_response(self, s):
        """Save the resposnce JSON"""
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

    def put_file(self, fname, make_public=False):
        """Upload file to S3"""
        k = self._create_key(fname)
        k.set_contents_from_filename(fname)
        log.info("Uploaded {} to S3".format(fname))

        res = k
        if make_public:
            k.set_acl('public-read')
            k.make_public()
            res = k.generate_url(expires_in=0, query_auth=False)
        return res

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

    def put_file(self, fname, make_public=False):
        shutil.copy(fname, self.local_store)
        return os.path.join(self.local_store, fname)


## S3 helper functions
# File upload / download helpers
def download_file(url, fname=None):
    """from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py"""
    fname = url.split('/')[-1] if fname is None else fname
    logging.info("Downloading file {} from {}".format(fname, url))
    r = requests.get(url, stream=True)
    with open(fname, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return fname


class Subprocess:
    """Subprocess helper functions"""
    @staticmethod
    def call_strings(cmd, stdin):
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr= p.communicate(input=stdin.encode())
            exitcode = p.returncode
        except OSError as e:
            raise ServerError(-32002, 'OS error', dict(error=e.strerror))

        if exitcode is not 0:
            raise NonZeroExitError(exitcode, stderr.decode())
        else:
            return dict(stdout=stdout.decode())

    @staticmethod
    def call_files(cmd, stdin, stdout, stderr):
        ret_val = subprocess.call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
        return ret_val
