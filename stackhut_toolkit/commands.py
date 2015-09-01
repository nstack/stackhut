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
Toolkit subcommands
"""
import json
import os
import getpass
import uuid
from distutils.dir_util import copy_tree

import sh
from jinja2 import Environment, FileSystemLoader

from stackhut_common.utils import log, CONTRACTFILE
from stackhut_common.runtime import rpc
from stackhut_common.runtime.backends import LocalBackend
from stackhut_common.runtime.runner import ServiceRunner
from stackhut_common.commands import BaseCmd, HutCmd
from stackhut_common.config import HutfileCfg, UserCfg
from . import __version__
from .utils import *
from .builder import Service, bases, stacks, is_stack_supported, get_docker, OS_TYPE


class UserCmd(BaseCmd):
    """User commands require the userconfig file"""
    def __init__(self, args):
        super().__init__(args)
        self.usercfg = UserCfg()
        keen_client.start(self.usercfg)

    def run(self):
        super().run()

        args = {k: v for (k, v)
                in vars(self.args).items()
                if k not in ['func', 'command']}
        keen_client.send('cli_cmd', dict(cmd=self.name, args=args))


class LoginCmd(UserCmd):
    name = 'login'
    description = "Login to StackHut"

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        import hashlib
        super().run()
        username = input("Username: ")
        # email = input("Email: ")
        password = getpass.getpass("Password: ")

        # connect securely to Stackhut service to get hash
        r = stackhut_api_call('login', dict(username=username, password=password))

        if r['success']:
            # self.usercfg['docker_username'] = docker_username
            self.usercfg['username'] = username
            self.usercfg['hash'] = r['hash']
            self.usercfg['u_id'] = hashlib.sha256(("stackhut_is_da_bomb" + username).encode('utf-8')).hexdigest()
            # self.usercfg['email'] = r['email']
            self.usercfg.save()
            log.info("User {} logged in successfully".format(username))
        else:
            raise RuntimeError("Incorrect username or password, please try again")

        return 0


class LogoutCmd(UserCmd):
    name = 'logout'
    description = "Logout from StackHut"

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        super().run()
        # connect to Stackhut service to get hash?
        log.info("Logged out {}".format(self.usercfg.get('email', '')))
        self.usercfg.wipe()
        return 0


class InfoCmd(UserCmd):
    name = 'info'
    description = "Display info for StackHut"

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        super().run()

        # log sys info
        log.info("StackHut version {}".format(__version__))

        # docker info
        docker = get_docker(_exit=False, verbose=False)
        if docker:
            log.info("Docker version {}".format(docker.client.version().get('Version')))
        else:
            log.info("Docker not installed or connection error")

        # usercfg info
        if self.usercfg.logged_in:
            log.info("User logged in")

            for x in self.usercfg.show_keys:
                log.info("{}: {}".format(x, self.usercfg.get(x)))
        else:
            log.info("User not logged in")

        return 0


class StackBuildCmd(UserCmd):
    """Build StackHut service using docker"""
    visible = False
    name = 'stackbuild'

    @staticmethod
    def register(sp):
        sp.add_argument("--outdir", '-o', default='stacks', help="Directory to save stacks to")
        sp.add_argument("--push", '-p', action='store_true', help="Push image to public after")
        sp.add_argument("--no-cache", '-n', action='store_true', help="Disable cache during build")

    def __init__(self, args):
        super().__init__(args)
        self.outdir = args.outdir
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)

    def run(self):
        super().run()

        # Python, y u no have assert function??
        assert self.usercfg.username == 'stackhut', "Must be logged in as StackHut user to build & deploy these"

        # build bases and stacks
        [b.build_push(self.outdir, self.args.push, self.args.no_cache) for b in bases.values()]
        [s.build_push(b, self.outdir, self.args.push, self.args.no_cache)
         for b in bases.values()
         for s in stacks.values()]
        log.info("All base OS and Stack images built and deployed")
        return 0


class InitCmd(UserCmd):
    name = 'init'
    description = "Initialise a new StackHut service"

    @staticmethod
    def register(sp):
        sp.add_argument("baseos", help="Base Operating System", choices=bases.keys())
        sp.add_argument("stack", help="Language stack to support", choices=stacks.keys())
        sp.add_argument("--no-git", '-n', action='store_true', help="Disable creating a git repo")

    def __init__(self, args):
        super().__init__(args)
        self.baseos = bases[args.baseos]
        self.stack = stacks[args.stack]
        self.task_id = uuid.uuid4()

    def render_file(self, env, fname, params):
        rendered_template = env.get_template(fname).render(params)
        with open(fname, 'w') as f:
            f.write(rendered_template)

    def run(self):
        super().run()

        # validation checks
        self.usercfg.assert_logged_in()

        if os.path.exists('.git') or os.path.exists('Hutfile.yaml'):
            raise RuntimeError('Found existing project, cancelling')

        if not is_stack_supported(self.baseos, self.stack):
            raise ValueError("Sorry, the combination of {} and {} is currently unsupported".format(self.baseos, self.stack))

        # set and check service name
        self.name = os.path.basename(os.getcwd())
        HutfileCfg.assert_valid_name(self.name)

        self.author = self.usercfg.username
        log.info("Creating service {}/{}".format(self.author, self.name))

        # copy the scaffolds into the service
        def copy_scaffold(name):
            dir_path = get_res_path(os.path.join('scaffold', name))
            copy_tree(dir_path, '.')
            return os.listdir(dir_path)

        common_files = copy_scaffold('common')
        stack_files = copy_scaffold(self.stack.name)

        # run the templates
        template_env = Environment(loader=FileSystemLoader('.'))
        [self.render_file(template_env, f, dict(scaffold=self))
         for f in (common_files + stack_files) if os.path.exists(f) and os.path.isfile(f)]

        # git commit
        if not self.args.no_git:
            sh.git.init()
            sh.git.add(".")
            sh.git.commit(m="Initial commit")
            sh.git.branch("stackhut")

        return 0


class HutBuildCmd(HutCmd, UserCmd):
    """Build StackHut service using docker"""
    name = 'build'
    description = "Build a StackHut service"

    @staticmethod
    def register(sp):
        sp.add_argument("--full", '-l', action='store_true', help="Run a full build")
        sp.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")
        sp.add_argument("--dev", '-d', action='store_true', help="Install dev version of StackHut Runner")

    def __init__(self, args):
        super().__init__(args)
        #self.no_cache = self.args.full if 'full' in self.args else False
        #self.force = self.args.force if 'force' in self.args else False
        self.no_cache = args.full
        self.force = args.force
        self.dev = args.dev

    # TODO - run clean cmd first
    def run(self):
        super().run()
        # Docker builder
        service = Service(self.hutcfg, self.usercfg.username)
        service.build_push(force=self.force, dev=self.dev, no_cache=self.no_cache)
        return 0


class RemoteBuildCmd(HutCmd):
    """Build StackHut service using docker"""
    name = 'remotebuild'
    description = "Build a StackHut service"
    visible = False

    @staticmethod
    def register(sp):
        sp.add_argument("--dev", action='store_true', help="Install dev version of StackHut Runner")
        sp.add_argument("author", help="Service author")

    def __init__(self, args):
        super().__init__(args)
        self.dev = args.dev
        self.author = args.author

    def run(self):
        super().run()
        # Docker builder
        service = Service(self.hutcfg, self.author)
        service.build_push(force=True, dev=self.dev, no_cache=False, push=True)
        return 0


class RunContainerCmd(HutCmd, UserCmd):
    """"Concrete Run Command within a container"""
    name = 'runcontainer'
    description = "Run StackHut service in a container"

    @staticmethod
    def register(sp):
        sp.add_argument("port", nargs='?', default='4001', help="Port to host API on locally", type=int)
        # sp.add_argument("--reqfile", '-r', help="Test request file")
        sp.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")
        sp.add_argument("--privileged", '-p', action='store_true', help="Run as a privileged service")

    def __init__(self, args):
        super().__init__(args)
        # self.reqfile = args.reqfile
        self.port = args.port
        self.force = args.force
        self.privileged = args.privileged

    def run(self):
        super().run()

        # Docker builder (if needed)
        service = Service(self.hutcfg, self.usercfg.username)
        service.build_push(force=self.force)

        host_store_dir = os.path.abspath(LocalBackend.local_store)
        os.mkdir(host_store_dir) if not os.path.exists(host_store_dir) else None

        # docker setup
        docker = get_docker()

        log.info("Running service '{}' on http://{}:{}".format(self.hutcfg.service_short_name(self.usercfg.username), docker.ip, self.port))
        # call docker to run the same command but in the container
        # use data vols for response output files
        # NOTE - SELINUX issues - can remove once Docker 1.7 becomes mainstream
        import random

        name = 'stackhut-{}'.format(random.randrange(10000))
        res_flag = 'z' if OS_TYPE == 'SELINUX' else 'rw'
        verbose_mode = '-v' if self.args.verbose else None
        uid_gid = '{}:{}'.format(os.getuid(), os.getgid())
        args = ['-p', '{}:4001'.format(self.port),
                '-v', '{}:/workdir/{}:{}'.format(host_store_dir, LocalBackend.local_store, res_flag),
                '--rm=true', '--name={}'.format(name),
                '--privileged' if self.args.privileged else None,
                '--entrypoint=/usr/bin/env', service.full_name, 'stackhut-runner', verbose_mode,
                'runcontainer', '--uid', uid_gid, '--author', self.usercfg.username]
        args = [x for x in args if x is not None]

        log.info("**** START SERVICE LOG ****")

        try:
            out = docker.run_docker_sh('run', args, _out=lambda x: print(x, end=''))

            # if self.reqfile:
            #     host_req_file = os.path.abspath(self.reqfile)
            #     log.debug("Send file using reqs here")
        except KeyboardInterrupt:
            log.debug("Shutting down service container, press again to force-quit...")
            # out.kill()
            docker.run_docker_sh('stop', ['-t', '5', name])

        log.info("**** END SERVICE LOG ****")
        log.info("Run completed successfully")
        return 0

