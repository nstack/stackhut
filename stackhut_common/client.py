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
StackHut Client Side library
Initial version w/ only server-side validation
* multiple stages
  * Stage 1 - (current) construct call dyamically via monkey-patching
  * Stage 2 - use server idl file to gen class via monkey-patching/meta-class
  * Stage 3 - Stage 2 + client-side validation
"""
import json
import urllib.parse
import logging as log
import uuid
import requests

__all__ = ['SHRPCError', 'SHAuth', 'SHService']

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


class SHService:
    json_header = {'content-type': 'application/json'}

    def __init__(self, author, name, version='latest', auth=None, host_url='https://api.stackhut.com/run'):
        self.service_short_name = "{}/{}:{}".format(author, name, version)
        self.auth = auth
        self.host_url = host_url

        # call to stackhut and get the json

    def _make_call(self, iface_name, method, params):
        log.info("Making RPC call to {}.{}.{}".format(self.service_short_name, iface_name, method))

        msg = {
            "service": self.service_short_name,
            "request": {
                "method": "{}.{}".format(iface_name, method),
                "params": list(params),
                "id": str(uuid.uuid4()),
                "jsonrpc": "2.0",
            },
            "id": str(uuid.uuid4()),
        }
        if self.auth:
            msg['auth'] = self.auth.msg

        r = requests.post(self.host_url, data=json.dumps(msg), headers=self.json_header)
        if r.status_code == requests.codes.ok:
            r_json = r.json()
            return r_json['result']
        else:
            log.error("HTTP Error {}".format(r.status_code))
            r_json = r.json()
            log.error("RPC Error {}".format(r_json['error']['code']))
            log.error(r_json)
            error_msg = r_json['error']
            raise SHRPCError(error_msg['code'], error_msg['message'], error_msg.get('data', {}))

    def __getattr__(self, iface_name):
        return IFaceCall(self, iface_name)

class IFaceCall:
    def __init__(self, service, iface_name):
        self.service = service
        self.iface_name = iface_name

    def __getattr__(self, name):
        def method(*args):
            return self.service._make_call(self.iface_name, name, args)
        return method



if __name__ == '__main__':
    # Simple test code
    log.basicConfig(level=log.INFO)
    sh_auth = SHAuth('mands', )
    sh_client = SHService('mands', 'test-service', host_url='http://localhost:6000')
    log.info("Result - {}".format(sh_client.Default.add(1, 2)))

    try:
        log.info("Result - {}".format(sh_client.sub(1, 2)))
    except SHRPCError as e:
        log.error("Caught error - {}".format(repr(e)))

