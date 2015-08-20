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
Initial stab at a dynamic client-side lib
- only server-side validation
"""
import json
import requests
import urllib.parse
from stackhut_common.utils import log, SERVER_URL

class SHRPCError(Exception):
    def __init__(self, code, msg, data=None):
        self.code = code
        self.msg = msg
        self.data = data if data else {}


class SHAuth:
    def __init__(self, user, hash=None, token=None):
        if hash is None and token is None:
            raise ValueError("Must provide either password or api token to auth")
        self.user = user
        self.hash = hash
        self.token = token

    @property
    def msg(self):
        if self.hash:
            return dict(user=self.user, hash=self.hash)
        else:
            return dict(user=self.user, token=self.token)


# TODO - make a metaclass?
# multiple stages
# Stage 1 - construct call dyamically via monkey-patching
# Stage 2 - use server idl file to gen class via monkey-patching/meta-class
# Stage 3 - Stage 2 + client-side validation
class SHService:
    json_header = {'content-type': 'application/json'}
    url = urllib.parse.urljoin(SERVER_URL, 'run')

    def __init__(self, author, name, version='latest', auth=None):
        self.service_fullname = "{}/{}:{}".format(author, name, version)
        self.auth = auth
        # call to stackhut and get the json

    def _make_call(self, method, params):
        log.debug("Making RPC call to {}.Default.{}".format(self.service_fullname, method))

        msg = {
            "service": self.service_fullname,
            "method": "Default.{}".format(method),
            "params": params
        }
        if self.auth:
            msg['auth'] = self.auth.msg

        r = requests.post(self.url, data=json.dumps(msg), headers=self.json_header)
        r_json = r.json()
        if r.status_code == requests.codes.ok:
            return r_json['result']
        else:
            log.error("RPC Error {}, HTTP Error".format(r_json['error']['code'], r.status_code))
            log.error(r_json)
            raise SHRPCError(r_json['code'], r_json['message'], r_json.get('data', {}))

    def __getattr__(self, name):
        def method(*args):
            return self._make_call(name, args)

        return method

