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

# TODO - small toolkit.commands go here...
# different classes for common tasks
# i.e. shell out, python code, etc.
# & payload pattern matching helper classes
import json
import os
import getpass
import uuid
import sh
from jinja2 import Environment, FileSystemLoader
from distutils.dir_util import copy_tree

from stackhut.common import utils
from stackhut.common.utils import log, BaseCmd, HutCmd, HutfileCfg, keen_client
from stackhut.common.primitives import Service, bases, stacks, is_stack_supported, get_docker
from stackhut import __version__


class UserCmd(BaseCmd):
    """User commands require the userconfig file"""
    def __init__(self, args):
        super().__init__(args)
        self.usercfg = utils.UserCfg()
        keen_client.start(self.usercfg)

    def run(self):
        super().run()
        args = {k: v for (k, v)
                in vars(self.args).items()
                if k not in ['func', 'command']}

        keen_client.send('cli_cmd',
                         dict(cmd=self.name,
                              args=args))

class LoginCmd(UserCmd):
    name = 'login'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(LoginCmd, LoginCmd).parse_cmds(subparser, LoginCmd.name,
                                                         "login to stackhut", LoginCmd)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        import hashlib
        super().run()
        # get docker username
        # NOTE - this is so hacky - why does cli return username but REST API doesn't
        try:
            stdout = sh.docker.info()
            docker_user_list = [x for x in stdout if x.startswith('Username')]
            if len(docker_user_list) == 1:
                docker_username = docker_user_list[0].split(':')[1].strip()
                log.debug("Docker user is '{}', note this may be different to your StackHut login".format(docker_username))
            else:
                raise RuntimeError("Please run 'docker login' first")
        except sh.ErrorReturnCode as e:
            raise OSError("Could not connect to Docker - try running 'docker info', "
                          "and if you are on OSX make sure you've run 'boot2docker up' first")

        username = input("Username: ")
        # email = input("Email: ")
        password = getpass.getpass("Password: ")

        # connect securely to Stackhut service to get hash
        r = utils.stackhut_api_call('login', dict(username=username, password=password))

        if r['success']:
            self.usercfg['docker_username'] = docker_username
            self.usercfg['username'] = username
            self.usercfg['hash'] = r['hash']
            self.usercfg['u_id'] = hashlib.sha256(username.encode('utf-8')).hexdigest()
            # self.usercfg['email'] = r['email']
            self.usercfg.save()
            log.info("User {} logged in successfully".format(username))
        else:
            raise RuntimeError("Incorrect username or password, please try again")

        return 0

class LogoutCmd(UserCmd):
    name = 'logout'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(LogoutCmd, LogoutCmd).parse_cmds(subparser, LogoutCmd.name,
                                                           "logout to stackhut", LogoutCmd)

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

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(InfoCmd, InfoCmd).parse_cmds(subparser, InfoCmd.name,
                                                       "Stackhut Infomation", InfoCmd)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        super().run()

        # log sys info
        log.info("StackHut version {}".format(__version__))

        docker = get_docker(_exit=False)
        if docker:
            log.info("Docker version {}".format(docker.version().get('Version')))
        else:
            log.info("Docker not installed or connection error")

        if self.usercfg.logged_in:
            log.info("User logged in")

            for x in self.usercfg.show_keys:
                log.info("{}: {}".format(x, self.usercfg.get(x)))
        else:
            log.info("User not logged in")

        return 0


class StackBuildCmd(UserCmd):
    """Build StackHut service using docker"""
    name = 'stackbuild'
    visible = False

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(StackBuildCmd, StackBuildCmd).parse_cmds(subparser, StackBuildCmd.name,
                                                                   '',
                                                                   StackBuildCmd)
        subparser.add_argument("--outdir", '-o', default='stacks',
                               help="Directory to save stacks to")
        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")
        subparser.add_argument("--no-cache", '-n', action='store_true', help="Disable cache during build")

    def __init__(self, args):
        super().__init__(args)
        self.outdir = args.outdir
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)

    def run(self):
        super().run()

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

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(InitCmd, InitCmd).parse_cmds(subparser, InitCmd.name,
            "Initialise a new StackHut service", InitCmd)
        subparser.add_argument("baseos", help="Base Operating System", choices=bases.keys())
        subparser.add_argument("stack", help="Language stack to support", choices=stacks.keys())
        subparser.add_argument("--no-git", '-n', action='store_true', help="Disable creating a git repo")

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

        if os.path.exists('.git') or os.path.exists('Hutfile'):
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
            dir_path = utils.get_res_path(os.path.join('scaffold', name))
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

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, HutBuildCmd.name,
                                                               "Build a StackHut service", HutBuildCmd)
        subparser.add_argument("--full", '-l', action='store_true', help="Run a full build")
        subparser.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")

    def __init__(self, args):
        super().__init__(args)
        self.no_cache = self.args.full if 'full' in self.args else False
        self.force = self.args.force if 'force' in self.args else False

    # TODO - run clean cmd first
    def run(self):
        super().run()
        self.usercfg.assert_user_is_author(self.hutcfg)

        # Docker builder
        service = Service(self.hutcfg, self.usercfg)
        service.build_push(self.force, False, self.no_cache)
        return 0


