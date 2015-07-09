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
from __future__ import (unicode_literals, print_function, division, absolute_import)
from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
import requests
import json

url = "http://localhost:4000/jsonrpc"
headers = {'content-type': 'application/json'}
id_val = 0

def make_call(method, *params):
    global id_val
    # Example echo method
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": id_val,
    }

    response = requests.post(
        url, data=json.dumps(payload), headers=headers).json()

    id_val += 1
    return response["result"]

def put_file(fname, make_public=True):
    return make_call('put_file', fname, make_public)

def download_file(url, fname=None):
    return make_call('download_file', url, fname)

def run_command(cmd, stdin=''):
    return make_call('run_command', cmd)
