import sys
import os
import subprocess
import logging
import argparse
import json
from boto.s3.connection import S3Connection, Location, Key
import requests
import barrister
import uuid
import yaml


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

# Subprocess helper functionsdef call_strings(cmd, stdin):
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

