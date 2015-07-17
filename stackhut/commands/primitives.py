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
import os
import time
import json
from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch
import sh
from distutils.dir_util import copy_tree

from stackhut import utils
from stackhut.utils import log
from stackhut.barrister import generate_contract

template_env = Environment(loader=FileSystemLoader(utils.get_res_path('templates')))

class DockerEnv:
    def __init__(self):
        self.push = None
        self.no_cache = None

    def build(self, push, no_cache):
        self.push = push
        self.no_cache = no_cache

    def gen_dockerfile(self, template_name, template_params, dockerfile='Dockerfile'):
        rendered_template = template_env.get_template(template_name).render(template_params)
        with open(dockerfile, 'w') as f:
            f.write(rendered_template)

    def build_dockerfile(self, tag, dockerfile='Dockerfile'):
        log.debug("Running docker build for {}".format(tag))
        cache_flag = '--no-cache=True' if self.no_cache else '--no-cache=False'
        cmds = ['build', '-f', dockerfile, '-t', tag, '--rm', cache_flag, '.']
        log.debug("Calling docker with cmds - {}".format(cmds))
        log.info("Starting build, this may take some time, please wait...")
        sh.docker(*cmds)
        if self.push:
            log.info("Uploading image {}".format(tag))
            sh.docker('push', tag, _in='Y')
        return tag

    def stack_build(self, template_name, template_params, outdir, image_name):
        image_dir = os.path.join(outdir, image_name)
        if not os.path.exists(image_dir):
            os.mkdir(image_dir)
        os.chdir(image_dir)
        self.gen_dockerfile(template_name, template_params)

        tag = "{}/{}:{}".format('stackhut', image_name, 'latest')
        self.build_dockerfile(tag)
        os.chdir(utils.ROOT_DIR)




# Base OS's that we support
class BaseOS(DockerEnv):
    name = None

    def __init__(self):
        super().__init__()

    @property
    def description(self):
        return "Base OS image using {}".format(self.name.capitalize())

    def build(self, outdir, *args):
        super().build(*args)
        log.info("Building image for base {}".format(self.name))
        image_name = self.name
        super().stack_build('Dockerfile-baseos.txt', dict(baseos=self), outdir, image_name)


class Fedora(BaseOS):
    name = 'fedora'

    baseos_pkgs = ['python3', 'python3-pip']

    def os_pkg_cmd(self, pkgs):
        return 'dnf -y install {}'.format(' '.join(pkgs))

    def install_os_pkg(self, pkgs):
        return [
            self.os_pkg_cmd(pkgs),
            'dnf -y autoremove',
            'dnf -y clean all',
            'rm -rf /usr/share/locale/*',
            'rm -rf /usr/share/doc/*',
            'journalctl --vacuum-size=0',
            'rm -rf /var/log/* || true',
            'rm -rf /var/cache/*',
            'rm -rf /tmp/*',
        ]

    def setup_cmds(self):
        return self.install_os_pkg(self.baseos_pkgs)


class Alpine(BaseOS):
    name = 'alpine'

    baseos_pkgs = ['python3', 'ca-certificates']

    def os_pkg_cmd(self, pkgs):
        return 'apk --update add {}'.format(' '.join(pkgs))

    def install_os_pkg(self, pkgs):
        return [
            self.os_pkg_cmd(pkgs),
            'rm -rf /usr/share/locale/*',
            'rm -rf /usr/share/doc/*',
            'rm -rf /var/log/* || true',
            'rm -rf /var/cache/*',
            'rm -rf /tmp/*',
            'mkdir /var/cache/apk',
        ]

    def setup_cmds(self):
        return [
            'echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories',
            'echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories',
        ] + self.install_os_pkg(self.baseos_pkgs)


# Language stacks that we support
class Stack(DockerEnv):
    name = None
    entrypoint = None
    stack_pkgs = None
    package_file = None
    shim_files = None
    shim_cmd = None
    scaffold_name = None

    def __init__(self):
        super().__init__()

    @property
    def description(self):
        return "Support for language stack {}".format(self.name.capitalize())

    def build(self, baseos, outdir, *args):
        super().build(*args)
        log.info("Building image for base {} with stack {}".format(baseos.name, self.name))
        image_name = "{}-{}".format(baseos.name, self.name)
        baseos_stack_cmds_pkgs = get_baseos_stack_pkgs(baseos, self)
        if baseos_stack_cmds_pkgs is not None:
            os_cmds, pkgs = baseos_stack_cmds_pkgs
            pkg_cmds = baseos.install_os_pkg(pkgs) if pkgs else []
            stack_cmds = os_cmds + pkg_cmds

            # only render the template if apy supported config
            super().stack_build('Dockerfile-stack.txt',
                                dict(baseos=baseos, stack=self, stack_cmds=stack_cmds),
                                outdir, image_name)

    def install_service_pkgs(self):
        """Anything needed to run the service"""
        return ''

    def install_stack_pkgs(self):
        """Anything needed to run the stack"""
        return ''

    @property
    def install_service_file(self):
        return self.package_file if os.path.exists(self.package_file) else ''

    def copy_shim(self):
        shim_dir = os.path.join(utils.get_res_path('shims'), self.name)
        copy_tree(shim_dir, utils.ROOT_DIR)

    def del_shim(self):
        for f in self.shim_files:
            os.remove(os.path.join(utils.ROOT_DIR, f))