class RunHostCmd(HutCmd, UserCmd):
    """Concrete Run Command using Local system for dev on Host OS"""
    name = 'runhost'
    description = "Run StackHut service on host OS"

    @staticmethod
    def register(sp):
        sp.add_argument("port", nargs='?', default='4001', help="Port to host API on locally", type=int)

    def __init__(self, args):
        super().__init__(args)
        self.port = args.port

    def run(self):
        toolkit_stack = stacks[self.hutcfg.stack]
        toolkit_stack.copy_shim()
        rpc.generate_contract()

        try:
            backend = LocalBackend(self.hutcfg, self.usercfg.username, port=self.port)
            with ServiceRunner(backend, self.hutcfg) as runner:
                log.info("Running service '{}' on http://127.0.0.1:{}".format(backend.service_short_name, self.port))
                runner.run()
        finally:
            toolkit_stack.del_shim()
            os.remove(rpc.REQ_FIFO)
            os.remove(rpc.RESP_FIFO)


class DeployCmd(HutCmd, UserCmd):
    name = 'deploy'
    description = "Deploy service to StackHut"

    @staticmethod
    def register(sp):
        sp.add_argument("--no-build", '-n', action='store_true', help="Deploy without re-building & pushing the image")
        sp.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")
        sp.add_argument("--local", '-l', action='store_true', help="Perform image build & push locally rather than remote")
        sp.add_argument("--dev", default=False, action='store_true', help="Install dev version of StackHut Runner")

    def __init__(self, args):
        super().__init__(args)
        self.no_build = args.no_build
        self.force = args.force
        self.local = args.local
        self.dev = args.dev

    def create_methods(self):
        with open(CONTRACTFILE, 'r') as f:
            contract = json.load(f)

        # remove the common.barrister element
        interfaces = [x for x in contract if 'barrister_version' not in x and x['type'] == 'interface']

        def render_param(param):
            # main render function
            array_t = "[]" if param.get('is_array') else ''
            name_type_t = param_t = "{}{}".format(array_t, param['type'])
            if 'name' in param:
                return "{} {}".format(param['name'], name_type_t)
            else:
                return name_type_t

        def render_params(params):
            return [render_param(p) for p in params]

        def render_signature(method):
            params_t = str.join(', ', render_params(method['params']))
            return "{}({}) {}".format(method['name'], params_t, render_param(method['returns']))

        for i in interfaces:
            for f in i['functions']:
                f['signature'] = render_signature(f)
                log.debug("Signature for {}.{} is \"{}\"".format(i['name'], f['name'], f['signature']))

        return interfaces

    def _read_file(self, fname):
        x = None
        if os.path.exists(fname):
            with open(fname) as f:
                x = f.read()
        return x

    def run(self):
        super().run()
        service = Service(self.hutcfg, self.usercfg.username)

        # run the contract regardless
        rpc.generate_contract()

        if self.local:
            # call build+push first using Docker builder
            if not self.no_build:
                service.build_push(force=self.force, push=True, dev=self.dev)
        else:
            import tempfile
            import requests
            import os.path
            from stackhut_common import utils
            from stackhut_client import client
            log.info("Starting Remote build, this may take a while (especially the first time), please wait...")

            # compress and upload the service
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as f:
                f.close()

            # get the upload url
            r_file = stackhut_api_user_call('file', dict(filename=os.path.basename(f.name)), self.usercfg)

            sh.tar('-czvf', f.name, '--exclude', ".git", '--exclude', "__pycache__", '--exclude', "run_result", '--exclude', ".stackhut", '.')
            log.debug("Uploading package {} ({:.2f} Kb)...".format(f.name, os.path.getsize(f.name)/1024))
            with open(f.name, 'rb') as f1:
                with Spinner():
                    r = requests.put(r_file['url'], data=f1)
                r.raise_for_status()
            # remove temp file
            os.unlink(f.name)

            # call the remote build service
            auth = client.SHAuth(self.usercfg.username, hash=self.usercfg['hash'])
            sh_client = client.SHService('stackhut', 'stackhut', auth=auth, host=utils.SERVER_URL)
            log.debug("Uploaded package, calling remote build...")
            try:
                with Spinner():
                    r = sh_client.Default.remoteBuild(r_file['key'], self.dev)

            except client.SHRPCError as e:
                log.error("Build error, remote build output below...")
                log.error(e.data['output'])
                return 1
            else:

                log.debug("Remote build output...\n" + r['cmdOutput'])
                if not r['success']:
                    raise RuntimeError("Build failed")
                log.info("...completed Remote build")

        # Inform the SH server re the new/updated service
        # build up the deploy message body
        test_request = json.loads(self._read_file('test_request.json'))
        readme = self._read_file('README.md')

        data = {
            'service': service.short_name,  # StackHut Service,
            'github_url': self.hutcfg.github_url,
            'example_request': test_request,
            'description': self.hutcfg.description,
            'private_service': self.hutcfg.private,
            'readme': readme,
            'schema': self.create_methods()
        }

        log.info("Deploying image '{}' to StackHut".format(service.short_name))
        r = stackhut_api_user_call('add', data, self.usercfg)
        log.info("Service {} has been {} and is live".format(service.short_name, r['message']))
        log.info("You can now call this service with our client-libs or directly over JSON+HTTP")
        return 0



# StackHut primary toolkit commands
# debug, push, pull, test, etc.
COMMANDS = [
    # visible
    LoginCmd, LogoutCmd, InfoCmd,
    InitCmd,
    HutBuildCmd, RunContainerCmd, RunHostCmd, DeployCmd,
    # hidden
    StackBuildCmd, RemoteBuildCmd
]
