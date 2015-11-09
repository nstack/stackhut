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
import threading
import sys
import os
import json
import itertools
import time
from queue import Queue
import urllib.parse
import requests
from .common.utils import log
from .common import utils


# names to export
__all__ = ['stackhut_api_call', 'stackhut_api_user_call', 'keen_client', 'get_res_path', 'Spinner']

# Setup app paths - this is unique for each stackhut package
sys_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
res_dir = os.path.normpath(os.path.join(sys_dir, './res'))

def get_res_path(res_name):
    return os.path.join(res_dir, res_name)

###################################################################################################
# StackHut server comms
json_header = {'content-type': 'application/json'}


def stackhut_api_call(endpoint, msg, secure=True, return_json=True):
    url = urllib.parse.urljoin(utils.SERVER_URL, endpoint)
    log.debug("Calling Stackhut Server at {} with \n\t{}".format(url, json.dumps(msg)))
    r = requests.post(url, data=json.dumps(msg), headers=json_header)

    if r.status_code == requests.codes.ok:
        return r.json() if return_json else r.text
    else:
        log.error("Error {} talking to Stackhut Server".format(r.status_code))
        log.error(r.text)
        r.raise_for_status()

def stackhut_api_user_call(endpoint, _msg, usercfg):
    msg = _msg.copy()
    msg['auth'] = dict(username=usercfg.username, hash=usercfg['hash'])
    return stackhut_api_call(endpoint, msg)



###################################################################################################
# Keen analytlics
class KeenClient(threading.Thread):
    project_id = '559f866f96773d25d47419f6'
    write_key = 'abd65ad8684753678eabab1f1c536b36a70704e6c4f10bcfe928c10ec859edb1d0366f3fad9b7794b0' \
                'eeab9825a27346e0186e2e062f76079708b66ddfca7ecc82b8db23062f8cd2e4f6a961d8d2ea23b22f' \
                'c9aae1387514da6d46cdbebec2d15c9167d401963ee8f96b00e06acf4e48'
    keen_url = "https://api.keen.io/3.0/projects/{project_id}/events/{{event_collection}}?" \
               "api_key={write_key}".format(project_id=project_id, write_key=write_key)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.send_analytics = False
        self.analytics_ids = None
        self.queue = Queue()

    def start(self, usercfg):
        self.send_analytics = usercfg.send_analytics
        if self.send_analytics:
            log.debug("User analytics enabled")
            self.analytics_ids = usercfg.analytics_ids
            super().start()
        else:
            log.debug("User analytics disabled")

    def run(self):
        while True:
            (endpoint, msg) = self.queue.get()
            msg.update(self.analytics_ids)
            try:
                log.debug("Sending analytics msg to {}".format(endpoint))
                # log.debug("Analytics msg - {}".format(msg))
                url = self.keen_url.format(event_collection=endpoint)
                r = requests.post(url, data=json.dumps(msg), headers=json_header, timeout=2)
                if not (r.status_code == requests.codes.created and r.json().get('created')):
                    log.debug("{} - {}".format(r.status_code, r.text()))
                    raise IOError()
            except:
                log.debug("Failed sending analytics msg to '{}'".format(endpoint))
            finally:
                self.queue.task_done()

    def send(self, endpoint, msg):
        if self.send_analytics:
            self.queue.put((endpoint, msg))

    def shutdown(self):
        if self.send_analytics:
            self.queue.join()

keen_client = KeenClient(daemon=True)


class Spinner(threading.Thread):
    """A simple console spinner to use with long-running tasks"""

    spin_interval = 0.5
    dot_interval = 10
    dot_max = int(dot_interval / spin_interval)

    def __init__(self):
        super().__init__(daemon=True)
        self.spinning = threading.Event()
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])

    def __enter__(self):
        self.spinning.set()
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.spinning.clear()

    def run(self):
        dot_count = 0

        while self.spinning.is_set():
            sys.stdout.write(next(self.spinner))  # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
            time.sleep(self.spin_interval)
            dot_count += 1
            if dot_count >= self.dot_max:
                sys.stdout.write('.')  # write the next character
                dot_count = 0

        sys.stdout.write('\n')

    def stop(self):
        self.spinning.clear()
