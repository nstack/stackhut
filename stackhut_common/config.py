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
Config files used by the platform
"""
import os
import re
import stat
import uuid
import json
import yaml
from .utils import log

class UserCfg(dict):
    """
    UserConfig configuration handling
    Wrapper class around dict that uses a json backing store
    """
    show_keys = ['username', 'send_analytics']
    keep_keys = ['send_analytics', 'm_id']
    config_version = 1
    config_fpath = os.path.expanduser(os.path.join('~', '.stackhut.cfg'))

    def __init__(self):
        super().__init__()
        if os.path.exists(self.config_fpath):
            with open(self.config_fpath, 'r') as f:
                self.update(json.load(f))
            if self.get('config_version', 0) < self.config_version:
                self.wipe()
                raise AssertionError("Config file version mismatch, please run 'stackhut login' again")
        else:
            # create with correct file permissions
            open(self.config_fpath, 'w').close()
            os.chmod(self.config_fpath, stat.S_IRUSR | stat.S_IWUSR)
            self.wipe()

        self.ask_analytics()

    def ask_analytics(self):
        def agree():
            while True:
                x = input("Agree to send analytics [Y/N]: ").capitalize()
                if x.startswith('Y'):
                    return True
                if x.startswith('N'):
                    return False

        if self.get('send_analytics') is None:
            log.info("Welcome to StackHut - thank you for installing the Toolkit")
            log.info("To help us improve StackHut we'd like to send some usage and error data for analytics")
            log.info("We'd really like it if you could help us with this, however if you'd like to opt out please enter 'N'")
            self['send_analytics'] = agree()
            self['m_id'] = str(uuid.uuid4())
            self.save()
            log.info("Thanks, your choice has been saved.")

    def save(self):
        with open(self.config_fpath, 'w') as f:
            json.dump(self, f)

    def wipe(self):
        """blank out the cfg file"""
        x = {k: self.get(k) for k in self.keep_keys}
        self.clear()
        self.update(x)
        self['config_version'] = self.config_version
        self.save()

    @property
    def logged_in(self):
        return 'username' in self

    def assert_logged_in(self):
        if not self.logged_in:
            raise AssertionError("Please login first - run 'stackhut login'")

    @property
    def username(self):
        self.assert_logged_in()
        return self['username']

    @property
    def send_analytics(self):
        return self['send_analytics']

    @property
    def analytics_ids(self):
        # if ('send_analytics' not in self) or (self.logged_in and 'u_id' not in self):
        #     raise AssertionError("Config file error - please delete {} and try again".format(CFGFILE))
        if self.send_analytics:
            return dict(m_id=self['m_id'], u_id=self.get('u_id'))
        else:
            return None

class HutfileCfg:
    re_check_name = re.compile('^[a-z0-9-_]+$')

    """Hutfile configuration file handling"""
    def __init__(self):
        # import the hutfile
        hutfile_fname = 'Hutfile.yaml' if os.path.exists('Hutfile.yaml') else 'Hutfile'
        with open(hutfile_fname, 'r') as f:
            hutfile = yaml.safe_load(f)

        # TODO - validation
        # get vals from the hutfile
        self.name = hutfile['name']
        self.assert_valid_name(self.name)
        self.version = hutfile.get('version', 'latest')

        # self.email = hutfile['contact']
        self.description = hutfile['description']
        self.github_url = hutfile.get('github_url', None)

        # copy files and dirs separetly
        files = hutfile.get('files', [])
        self.files = [f for f in files if os.path.isfile(f)]
        self.dirs = [d for d in files if os.path.isdir(d)]

        self.persistent = hutfile.get('persistent', True)
        self.private = hutfile.get('private', False)

        self.os_deps = hutfile.get('os_deps', [])
        self.docker_cmds = hutfile.get('docker_cmds', [])
        self.baseos = hutfile['baseos']
        self.stack = hutfile['stack']

    @staticmethod
    def assert_valid_name(name):
        if HutfileCfg.re_check_name.match(name) is None:
            raise AssertionError("'{}' is not a valid service name, must be [a-z0-9-_]".format(name))

    @property
    def from_image(self):
        return "{}-{}".format(self.baseos, self.stack)

    def service_short_name(self, username):
        """Returns the StackHut service name for the image"""
        return "{}/{}:{}".format(username, self.name, self.version)
