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
"""Main interface into client stackhut code"""
import threading
import os
import requests
import sh
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher
from stackhut.common import utils
from stackhut.common.utils import ServerError, NonZeroExitError, log

store = None

@dispatcher.add_method
def put_file(req_id, fname, make_public=True):
    return store.put_file(fname, req_id, make_public)

# File upload / download helpers
@dispatcher.add_method
def download_file(req_id, url, fname=None):
    """from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py"""

    fname = url.split('/')[-1] if fname is None else fname
    req_fname = utils.get_req_file(req_id, fname)
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
        output = sh.Command(cmd, _in=stdin)
    except sh.ErrorReturnCode as e:
        raise NonZeroExitError(output.exit_code, e.stderr)
    return output

@Request.application
def application(request):
    log.debug("Got helper request - {}".format(request.data))
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')

def init(_store, daemon=True):
    global store
    store = _store

    def run_server():
         # start in a new thread
         log.debug("Starting StackHut helper-server")
         run_simple('localhost', 4000, application, threaded=True)

    # start server in sep thread
    t = threading.Thread(target=run_server, daemon=daemon)
    t.start()
    return t

def shutdown():
    pass
