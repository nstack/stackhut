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
StackHut IO Handling on local and cloud backends
"""
import abc
import os
import json
import shutil
import threading
from queue import Queue

import sh
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, ImATeapot
from werkzeug.utils import redirect

from ..utils import log
from . import rpc

STACKHUT_DIR = os.path.abspath('.stackhut')

def get_req_dir(req_id):
    return os.path.join(STACKHUT_DIR, req_id)

def get_req_file(req_id, fname):
    return os.path.join(STACKHUT_DIR, req_id, fname)

def http_status_code(data):
    if type(data) == list:
        log.debug("Shit, HTTP status code incorrect")

    if 'error' not in data.get('response', {}):
        return 200

    code = data['response']['error']['code']

    if code == -32600:
        return 400
    elif code == -32601:
        return 404
    else:
        return 500

class AbstractBackend:
    """A base wrapper wrapper around common IO task state"""
    def __init__(self, hutcfg, author):
        self.author = author
        self.service_short_name = hutcfg.service_short_name(self.author)
        os.mkdir(STACKHUT_DIR) if not os.path.exists(STACKHUT_DIR) else None
        self.request = {}
        log.debug("Starting service {}".format(self.service_short_name))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # Interace between backend and runner
    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    # First-stage processing of request/response
    def _process_request(self, data):
        try:
            self.request = json.loads(data.decode('utf-8'))
            rpc.add_get_id(self.request)
            log.info("Request - {}".format(self.request))
            if ((self.request['service'] != self.service_short_name) and ((self.request['service']+':latest') != self.service_short_name)):
                log.warn("Service request ({}) sent to wrong service ({})".format(self.request['service'], self.service_short_name))
        except Exception as e:
            _e = rpc.exc_to_json_error(rpc.ParseError(dict(exception=repr(e))))
            return True, _e
        else:
            return False, self.request

    def _process_response(self, data):
        log.info("Response - {}".format(data))
        self.request = {}
        return json.dumps(data).encode('utf-8')

    def get_file(self, key):
        raise NotImplementedError("IOStore.get_file called")

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    @property
    def task_id(self):
        return self.request.get('id', None)

    def create_request_dir(self, req_id):
        # create a private working dir
        req_path = os.path.join(STACKHUT_DIR, req_id)
        os.mkdir(req_path) if not os.path.exists(req_path) else None
        return req_path

    def del_request_dir(self, req_id):
        req_path = os.path.join(STACKHUT_DIR, req_id)
        shutil.rmtree(req_path, ignore_errors=True)


class LocalRequestServer(threading.Thread):
    def __init__(self, port, backend, req_q, resp_q):
        super().__init__(daemon=True)
        # configure the local server thread
        self.port = port
        self.req_q = req_q
        self.resp_q = resp_q
        self.backend = backend
        # self.got_req = threading.Event()
        self.start()

        # routing
        self.url_map = Map([
            Rule('/run', endpoint='run_request'),
            Rule('/files', endpoint='run_files'),
        ])

    def run(self):
        # start in a new thread
        log.info("Started StackHut Request Server - press Ctrl-C to quit")
        run_simple('0.0.0.0', self.port, self.local_server)

    @Request.application
    def local_server(self, request):
        """
        Local webserver running on separate thread for dev usage
        Sends msgs to LocalBackend over a pair of shared queues
        """
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException as e:
            return e

    def on_run_request(self, request):
        """
        Sends run requests to LocalBackend over a pair of shared queues
        """
        (rpc_error, data) = self.backend._process_request(request.data)
        if rpc_error:
            return self.return_reponse(data)

        task_req = data
        self.req_q.put(task_req)
        response = self.resp_q.get()

        self.req_q.task_done()
        self.resp_q.task_done()

        return self.return_reponse(response)

    def return_reponse(self, data):
        return Response(self.backend._process_response(data),
                        status=http_status_code(data), mimetype='application/json')

    def on_run_files(self, request):
        log.debug("In run_files endpoint")
        raise ImATeapot()



class LocalBackend(AbstractBackend):
    """Mock storage and server system for local testing"""
    local_store = "run_result"

    def _get_path(self, name):
        return "{}/{}".format(self.local_store, name)

    def __init__(self, hutcfg, author, port, uid_gid=None):
        super().__init__(hutcfg, author)
        self.uid_gid = uid_gid

        # delete and recreate local_store
        shutil.rmtree(self.local_store, ignore_errors=True)
        if not os.path.exists(self.local_store):
            os.mkdir(self.local_store)

        # configure the local server thread
        self.req_q = Queue(1)
        self.resp_q = Queue(1)
        self.server = LocalRequestServer(port, self, self.req_q, self.resp_q)

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("Shutting down Local backend")
        # wait for queues to empty
        self.req_q.join()
        self.resp_q.join()

        # change the results owner
        if self.uid_gid is not None:
            sh.chown('-R', self.uid_gid, self.local_store)

    def get_request(self):
        return self.req_q.get()

    def put_response(self, data):
        self.resp_q.put(data)

    def _process_response(self, _data):
        """For local wrap up in a response dict"""
        data = dict(response=_data)
        return super()._process_response(data)

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
