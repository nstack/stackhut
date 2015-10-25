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
import signal
import threading

from . import rpc
from .runtime_server import RuntimeServer
from ..utils import log

shim_cmds = {
    'python': ['/usr/bin/env', 'python3', 'runner.py'],
    'python2': ['/usr/bin/env', 'python2', 'runner.py'],
    'nodejs': ['/usr/bin/env', 'node', '--es_staging', 'runner.js']
}

def sigterm_handler(signo, frame):
    log.debug("Got shutdown signal".format(signo))
    raise KeyboardInterrupt

class ServiceRunner:
    """Runs a service"""
    def __init__(self, backend, hutcfg):
        log.debug('Starting Service Runner')
        self.backend = backend
        self.hutcfg = hutcfg
        # select the stack
        self.shim_cmd = shim_cmds.get(self.hutcfg.stack)
        if self.shim_cmd is None:
            raise RuntimeError("Unknown stack - {}".format(self.hutcfg.stack))

        # init the local runtime service
        self.runtime_server = RuntimeServer(backend)
        # init the rpc server
        self.rpc = rpc.StackHutRPC(self.backend, self.shim_cmd)

        assert threading.current_thread() == threading.main_thread()
        signal.signal(signal.SIGTERM, sigterm_handler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """clean the system, write all output data and exit"""
        log.debug('Shutting down service runner')

    def run(self):
        # error_count = 0

        # setup the run contexts
        with self.backend, self.runtime_server, self.rpc:
            while True:
                try:
                    # get the request
                    task_req = self.backend.get_request()
                    # make the internal rpc call
                    task_resp = self.rpc.call(task_req)
                    # send the response out to the storage backend
                    self.backend.put_response(task_resp)
                except KeyboardInterrupt:
                    break

                if not self.hutcfg.persistent:
                    break

