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
import abc
import yaml
import json
import os
import shutil
import getpass
import uuid
import sh
import argparse
from jinja2 import Environment, FileSystemLoader
from distutils.dir_util import copy_tree

from stackhut.common import utils
from stackhut.common.utils import log, BaseCmd, HutCmd
from stackhut.common.primitives import Service, bases, stacks, is_stack_supported, gen_barrister_contract


# Base command implementing common func
class UserCmd(BaseCmd):
    """Admin commands require the userconfig file"""
    def __init__(self, args):
        super().__init__(args)
        self.usercfg = utils.StackHutCfg()


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
        # if 'username' in self.usercfg and len(self.usercfg['username']) > 0:
        #     # self.author = (self.usercfg['username'].split('@')[0]).capitalize()
        #     pass
        # else:
        #     log.error("Please login first")
        #     return 1

        if os.path.exists('.git'):
            log.error('Found existing git repo, not initialising')
            return 1

        if is_stack_supported(self.baseos, self.stack):
            self.service_name = os.path.basename(os.getcwd())
            log.info("Creating service {}".format(self.service_name))
            # copy the scaffold into the service
            copy_tree(utils.get_res_path('scaffold'), '.')

            # rename scaffold file to entrypoint and remove others
            os.rename(self.stack.scaffold_name, self.stack.entrypoint)
            [os.remove(f) for f in os.listdir(".") if f.startswith("scaffold-")]

            # run the templates
            template_env = Environment(loader=FileSystemLoader('.'))
            [self.render_file(template_env, f, dict(scaffold=self))
                for f in os.listdir('.') if os.path.isfile(f)]

            # add the package file if present?
            open(self.stack.package_file, 'w').close()

            # add the .stackhut dir
            os.mkdir('.stackhut')

            # git commit
            if not self.args.no_git:
                sh.git.init()
                sh.git.add(".")
                sh.git.commit(m="Initial commit")
                sh.git.branch("stackhut")

        else:
            log.info("Sorry the combination of {} and {} is not supported".format(self.baseos,
                                                                                  self.stack))
            return 1


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
        # build bases and stacks
        [b.build(self.outdir, self.args.push, self.args.no_cache) for b in bases.values()]
        [s.build(b, self.outdir, self.args.push, self.args.no_cache)
            for b in bases.values()
            for s in stacks.values()]
        log.info("All base OS and Stack images built and deployed")


class HutBuildCmd(HutCmd, UserCmd):
    """Build StackHut service using docker"""
    name = 'build'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, HutBuildCmd.name,
                                                               "Build a StackHut service", HutBuildCmd)
        subparser.add_argument("--no-cache", '-n', action='store_true', help="Disable cache during build")

    def __init__(self, args):
        super().__init__(args)

    # TODO - run clean cmd first
    def run(self, push=False):
        super().run()
        # setup
        gen_barrister_contract()
        # Docker build
        service = Service(self.hutcfg, self.usercfg)
        no_cache = self.args.no_cache if 'no_cache' in self.args else False
        service.build(push, no_cache)
        log.info("{} build complete".format(self.hutcfg.name))


# Base command implementing common func
class LoginCmd(UserCmd):
    name = 'login'

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(LoginCmd, LoginCmd).parse_cmds(subparser, LoginCmd.name,
                                                         "login to stackhut", LoginCmd)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        super().run()

        # get docker username
        stdout = sh.docker('info')
        docker_user_list = [x for x in stdout if x.startswith('Username')]
        if len(docker_user_list) == 1:
            docker_username = docker_user_list[0].split(':')[1].strip()
            log.info("Docker user is '{}'".format(docker_username))
        else:
            log.error("Please run 'docker login' first")
            return 1

        username = input("Username: ")
        # email = input("Email: ")
        password = getpass.getpass("Password: ")

        # connect securely to Stackhut service to get token
        r = utils.stackhut_api_call('login', dict(userName=username, password=password))

        if r['success']:
            self.usercfg['docker_username'] = docker_username
            self.usercfg['username'] = username
            self.usercfg['token'] = r['token']
            # self.usercfg['email'] = email
            # cfg['token'] = token

            self.usercfg.save()
            log.info("User {} logged in successfully".format(username))

        else:
            print("Incorrect username or password, please try again")


# Base command implementing common func
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
        # connect to Stackhut service to get token?
        print("Logged out {}".format(self.usercfg.get('email', '')))
        self.usercfg.wipe()
        self.usercfg.save()


# Base command implementing common func
# dockerImage: String, userName : String,
# password : String,
# methods : JsValue,
# githubUrl : Option[String],
# exampleRequest : Option[JsValue],
# description : String)
class DeployCmd(HutCmd, UserCmd):
    name = 'deploy'
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(DeployCmd, DeployCmd).parse_cmds(subparser, DeployCmd.name,
                                                           "deploy service to StackHut", DeployCmd)
        subparser.add_argument("--no-build", '-n', action='store_true', help="Deploy without re-building & pushing the image")

    def __init__(self, args):
        super().__init__(args)
        self.hutbuild = HutBuildCmd(args)
        self.no_build = args.no_build

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

        # call build+push first
        if not self.no_build:
            self.hutbuild.run(True)

        # build up the deploy message body
        test_request = json.loads(self._read_file('test_request.json'))
        readme = self._read_file('README.md')

        # if self.usercfg['username'] != self.hutcfg.email:
        #     log.error("StackHut username ({}) not equal to Hutfile contact email ({})".format(self.usercfg['username'], self.hutcfg.email))
        #     return 1
        tag = self.hutcfg.tag(self.usercfg)

        data = {
            'dockerImage': tag,
            'githubUrl': self.hutcfg.github_url,
            'exampleRequest': test_request,
            'description': self.hutcfg.description,
            #'readme': readme,
            'schema': self.create_methods()
        }

        log.info("Deploying image '{}' to StackHut".format(tag))
        r = utils.stackhut_api_user_call('add', data, self.usercfg)
        log.info("Image {} has been {}".format(r['serviceName'], r['message']))


# StackHut primary toolkit commands
COMMANDS = [
    InitCmd,
    LoginCmd, LogoutCmd,
    HutBuildCmd, DeployCmd,
    # debug, push, pull, test, etc.
    # internal
    StackBuildCmd,
]
