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
Builder module used to communicate with Docker and build
our specific OSs, stacks, & runtimes
"""
import os
import sys
import time
import json
from distutils.dir_util import copy_tree

from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch
import sh
import arrow
import docker as docker_py
from docker.utils import kwargs_from_env
from docker.errors import DockerException

from stackhut_common import utils
from stackhut_common.runtime import rpc
from stackhut_common.utils import log
from stackhut_toolkit import utils as t_utils

template_env = Environment(loader=FileSystemLoader(t_utils.get_res_path('templates')))

# OS Types - for docker flags
OS_TYPE = None
try:
    os_str = (str(sh.lsb_release('-i', '-s'))).strip()
    if os_str in ['Fedora']:
        OS_TYPE = 'SELINUX'
    else:
        OS_TYPE = 'UNKNOWN'
except sh.CommandNotFound as e:
    OS_TYPE = 'UNKNOWN'


# TODO - move to docker machine/toolkit instead
class DockerClient:
    client = None
    ip = 'localhost'
    x = "https://github.com/boot2docker/boot2docker/blob/master/doc/WORKAROUNDS.md"

    def __init__(self, _exit, verbose):
        # setup_client
        try:
            # setup client depending if running on linux or using boot2docker (osx/win)
            if sys.platform == 'linux':
                self.client = docker_py.Client(version='auto')
            else:
                # get b2d ip
                self.ip = str(sh.boot2docker.ip()).strip()

                try:
                    # try secure connection first
                    kw = kwargs_from_env(assert_hostname=False)
                    self.client = docker_py.Client(version='auto', **kw)
                except docker_py.errors.DockerException as e:
                    # shit - some weird boot2docker, python, docker-py, requests, and ssl error
                    # https://github.com/docker/docker-py/issues/465
                    if verbose:
                        log.debug(e)
                    log.warn("Cannot connect securely to Docker, trying insecurely")
                    kw = kwargs_from_env(assert_hostname=False)
                    if 'tls' in kw:
                        kw['tls'].verify = False
                    self.client = docker_py.Client(version='auto', **kw)

        except Exception as e:
            if verbose:
                log.error("Could not connect to Docker - try running 'docker info' first")
                if sys.platform != 'linux':
                    log.error("Please ensure you've run 'boot2docker up' and 'boot2docker shellinit' first and have added the ENV VARs it suggests")
            if _exit:
                raise e

    def run_docker_sh(self, docker_cmd, docker_args=None, **kwargs):
        _docker_args = docker_args if docker_args is not None else []
        _docker_args.insert(0, docker_cmd)
        log.debug("Running 'docker {}' with args {}".format(docker_cmd, _docker_args[1:]))
        return sh.docker(_docker_args, **kwargs)

docker_client = None

def get_docker(_exit=True, verbose=True):
    global docker_client
    docker_client = docker_client if docker_client is not None else DockerClient(_exit, verbose)
    return docker_client


class DockerBuild:
    def __init__(self, push=False, no_cache=False):
        self.push = push
        self.no_cache = no_cache
        self.docker = get_docker()

    def gen_dockerfile(self, template_name, template_params, dockerfile='Dockerfile'):
        rendered_template = template_env.get_template(template_name).render(template_params)
        with open(dockerfile, 'w') as f:
            f.write(rendered_template)

    def build_dockerfile(self, tag, dockerfile='Dockerfile'):
        log.debug("Running docker build for {}".format(tag))
        cache_flag = '--no-cache=True' if self.no_cache else '--no-cache=False'
        cmds = ['-f', dockerfile, '-t', tag, '--rm', cache_flag, '.']
        log.info("Starting build, this may take some time, please wait...")

        try:
            if utils.VERBOSE:
                self.docker.run_docker_sh('build', cmds, _out=lambda x: log.debug(x.strip()))
            else:
                self.docker.run_docker_sh('build', cmds)
        except sh.ErrorReturnCode as e:
            log.error("Couldn't complete build")
            log.error("Build error - {}".format(e.stderr.decode('utf-8').strip()))
            if not utils.VERBOSE:
                log.error("Build Traceback - \n{}".format(e.stdout.decode('utf-8').strip()))
            raise RuntimeError("Docker Build failed") from None

    def push_image(self, tag):
        if self.push:
            log.info("Uploading image {} - this may take a while...".format(tag))
            r = self.docker.client.push(tag, stream=True)
            r_summary = [json.loads(x.decode('utf-8')) for x in r][-1]

            if 'error' in r_summary:
                log.error(r_summary['error'])
                log.error(r_summary['errorDetail'])
                raise RuntimeError("Error pushing to Docker Hub, check your connection and auth details")
            else:
                log.debug(r_summary['status'])
                # log.error("Error pushing to Docker Hub - {}".format(r_summary['error']))

            # docker.run_docker_sh('push', tag, _in='Y')

    def stack_build_push(self, template_name, template_params, outdir, image_name):
        """Called by StackHut builders to build BaseOS and Stack images"""
        image_dir = os.path.join(outdir, image_name)
        os.mkdir(image_dir) if not os.path.exists(image_dir) else None

        os.chdir(image_dir)

        self.gen_dockerfile(template_name, template_params)
        # hardcode the service under stackhut name
        tag = "{}/{}:{}".format('stackhut', image_name, 'latest')

        self.build_dockerfile(tag)
        self.push_image(tag)

        os.chdir(utils.ROOT_DIR)


# Base OS's that we support
class BaseOS:
    name = None
    tag = 'latest'
    baseos_pkgs = []
    # Override and set pre- and post- commands if needed for initial OS setup
    pre = []
    post = []
    py_update = ['python3 /get-pip.py',
                 'rm /get-pip.py'
                 ]

    def __init__(self):
        super().__init__()

    def install_os_pkg(self, pkgs):
        return []

    @property
    def description(self):
        return "Base OS image using {}".format(self.name.capitalize())

    def build_push(self, outdir, *args):
        log.info("Building image for base {}".format(self.name))
        image_name = self.name
        builder = DockerBuild(*args)
        builder.stack_build_push('Dockerfile-baseos.txt', dict(baseos=self), outdir, image_name)

    def setup_cmds(self):
        return self.pre + self.install_os_pkg(self.baseos_pkgs) + self.post + self.py_update


class Fedora(BaseOS):
    name = 'fedora'

    baseos_pkgs = ['python3']

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


class Debian(BaseOS):
    name = 'debian'
    baseos_pkgs = ['python3']
    pre = []

    def os_pkg_cmd(self, pkgs):
        return 'apt-get install -y --no-install-recommends {}'.format(' '.join(pkgs))

    def install_os_pkg(self, pkgs):
        return [
            'apt-get -y update',
            self.os_pkg_cmd(pkgs),
            'apt-get -y clean',
            'apt-get -y autoclean',
            'apt-get -y autoremove --purge',
            'rm -rf /var/lib/apt/lists/*',
            'rm -rf /usr/share/locale/*',
            'rm -rf /usr/share/doc/*',
            # 'journalctl --vacuum-size=0',
            'rm -rf /var/log/* || true',
            'rm -rf /var/cache/*',
            'rm -rf /tmp/*',
        ]

class Ubuntu(Debian):
    name = 'ubuntu'
    tag = 'vivid'

# Alpine disabled for now while Python threading bug on musl exists
# class Alpine(BaseOS):
#     name = 'alpine'
#
#     baseos_pkgs = ['python3', 'ca-certificates']
#     pre = [
#         'echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories',
#         'echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories',
#     ]
#
#     def os_pkg_cmd(self, pkgs):
#         return 'apk --update add {}'.format(' '.join(pkgs))
#
#     def install_os_pkg(self, pkgs):
#         return [
#             self.os_pkg_cmd(pkgs),
#             'rm -rf /usr/share/locale/*',
#             'rm -rf /usr/share/doc/*',
#             'rm -rf /var/log/* || true',
#             'rm -rf /var/cache/*',
#             'rm -rf /tmp/*',
#             'mkdir /var/cache/apk',
#         ]
#




###############################################################################
# Language stacks that we support
class Stack:
    name = None
    entrypoint = None
    stack_packages = None
    package_file = None
    shim_files = None
    shim_cmd = None

    def __init__(self):
        super().__init__()

    @property
    def description(self):
        return "Support for language stack {}".format(self.name.capitalize())

    def build_push(self, baseos, outdir, *args):
        log.info("Building image for base {} with stack {}".format(baseos.name, self.name))
        image_name = "{}-{}".format(baseos.name, self.name)
        baseos_stack_cmds_pkgs = get_baseos_stack_pkgs(baseos, self)
        if baseos_stack_cmds_pkgs is not None:
            os_cmds, pkgs = baseos_stack_cmds_pkgs
            pkg_cmds = baseos.install_os_pkg(pkgs) if pkgs else []
            stack_cmds = os_cmds + pkg_cmds

            # only render the template if apy supported config
            builder = DockerBuild(*args)
            builder.stack_build_push('Dockerfile-stack.txt',
                                     dict(baseos=baseos, stack=self, stack_cmds=stack_cmds),
                                     outdir, image_name)

    def install_service_packages(self):
        """Anything needed to run the service"""
        return ''

    def install_stack_packages(self):
        """Anything needed to run the stack"""
        return ''

    @property
    def service_package_files(self):
        return self.package_file if os.path.exists(self.package_file) else None

    # TODO - keep shim in project dir and only update on build/run if newer
    def copy_shim(self):
        shim_dir = os.path.join(t_utils.get_res_path('shims'), self.name)
        copy_tree(shim_dir, utils.ROOT_DIR)

    # def link_shim(self):
    #     shim_dir = os.path.join(utils.get_res_path('shims'), self.name)
    #     for f in self.shim_files:
    #         os.symlink(os.path.join(shim_dir, f), f)

    def del_shim(self):
        # log.debug(sh.ls('-lrta'))
        for f in self.shim_files:
            os.remove(os.path.join(utils.ROOT_DIR, f))


class Python(Stack):
    name = 'python'
    entrypoint = 'app.py'
    stack_packages = ['requests', 'sh']
    package_file = 'requirements.txt'

    shim_files = ['runner.py', 'stackhut.py']
    shim_cmd = ['/usr/bin/env', 'python3', 'runner.py']

    def install_stack_packages(self):
        return 'pip3 install --no-cache-dir --compile {}'.format(str.join(' ', self.stack_packages))

    def install_service_packages(self):
        return 'pip3 install --no-cache-dir --compile -r {}'.format(self.package_file)


class NodeJS(Stack):
    name = 'nodejs'
    entrypoint = 'app.js'
    stack_packages = ['request']
    package_file = 'package.json'

    shim_files = ['runner.js', 'stackhut.js']
    shim_cmd = ['/usr/bin/env', 'node', '--harmony', 'runner.js']

    def install_stack_packages(self):
        return 'npm install {}'.format(str.join(' ', self.stack_packages))

    def install_service_packages(self):
        return 'npm install; exit 0'

# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return [], []  # installed by default

@dispatch(Debian, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return [], []  # installed by default

@dispatch(Ubuntu, Python)
def get_baseos_stack_pkgs(base_os, stack):
    return [], []  # installed by default

@dispatch(Fedora, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    cmds = ['dnf -y install dnf-plugins-core',
            'dnf -y copr enable nibbler/iojs',
            ]
    pkgs = ['iojs', 'iojs-npm']
    return cmds, pkgs

@dispatch(Ubuntu, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    cmds = ['apt-get update',
            'apt-get install -y curl',
            'curl -sL https://deb.nodesource.com/setup_iojs_3.x | bash -',
            'apt-get remove --purge -y curl',
            ]
    pkgs = ['iojs']
    return cmds, pkgs

@dispatch(Debian, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    cmds = ['apt-get update',
            'apt-get install -y curl',
            'curl -sL https://deb.nodesource.com/setup_iojs_3.x | bash -',
            'apt-get remove --purge -y curl',
            ]
    pkgs = ['iojs']
    return cmds, pkgs

# @dispatch(Alpine, NodeJS)
# def get_baseos_stack_pkgs(base_os, stack):
#     return [], ['iojs@testing', 'libstdc++@edge']

@dispatch(object, object)
def get_baseos_stack_pkgs(base_os, stack):
    log.debug("OS / Stack combo for {}/{} not implemented".format(base_os.name, stack.name))
    return None

bases = dict([(b.name, b) for b in [Debian(), Ubuntu(), Fedora()]])
stacks = dict([(s.name, s) for s in [NodeJS(), Python()]])

# bases = dict([(b.name, b) for b in [Debian()]])
# stacks = dict([(s.name, s) for s in [NodeJS()]])

def is_stack_supported(base, stack):
    """Return true if the baseos & stack combination is supported"""
    return False if get_baseos_stack_pkgs(base, stack) is None else True

###############################################################################
class Service:
    """Main primitive representing a StackHut service"""
    def __init__(self, hutcfg, author):
        super().__init__()
        self.hutcfg = hutcfg
        self.baseos = bases[hutcfg.baseos]
        self.stack = stacks[hutcfg.stack]

        self.short_name = hutcfg.service_short_name(author)
        self.repo_name = 'registry.stackhut.com:5000/{}'.format(self.short_name.split(':')[0])
        self.full_name = 'registry.stackhut.com:5000/{}'.format(self.short_name)
        self.dev = False

    @property
    def build_date(self):
        return int(time.time())

    @property
    def image_exists(self):
        repo_images = get_docker().client.images(self.repo_name)
        service_images = [x for x in repo_images if self.full_name in x['RepoTags']]
        assert len(service_images) < 2, "{} versions of {} found in Docker".format(self.full_name)
        return True if len(service_images) > 0 else False

    def _files_mtime(self):
        """Recurse over all files referenced by project and find max mtime"""
        def max_mtime(dirpath, fnames):
            """return max mtime from list of files in a dir"""
            mtimes = (os.path.getmtime(os.path.join(dirpath, fname)) for fname in fnames)
            return max(mtimes)

        def max_mtime_dir(dirname):
            """find max mtime of a single file in dir recurseively"""
            for (dirpath, dirnames, fnames) in os.walk(dirname):
                log.debug("Walking dir {}".format(dirname))
                return max_mtime(dirpath, fnames)

        stack = stacks[self.hutcfg.stack]
        default_files = [stack.entrypoint, stack.package_file, 'api.idl', 'Hutfile.yaml']

        # find the max - from default files, hut file and hut dirs
        max_mtime_default_files = max_mtime(os.getcwd(), default_files)
        max_mtime_hutfiles = max_mtime(os.getcwd(), self.hutcfg.files) if self.hutcfg.files else 0
        max_mtime_hutdirs = max((max_mtime_dir(dirname) for dirname in self.hutcfg.dirs)) if self.hutcfg.dirs else 0

        return max([max_mtime_default_files, max_mtime_hutfiles, max_mtime_hutdirs])

    def image_stale(self):
        """Runs the build only if a file has changed"""
        max_mtime = self._files_mtime()

        image_info = get_docker().client.inspect_image(self.full_name)
        image_build_string = image_info['Created']

        log.debug("Service {} last built at {}".format(self.short_name, image_build_string))
        build_date = arrow.get(image_build_string).datetime.timestamp()
        log.debug("Files max mtime is {}, image build date is {}".format(max_mtime, build_date))

        return max_mtime >= build_date

    def build_push(self, force=False, dev=False, push=False, no_cache=False):
        """
        Builds a user service, if changed, and pushes  to repo if requested
        """
        builder = DockerBuild(push, no_cache)
        self.dev = dev
        dockerfile = '.Dockerfile'

        if force or not self.image_exists or self.image_stale():
            log.debug("Image not found or stale - building...")
            # run barrister and copy shim
            rpc.generate_contract()
            self.stack.copy_shim()

            try:
                builder.gen_dockerfile('Dockerfile-service.txt', dict(service=self), dockerfile)
                builder.build_dockerfile(self.full_name, dockerfile)
            finally:
                self.stack.del_shim()

            log.info("{} build complete".format(self.short_name))
        else:
            log.info("Build not necessary, run with '--force' to override")

        builder.push_image(self.full_name)
