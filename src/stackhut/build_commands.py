from __future__ import (unicode_literals, print_function, division, absolute_import)
from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
import os
import shutil
from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch
import sh
from stackhut import utils
from stackhut.utils import log, AdminCmd

template_env = Environment(loader=FileSystemLoader(utils.get_res_path('templates')))
root_dir = os.getcwdu()

class DockerEnv(object):
    def gen_dockerfile(self, template_name, template_params, dockerfile='Dockerfile'):
        rendered_template = template_env.get_template(template_name).render(template_params)
        with open(dockerfile, 'w') as f:
            f.write(rendered_template)

    def build_dockerfile(self, image_name, push=False, author='stackhut', version='latest', dockerfile='Dockerfile'):
        tag = "{}/{}:{}".format(author, image_name, version)
        log.debug("Running docker build for {}".format(tag))
        sh.docker('build', '-f', dockerfile, '-t', tag, '--rm', '.')
        if push:
            log.info("Pushing {} to Docker Hub".format(tag))
            sh.docker('push', '-f', tag)

    def stack_build(self, template_name, template_params, outdir, image_name, push=False):
        image_dir = os.path.join(outdir, image_name)
        if not os.path.exists(image_dir):
            os.mkdir(image_dir)
        os.chdir(image_dir)
        self.gen_dockerfile(template_name, template_params)
        self.build_dockerfile(image_name, push)
        os.chdir(root_dir)


# Base OS's that we support
class BaseOS(DockerEnv):
    name = None

    @property
    def description(self):
        return "Base OS image using {}".format(self.name.capitalize())

    def build(self, outdir, push):
        log.info("Building image for base {}".format(self.name))
        image_name = self.name
        super().stack_build('Dockerfile-baseos.txt', dict(baseos=self), outdir, image_name, push)

    # py3_packages = ['boto', 'sh', 'requests', 'markdown', 'redis', 'jinja2']
    # def pip_install_cmd(self, packages):
    #     return 'pip3 install --no-cache-dir --compile {}'.format(packages.join(' '))


class Fedora(BaseOS):
    name = 'fedora'

    baseos_pkgs = ['python', 'python-pip']

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

    baseos_pkgs = ['python', 'py-pip', 'ca-certificates']

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

    @property
    def description(self):
        return "Support for language stack {}".format(self.name.capitalize())

    def build(self, baseos, outdir, push):
        log.info("Building image for base {} with stack {}".format(baseos.name, self.name))
        image_name = "{}-{}".format(baseos.name, self.name)
        baseos_stack_pkgs = get_baseos_stack_pkgs(baseos, self)
        if baseos_stack_pkgs is not None:
            baseos_stack_cmds = baseos.install_os_pkg(baseos_stack_pkgs)
            # only render the template if apy supported config
            super().stack_build('Dockerfile-stack.txt',
                                dict(baseos=baseos, stack=self, baseos_stack_pkgs=baseos_stack_pkgs),
                                outdir, image_name, push)


class Python2(Stack):
    name = 'python2'
    entrypoint = 'app.py'

    def install_stack_pkgs(self):
        return 'pip2 install --no-cache-dir --compile -r requirements.txt'

class Python3(Stack):
    name = 'python3'
    entrypoint = 'app.py'

    def install_stack_pkgs(self):
        return 'pip3 install --no-cache-dir --compile -r requirements.txt'

class NodeJS(Stack):
    name = 'nodejs'
    entrypoint = 'app.js'


# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    return []  # installed by default

@dispatch(Alpine, Python2)
def get_baseos_stack_pkgs(base_os, stack):
    return []  # installed by default

@dispatch(Fedora, Python3)
def get_baseos_stack_pkgs(base_os, stack):
    return ['python3', 'python3-pip']

@dispatch(Alpine, Python3)
def get_baseos_stack_pkgs(base_os, stack):
    return ['python3']

@dispatch(Fedora, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    return None  # not supported

@dispatch(Alpine, NodeJS)
def get_baseos_stack_pkgs(base_os, stack):
    return ['iojs@testing', 'libstdc++@edge']

@dispatch(object, object)
def get_baseos_stack_pkgs(base_os, stack):
    log.error("Os / Stack combo for {}/{} not implemented".format(base_os.name, stack.name))
    raise NotImplementedError()

# Main configs we support
bases = [Fedora(), Alpine()]
stacks = [Python2(), Python3(), NodeJS()]

def get_base(base_name):
    return [base for base in bases if base.name == base_name][0]

def get_stack(stack_name):
    return [stack for stack in stacks if stack.name == stack_name][0]

class StackBuildCmd(AdminCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(StackBuildCmd, StackBuildCmd).parse_cmds(subparser, 'stackbuild',
                                                                   "Build the default OS and Stack images",
                                                                   StackBuildCmd)
        subparser.add_argument("--outdir", '-o', default='stacks',
                               help="Directory to save stacks to")
        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")

    def __init__(self, args):
        super().__init__(args)
        self.outdir = args.outdir
        self.push = args.push
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)

    def run(self):
        super().run()
        # build bases and stacks
        [b.build(self.outdir, self.push) for b in bases]
        [s.build(b, self.outdir, self.push) for b in bases for s in stacks]
        log.info("All base OS and Stack images built and deployed")



class Service(DockerEnv):

    def __init__(self, hutfile):
        # get vals from the hutfile
        self.name = hutfile['name'].lower()
        self.author = hutfile['author'].lower()
        self.email = hutfile['contact']
        self.version = 'latest'
        self.description = hutfile['description']
        self.files = hutfile['files'] if 'files' in hutfile else []
        self.os_deps = []
        self.lang_deps = False
        self.docker_cmds = []
        self.baseos = get_base(hutfile['baseos'])
        self.stack = get_stack(hutfile['stack'])
        self.from_image = "{}-{}".format(self.baseos.name, self.stack.name)

    def build(self, push):
        dockerfile = os.path.join(utils.STACKHUT_DIR, 'Dockerfile')
        self.gen_dockerfile('Dockerfile-service.txt', dict(service=self), dockerfile)
        self.build_dockerfile(self.name, push, self.author, self.version, dockerfile)


class HutBuildCmd(utils.HutCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, 'build',
                                                               "Build a StackHut service", HutBuildCmd)
        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")

    def __init__(self, args):
        super().__init__(args)
        self.push = args.push

# TODO - run clean cmd first
    def run(self):
        super().run()

        # setup
        # TODO - move barrister call into process as running on py2.7 ?
        if not os.path.exists(utils.STACKHUT_DIR):
            os.mkdir(utils.STACKHUT_DIR)

        sh.barrister('-j', utils.CONTRACTFILE, 'service.idl')
        # private clone for now - when OSS move into docker build
        log.debug("Copying stackhut app")
        shutil.rmtree('stackhut', ignore_errors=True)
        sh.git('clone', 'git@github.com:StackHut/stackhut-app.git', 'stackhut')
        shutil.rmtree('stackhut/.git')

        # Docker build
        service = Service(self.hutfile)
        service.build(self.push)

        # cleanup
        shutil.rmtree('stackhut')
        log.info("{} build complete".format(service.name))

