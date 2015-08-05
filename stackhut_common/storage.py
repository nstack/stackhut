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
import shutil
import threading
import json
from queue import Queue
import sh
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from stackhut_common.utils import log

STACKHUT_DIR = '.stackhut'

def get_req_dir(req_id):
    return os.path.join(STACKHUT_DIR, req_id)

def get_req_file(req_id, fname):
    return os.path.join(STACKHUT_DIR, req_id, fname)

class IOStore:
    """A base wrapper wrapper around common IO task state"""
    def __init__(self):
        os.mkdir(STACKHUT_DIR) if not os.path.exists(STACKHUT_DIR) else None

    def new_request_path(self, req_id):
        # create a private working dir
        req_path = os.path.join(STACKHUT_DIR, req_id)
        os.mkdir(req_path) if not os.path.exists(req_path) else None
        return req_path

    def cleanup(self):
        pass

    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    def get_file(self, name):
        raise NotImplementedError("IOStore.get_file called")

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    def set_task_id(self, task_id):
        self.task_id = task_id

class LocalServer(threading.Thread):

    def __init__(self, port, req_q, resp_q, *args, **kwargs):
        super().__init__(*args, daemon=True, **kwargs)
        self.port = port
        self.req_q = req_q
        self.resp_q = resp_q

    @Request.application
    def application(self, request):
        self.req_q.put(request.data.decode('utf-8'))
        response = self.resp_q.get()

        self.resp_q.task_done()
        return Response(response.encode('utf-8'), mimetype='application/json')

    def run(self):
        # start in a new thread
        log.info("Starting StackHut local server - press Ctrl-C to quit")
        run_simple('localhost', self.port, self.application)


class LocalStore(IOStore):
    """Mock storage and server system for local testing"""
    local_store = "run_result"

    def _get_path(self, name):
        return "{}/{}".format(self.local_store, name)

    def __init__(self, port=8080, uid_gid=None):
        super().__init__()
        self.uid_gid = uid_gid

        # delete and recreate local_store
        shutil.rmtree(self.local_store, ignore_errors=True)
        if not os.path.exists(self.local_store):
            os.mkdir(self.local_store)

        self.req_q = Queue(1)
        self.resp_q = Queue(1)
        self.got_req = threading.Event()
        self.server = LocalServer(port, self.req_q, self.resp_q)
        self.server.start()

    def cleanup(self):
        log.debug("Cleaning up store")
        # wait for queues to empty
        self.req_q.join()
        self.resp_q.join()

        # change the results owner
        if self.uid_gid is not None:
            sh.chown('-R', self.uid_gid, self.local_store)

    def get_request(self):
        return self.req_q.get()

    def put_response(self, s):
        self.req_q.task_done()
        self.resp_q.put(s)

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
