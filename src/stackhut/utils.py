import subprocess
import logging
from boto.s3.connection import Key
import requests
import barrister
import yaml
import sys

# global constants
LOGFILE = 'service.log'
HUTFILE = 'Hutfile'
CONTRACTFILE = 'service.json'

log = logging.getLogger('stackhut')
# consoleHandler = logging.StreamHandler()
# #consoleHandler.setFormatter(logFormatter)
# log.addHandler(consoleHandler)

def setup_logging(args_level):
    # setup the logger
    loglevel = logging.WARN
    if args_level == 1:
        loglevel = logging.INFO
    elif args_level >= 2:
        loglevel = logging.DEBUG
    log.setLevel(loglevel)

    logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s', '%H:%M:%S')
    # file output
    fileHandler = logging.FileHandler(LOGFILE, mode='w')
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)
    # console
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)



class BaseCmd:
    """The Base Command"""
    cmd_name = ''

    def __init__(self):
        pass

    def parse_cmds(self, subparsers, description):
        sp = subparsers.add_parser(self.cmd_name, help=description, description=description)
        sp.set_defaults(func=self.run)
        return sp

    def run(self, args):
        """Main entry point for a command with parsed cmd args"""
        # import the hutfile
        self.hutfile = yaml.load(args.hutfile)

        return 0



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



## S3 helper functions
# File upload / download helpers
def download_file(url):
    """from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py"""
    local_filename = url.split('/')[-1]
    logging.info("Downloading file {} from {}".format(local_filename, url))
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

def upload_file(filename, task_id, bucket):
    # NOTE - very hacky, move into a s3 upload/download class that can be mocked with local
    if LOCAL:
        res = filename
    else:
        logging.info("Uploading output file {}".format(filename))
        # upload output.json to S3
        k = Key(bucket)
        k.key = "{}/{}".format(task_id, filename)
        k.set_contents_from_filename(filename)
        k.set_acl('public-read')
        k.make_public()
        res = k.generate_url(expires_in=0, query_auth=False)

    return res

# Subprocess helper functions
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

def call_files(cmd, stdin, stdout, stderr):
    ret_val = subprocess.call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    return ret_val

