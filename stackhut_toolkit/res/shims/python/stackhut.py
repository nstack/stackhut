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
import requests
import json
import os

url = "http://localhost:4000/jsonrpc"
headers = {'content-type': 'application/json'}

id_val = 0
req_id = None

class Service:
    def __init__(self):
        pass

    def shutdown(self):
        pass

    def preBatch(self):
        pass

    def postBatch(self):
        pass

    def preRequest(self):
        pass

    def postRequest(self):
        pass

class ServiceError(Exception):
    def __init__(self, msg, data=None):
        self.msg = msg
        self.data = data


###############################################################################
# Runtime Lib
def make_call(method, *_params):
    global id_val
    global req_id

    params = list(_params)
    params.insert(0, req_id)

    payload = {
        'method': method,
        'params': params,
        'jsonrpc': '2.0',
        'id': id_val,
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers).json()

    id_val += 1

    if 'result' in response:
        return response['result']
    else:
        raise RuntimeError(response['error'])

# stackhut fields
root_dir = os.getcwd()
in_container = True if os.path.exists('/workdir') else False

# stackhut library functions
def get_stackhut_user():
    return make_call('get_stackhut_user')

def get_service_author():
    return make_call('get_service_author')

def is_author():
    return make_call('is_author')

def put_file(fname, make_public=True):
    return make_call('put_file', fname, make_public)

def get_file(key):
    return make_call('get_file', key)

def download_file(url, fname=None):
    return make_call('download_file', url, fname)

def run_command(cmd, stdin=''):
    return make_call('run_command', cmd)