class Python(Stack):
    name = 'python'
    entrypoint = 'app.py'
    stack_pkgs = ['requests', 'sh']
    package_file = 'requirements.txt'

    shim_files = ['runner.py', 'stackhut.py']
    shim_cmd = ['/usr/bin/env', 'python3', 'runner.py']

    scaffold_name = 'scaffold-python.py'

    def install_stack_pkgs(self):
        return 'pip3 install --no-cache-dir --compile {}'.format(str.join(' ', self.stack_pkgs))

    def install_service_pkgs(self):
        return 'pip3 install --no-cache-dir --compile -r {}'.format(self.package_file)

class Python2(Stack):
    name = 'python2'
    entrypoint = 'app.py'
    stack_pkgs = ['requests', 'sh']
    package_file = 'requirements.txt'

    shim_files = ['runner.py', 'stackhut.py']
    shim_cmd = ['/usr/bin/env', 'python2', 'runner.py']

    scaffold_name = 'scaffold-python2.py'

    def install_stack_pkgs(self):
        return 'pip2 install --no-cache-dir --compile {}'.format(str.join(' ', self.stack_pkgs))

    def install_service_pkgs(self):
        return 'pip2 install --no-cache-dir --compile -r {}'.format(self.package_file)

class NodeJS(Stack):
    name = 'nodejs'
    entrypoint = 'app.js'
    stack_pkgs = ['sync-request']
    package_file = 'package.json'

    shim_files = ['runner.js', 'stackhut.js']
    shim_cmd = ['/usr/bin/env', 'iojs', '--harmony', 'runner.js']

    scaffold_name = 'scaffold-nodejs.js'

    def install_stack_pkgs(self):
        return 'npm install {}'.format(str.join(' ', self.stack_pkgs))

    def install_service_pkgs(self):
        return 'npm install; exit 0'

# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    """return the docker cmds and any os packages needed to be installed"""
    return [], ['python', 'python-pip']

@dispatch(Alpine, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    return [], ['python', 'py-pip']

@dispatch(Fedora, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return [], []  # installed by default

@dispatch(Alpine, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return [], []  # installed by default

@dispatch(Fedora, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    cmds = ['dnf -y install dnf-plugins-core',
            'dnf -y copr enable nibbler/iojs',
            ]
    pkgs = ['iojs', 'iojs-npm']
    return cmds, pkgs

@dispatch(Alpine, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    return [], ['iojs@testing', 'libstdc++@edge']

@dispatch(object, object)
def get_baseos_stack_pkgs(base_os, stack):
    log.debug("Os / Stack combo for {}/{} not implemented".format(base_os.name, stack.name))
    return None
    # raise NotImplementedError()

bases = dict([(b.name, b) for b in [Alpine(), Fedora()]])
stacks = dict([(s.name, s) for s in [Python(), NodeJS(), Python2()]])

def is_stack_supported(base, stack):
    """Return true if the baseos & stack combination is supported"""
    if get_baseos_stack_pkgs(base, stack) is not None:
        return True
    else:
        return False

class Service(DockerEnv):
    """Main primitive representing a StackHut service"""
    def __init__(self, hutcfg, usercfg):
        super().__init__()

        self.hutcfg = hutcfg
        self.usercfg = usercfg
        self.baseos = bases[hutcfg.baseos]
        self.stack = stacks[hutcfg.stack]
        self.from_image = "{}-{}".format(self.baseos.name, self.stack.name)

    @property
    def build_date(self):
        return int(time.time())

    def build(self, *args):
        super().build(*args)
        dockerfile = os.path.join(utils.STACKHUT_DIR, 'Dockerfile')
        self.gen_dockerfile('Dockerfile-service.txt', dict(service=self), dockerfile)
        tag = self.hutcfg.tag(self.usercfg)
        self.build_dockerfile(tag, dockerfile)


# Helper functions
# TODO - we should move these into a dep-style system - maybe use Makefiled in interrim
def gen_barrister_contract():
    generate_contract('api.idl', utils.CONTRACTFILE)
