#!/usr/bin/env python3
import logging
import os
import abc
import shutil
from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch
import pyconfig
import sh
from stackhut import utils
from stackhut.utils import log, AdminCmd

template_env = Environment(loader=FileSystemLoader(utils.get_res_path('templates')))

# Base OS's that we support
class BaseOS:
    name = ''

    @property
    def description(self):
        return "Base OS image using {}".format(self.name.capitalize())

    # TODO - replace these with a reqs.txt
    py3_packages = ['boto', 'sh', 'requests', 'markdown', 'redis', 'jinja2']

    def pip_install_cmd(self, packages):
        return 'pip3 install --no-cache-dir --compile {}'.format(packages.join(' '))


class Fedora(BaseOS):
    name = 'fedora'

    base_pkgs = ['python3', 'python3-pip']

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
        return self.install_os_pkg(self.base_pkgs)


class Alpine(BaseOS):
    name = 'alpine'

    base_pkgs = ['python3', 'ca-certificates']

    def os_pkg_cmd(self, pkgs):
        return 'apk --update add {}'.format(str.join(' ', pkgs))

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
        ] + self.install_os_pkg(self.base_pkgs)


# Language stacks that we support
class Stack:
    name = None
    entrypoint = None

    @property
    def description(self):
        return "Support for language stack {}".format(self.name.capitalize())

class Python(Stack):
    name = 'python'
    entrypoint = 'app.py'

    def install_stack_pkgs(self):
        return 'pip3 install --no-cache-dir --compile -r requirements.txt'



class NodeJS(Stack):
    name = 'nodejs'
    entrypoint = 'app.js'


# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python)
def get_stack_install_cmd(base_os, stack):
    return []  # installed by default

@dispatch(Alpine, Python)
def get_stack_install_cmd(base_os, stack):
    return []  # installed by default

@dispatch(Fedora, NodeJS)
def get_stack_install_cmd(base_os, stack):
    return None  # not supported

@dispatch(Alpine, NodeJS)
def get_stack_install_cmd(base_os, stack):
    pkgs = ['iojs@testing']
    return base_os.install_os_pkg(pkgs)

@dispatch(object, object)
def get_stack_install_cmd(base_os, stack):
    log.error("Os / Stack combo for {}/{} not implemented".format(base_os.name, stack.name))
    raise NotImplementedError()

# Main configs we support
bases = [Fedora(), Alpine()]
stacks = [Python(), NodeJS()]

def get_base(base_name):
    return [base for base in bases if base.name == base_name][0]

def get_stack(stack_name):
    return [stack for stack in stacks if stack.name == stack_name][0]

def write_dockerfile(dockerfile, dirname):
    dockerpath = os.path.join(dirname, 'Dockerfile')

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(dockerpath, 'w') as f:
        f.write(dockerfile)

    return dirname


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
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)



    def build_base(self, base):
        log.info("Building Dockerfile for base {}".format(base.name))
        template = template_env.get_template('Dockerfile-base.txt')
        rendered_template = template.render(base=base)
        log.debug(rendered_template)
        return write_dockerfile(rendered_template, os.path.join(self.outdir, base.name))

    def build_stack(self, base, stack):
        log.info("Building Dockerfile for base {} with stack {}".format(base.name, stack.name))
        template = template_env.get_template('Dockerfile-stack.txt')

        stack_install_cmds = get_stack_install_cmd(base, stack)
        if stack_install_cmds is not None:
            # only render the template if apy supported config
            rendered_template = template.render(base=base, stack=stack, stack_install_cmds=stack_install_cmds)
            logging.debug(rendered_template)
            outdir = os.path.join(self.outdir, "{}-{}".format(base.name, stack.name))
            return write_dockerfile(rendered_template, outdir)
        else:
            return None

    def dockerbuild_deploy(self, build_dirs):
        # loop over the dirs and build and push to dockerhub
        log.info("Build dirs - {}".format(build_dirs))
        root_dir = os.getcwd()
        for d in build_dirs:
            name = "stackhut/{}".format(d.split('/')[1])
            os.chdir(d)
            log.debug("Running docker build and push for {}".format(name))
            sh.docker('build', '-t', "{}:{}".format(name, 'latest'), '--rm', '.')
            if self.args.push:
                log.info("Pushing image {} to Docker Hub".format(name))
                sh.docker('push', '-f', name)
            os.chdir(root_dir)

    def run(self):
        super().run()
        base_dirs = [self.build_base(b) for b in bases]
        stack_dirs = [self.build_stack(b, s) for b in bases for s in stacks]
        build_dirs = [x for x in (base_dirs + stack_dirs) if x is not None]

        self.dockerbuild_deploy(build_dirs)
        log.info("All base OS and Stack images built and deployed")



class Service:
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
        self.base = get_base(hutfile['baseos'])
        self.stack = get_stack(hutfile['stack'])

        self.from_image = "{}-{}".format(self.base.name, self.stack.name)




class HutBuildCmd(utils.HutCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, 'build',
                                                               "Build a StackHut service", HutBuildCmd)
        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")

    def __init__(self, args):
        super().__init__(args)

    # TODO - run clean cmd first
    def run(self):
        super().run()

        service = Service(self.hutfile)

        # build the dockerfile
        template = template_env.get_template('Dockerfile-service.txt')
        rendered_template = template.render(service=service)
        write_dockerfile(rendered_template, '.stackhut')

        # setup
        # TODO - move barrister call into process as running on py2.7 ?
        sh.barrister('-j', utils.CONTRACTFILE, 'service.idl')
        # private clone for now - when OSS move into docker build
        log.debug("Copying stackhut app")
        shutil.rmtree('stackhut', ignore_errors=True)
        sh.git('clone', 'git@github.com:StackHut/stackhut-app.git', 'stackhut')
        shutil.rmtree('stackhut/.git')

        # run docker build
        log.debug("Running docker build")
        docker_name = "{}/{}:{}".format(service.author, service.name, service.version)
        sh.docker('build', '-f', '.stackhut/Dockerfile', '-t', docker_name, '--rm', '.')

        if self.args.push:
            log.info("Pushing image {} to Docker Hub".format(docker_name))
            sh.docker('push', '-f', docker_name)

        # cleanup

        shutil.rmtree('stackhut')
        log.info("{} build complete".format(service.name))













