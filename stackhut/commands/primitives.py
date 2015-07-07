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
from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch
import sh

from stackhut import utils
from stackhut.utils import log

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

    def build_dockerfile(self, image_name, author='stackhut', version='latest', dockerfile='Dockerfile'):
        tag = "{}/{}:{}".format(author, image_name, version)
        log.debug("Running docker build for {}".format(tag))
        cache_flag = '--no-cache=True' if self.no_cache else '--no-cache=False'
        cmds = ['build', '-f', dockerfile, '-t', tag, '--rm', cache_flag, '.']
        log.debug("Calling Docker with cmds - {}".format(cmds))
        sh.docker(*cmds)
        if self.push:
            log.info("Pushing {} to Docker Hub".format(tag))
            sh.docker('push', '-f', tag)

    def stack_build(self, template_name, template_params, outdir, image_name):
        image_dir = os.path.join(outdir, image_name)
        if not os.path.exists(image_dir):
            os.mkdir(image_dir)
        os.chdir(image_dir)
        self.gen_dockerfile(template_name, template_params)
        self.build_dockerfile(image_name)
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

    def __init__(self):
        super().__init__()

    @property
    def description(self):
        return "Support for language stack {}".format(self.name.capitalize())

    def build(self, baseos, outdir, *args):
        super().build(*args)
        log.info("Building image for base {} with stack {}".format(baseos.name, self.name))
        image_name = "{}-{}".format(baseos.name, self.name)
        baseos_stack_pkgs = get_baseos_stack_pkgs(baseos, self)
        if baseos_stack_pkgs is not None:
            baseos_stack_cmds = baseos.install_os_pkg(baseos_stack_pkgs)
            # only render the template if apy supported config
            super().stack_build('Dockerfile-stack.txt',
                                dict(baseos=baseos, stack=self, baseos_stack_pkgs=baseos_stack_pkgs),
                                outdir, image_name)

    def install_stack_pkgs(self):
        return ''

class Python2(Stack):
    name = 'python2'
    entrypoint = 'app.py'
    package_file = 'requirements.txt'

    @property
    def get_install_stack_file(self):
        return self.package_file if os.path.exists(self.package_file) else ''

    def install_stack_pkgs(self):
        return 'pip2 install --no-cache-dir --compile -r requirements.txt'

class Python(Stack):
    name = 'python'
    entrypoint = 'app.py'
    package_file = 'requirements.txt'

    @property
    def get_install_stack_file(self):
        return self.package_file if os.path.exists(self.package_file) else ''

    def install_stack_pkgs(self):
        return 'pip3 install --no-cache-dir --compile -r requirements.txt'

class NodeJS(Stack):
    name = 'nodejs'
    entrypoint = 'app.js'


# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    return ['python', 'python-pip']

@dispatch(Alpine, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    return ['python', 'py-pip']

@dispatch(Fedora, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return []  # installed by default

@dispatch(Alpine, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return []  # installed by default

# @dispatch(Fedora, NodeJS)
# def get_baseos_stack_pkgs(base_os, stack):
#     return None  # not supported

@dispatch(Alpine, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    return ['iojs@testing', 'libstdc++@edge']

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
    def __init__(self, hutfile):
        super().__init__()

        # get vals from the hutfile
        self.name = hutfile['name'].lower()
        self.author = hutfile['author'].lower()
        self.email = hutfile['contact']
        self.version = 'latest'
        self.description = hutfile['description']

        # copy files and dirs separetly
        files = hutfile.get('files', [])
        self.files = [f for f in files if os.path.isfile(f)]
        self.dirs = [d for d in files if os.path.isdir(d)]

        self.os_deps = hutfile.get('os_deps', [])
        self.docker_cmds = hutfile.get('docker_cmds', [])
        self.baseos = bases[(hutfile['baseos'])]
        self.stack = stacks[(hutfile['stack'])]
        self.from_image = "{}-{}".format(self.baseos.name, self.stack.name)

    @property
    def build_date(self):
        return int(time.time())

    def build(self, *args):
        super().build(*args)
        dockerfile = os.path.join(utils.STACKHUT_DIR, 'Dockerfile')
        self.gen_dockerfile('Dockerfile-service.txt', dict(service=self), dockerfile)
        self.build_dockerfile(self.name, self.author, self.version, dockerfile)




# Helper functions
# TODO - we should move these into a dep-style system - maybe use Makefiled in interrim
def run_barrister():
    # TODO - move barrister call into process as running on py2.7 ?
    if not os.path.exists(utils.STACKHUT_DIR):
        os.mkdir(utils.STACKHUT_DIR)
    sh.barrister('-j', utils.CONTRACTFILE, 'service.idl')
