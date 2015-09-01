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
"""
StackHut Runtime library, accessible over JSON-RPC
"""
import threading

import requests
import sh
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher

from ..utils import log
from . import rpc, backends

backend = None

class RuntimeServer(threading.Thread):
    def __init__(self, _backend):
        super().__init__(daemon=True)
        global backend
        backend = _backend

    @Request.application
    def application(self, request):
        log.debug("Got helper request - {}".format(request.data))
        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype='application/json')

    def run(self):
        # start in a new thread
        log.debug("Starting StackHut helper-server")
        run_simple('localhost', 4000, self.application, threaded=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

###############################################################################
# Runtime Functions

@dispatcher.add_method
def get_stackhut_user(req_id):
    auth = backend.request.get('auth', None)
    return auth['username'] if auth else ''

@dispatcher.add_method
def get_service_author(req_id):
    return backend.author

@dispatcher.add_method
def is_author(req_id):
    return (get_stackhut_user(req_id) == get_service_author(req_id))

@dispatcher.add_method
def put_file(req_id, fname, make_public=True):
    return backend.put_file(fname, req_id, make_public)

@dispatcher.add_method
def get_file(req_id, key):
     return backend.get_file(key)

# File upload / download helpers
@dispatcher.add_method
def download_file(req_id, url, fname=None):
    """from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py"""
    fname = url.split('/')[-1] if fname is None else fname
    req_fname = backends.get_req_file(req_id, fname)
    log.info("Downloading file {} from {}".format(fname, url))
    r = requests.get(url, stream=True)
    with open(req_fname, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return fname

@dispatcher.add_method
def run_command(req_id, cmd, stdin=''):
    try:
        cmd_run = sh.Command(cmd)
        output = cmd_run(_in=stdin)
    except sh.ErrorReturnCode as e:
        raise rpc.NonZeroExitError(e.exit_code, e.stderr)
    return output
