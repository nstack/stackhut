#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StackHut service support
"""
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

# TODO - add more service handling here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes

LOG_NAME = 'service.log'
LOCAL = False  # do we debug locally

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
        data = {
            'exitcode': exitcode,
            'stderr': stderr
        }
        super(NonZeroExitError, self).__init__(code, msg, data)

# File upload / download helpers
def download_file(url):
    """from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py"""
    local_filename = url.split('/')[-1]
    logging.info("Downloading file {} from {}".format(local_filename, url))
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
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

# Subprocess helpers
def call_strings(cmd, stdin):
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr= p.communicate(input=stdin.encode())
        exitcode = p.returncode
    except OSError as e:
        raise ServerError(-32002, 'OS error', {
            'error': e.strerror
        })

    if exitcode is not 0:
        raise NonZeroExitError(exitcode, stderr.decode())
    else:
        return {
            'stdout': stdout.decode()
        }

def call_files(cmd, stdin, stdout, stderr):
    ret_val = subprocess.call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    return ret_val


class Stack:
    def __init__(self):
        # setup the logger
        logging.basicConfig(filename=LOG_NAME, level=logging.INFO)

        # setup the service contracts
        self.contract = barrister.contract_from_file('./service.json')
        self.server = barrister.Server(self.contract)

        # instance vars
        self.aws_id = None
        self.aws_key = None
        self.task_id = None
        self.conn = None
        self.bucket = None


    # called by service on startup
    #
    def _startup(self):
        logging.debug('Starting up service')
        # parse cmd-args
        # aws_key[s], s3bucket id, --?
        # get AWS keys - hmm, how do we do this securly?
        # need temp keys
        parser = argparse.ArgumentParser()
        parser.add_argument("task_id", help="Id representing the specific task", type=str)
        parser.add_argument("aws_id", help="Key used to communicate with AWS", type=str)
        parser.add_argument("aws_key", help="Key used to communicate with AWS", type=str)
        parser.add_argument("--local", help="Run system locally", action="store_true")
        args = parser.parse_args()
        self.aws_id = args.aws_id
        self.aws_key = args.aws_key
        self.task_id = args.task_id
        global LOCAL
        LOCAL = args.local

        # setup AWS
        self.conn = S3Connection(self.aws_id, self.aws_key)
        self.bucket = self.conn.get_bucket('stackhut-payloads')

        if LOCAL:
            with open("./input.json", "r") as f:
                input_json_str = f.read()
        else:
            # download input.json from S3
            k = Key(self.bucket)
            k.key = '{}/input.json'.format(self.task_id)
            input_json_str = k.get_contents_as_string(encoding='UTF-8')
            logging.info("Downloaded input.json from S3")

        # now parse the json
        try:
            input_json = json.loads(input_json_str)
        except:
            raise ParseError()
        logging.info('Input - \n{}'.format(input_json))

        # using json, download any referenced files from s3 bucket? (or are they already there and we download bucket?)
        in_filepaths = []

        # format the JSON-RPC request
        # NOTE - this may be entirely valid JSON-RPC - if so add the correct tags as needed
        def _make_json_rpc(req):
            if 'jsonrpc' not in req:
                req['jsonrpc'] = "2.0"
            if 'id' not in req:
                req['id'] = str(uuid.uuid4())
            return req

        if 'req' in input_json:
            reqs = input_json['req']
            if type(reqs) is list:
                reqs = [_make_json_rpc(req) for req in reqs]
            else:
                reqs = _make_json_rpc(reqs)
        else:
            raise ParseError()

        return reqs, in_filepaths  # anything else

    # called by service on exit - clean the system, write all output data and return control back to docker
    # intended to upload all files into S#
    def _shutdown(self, res):
        logging.info('Shutting down service')

        output_json = json.dumps(res)
        logging.info('Output - \n{}'.format(output_json))

        if LOCAL:
            with open("./output.json", "w") as f:
                f.write(output_json)
        else:
            # upload output.json to S3
            k = Key(self.bucket)
            k.key = '{}/output.json'.format(self.task_id)
            k.set_contents_from_string(output_json)
            logging.info("Uploaded output.json to S3")

            # upload output files to S3

            # send completion message to SQS ?

            # upload log to S3
            k.key = '{}/{}'.format(self.task_id, LOG_NAME)
            k.set_contents_from_filename(LOG_NAME)

    def add_handler(self, iname, impl):
        """Add a service handler to the system"""
        self.server.add_handler(iname, impl)

    def run(self):
        """Run the main rpc commands"""
        try:
            req, in_files = self._startup()
            resp = self.server.call(req)
            self._shutdown(resp)
        except Exception as e:
            logging.exception("Shit, unhandled error! - {}".format(e))
            exit(1)

        # quit with correct exit code
        logging.info('Service call complete')
        exit(0)


def _aws_test():
    """Internal test functions for aws connection"""
    id =''
    key2 = ''

    conn = S3Connection(id, key2)

    allBuckets = conn.get_all_buckets()
    for bucket in allBuckets:
        print(str(bucket.name))

    bucket = conn.get_bucket('stackhut-payloads')
    # Location.EU
    # 'eu-west-1'
    data = open('./input.json', 'r')
    k = Key(bucket)
    k.key = 'input.json'
    k.set_contents_from_filename('./input.json')

    x = k.get_contents_as_string()
    print(x)

if __name__ == "__main__":
    """Manual execution"""
    # aws_test()