class ToolkitRunCmd(HutCmd, UserCmd):
    """"Concrete Run Command within a container"""
    name = 'run'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(ToolkitRunCmd, ToolkitRunCmd).parse_cmds(subparser,
                                                                   ToolkitRunCmd.name,
                                                                   "Run StackHut service in a container",
                                                                   ToolkitRunCmd)
        subparser.add_argument("reqfile", nargs='?', default='test_request.json',
                               help="Test request file to use")
        subparser.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")

    def __init__(self, args):
        super().__init__(args)
        self.reqfile = args.reqfile
        self.force = args.force

    def run(self):
        super().run()
        self.usercfg.assert_user_is_author(self.hutcfg)

        # Docker builder (if needed)
        service = Service(self.hutcfg, self.usercfg)
        service.build_push(self.force, False, False)

        host_req_file = os.path.abspath(self.reqfile)

        host_store_dir = os.path.abspath(utils.LocalStore.local_store)
        os.mkdir(host_store_dir) if not os.path.exists(host_store_dir) else None

        uid_gid = '{}:{}'.format(os.getuid(), os.getgid())

        log.info("Running service with {} in container - log below...".format(self.reqfile))
        # call docker to run the same command but in the container
        # use data vols for req and run_output

        # NOTE - SELINUX issues - can remove once Docker 1.7 becomes mainstream
        req_flag = 'z' if utils.OS_TYPE == 'SELINUX' else 'ro'
        res_flag = 'z' if utils.OS_TYPE == 'SELINUX' else 'rw'
        verbose_mode = '-v' if self.args.verbose else None

        args = ['-v', '{}:/workdir/test_request.json:{}'.format(host_req_file, req_flag),
                '-v', '{}:/workdir/{}:{}'.format(host_store_dir, utils.LocalStore.local_store, res_flag),
                '--entrypoint=/usr/bin/stackhut', service.docker_fullname, verbose_mode, 'runcontainer', '--uid', uid_gid]
        args = [x for x in args if x is not None]

        out = sh.docker.run(args, _out=lambda x: print(x, end=''))
        log.info("...finished service in container")
        return 0


class DeployCmd(HutCmd, UserCmd):
    name = 'deploy'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(DeployCmd, DeployCmd).parse_cmds(subparser, DeployCmd.name,
                                                           "deploy service to StackHut", DeployCmd)
        subparser.add_argument("--no-build", '-n', action='store_true', help="Deploy without re-building & pushing the image")
        subparser.add_argument("--force", '-f', action='store_true', help="Force rebuild of image")

    def __init__(self, args):
        super().__init__(args)
        self.no_build = args.no_build
        self.force = args.force

    def create_methods(self):
        with open(utils.CONTRACTFILE, 'r') as f:
            contract = json.load(f)

        # remove the common.barrister element
        interfaces = [x for x in contract if 'barrister_version' not in x]

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
        self.usercfg.assert_user_is_author(self.hutcfg)

        service = Service(self.hutcfg, self.usercfg)

        # call build+push first using Docker builder
        if not self.no_build:
            service.build_push(self.force, True, False)

        # run the contract regardless
        service.gen_barrister_contract()

        # build up the deploy message body
        test_request = json.loads(self._read_file('test_request.json'))
        readme = self._read_file('README.md')

        data = {
            'service': service.fullname,  # StackHut Service,
            'docker_service': self.hutcfg.docker_fullname(self.usercfg),  # Docker service name
            'github_url': self.hutcfg.github_url,
            'example_request': test_request,
            'description': self.hutcfg.description,
            'readme': readme,
            'schema': self.create_methods()
        }

        log.info("Deploying image '{}' to StackHut".format(service.fullname))
        r = utils.stackhut_api_user_call('add', data, self.usercfg)
        log.info("Service {} has been {}".format(service.fullname, r['message']))
        return 0


# StackHut primary toolkit commands
# debug, push, pull, test, etc.
COMMANDS = [
    # visible
    LoginCmd, LogoutCmd, InfoCmd,
    InitCmd,
    HutBuildCmd, ToolkitRunCmd, DeployCmd,
    # hidden
    StackBuildCmd,
]
