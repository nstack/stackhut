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

# TODO - small commands go here...
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
from jinja2 import Environment, FileSystemLoader

from stackhut import utils
from stackhut.utils import log
from .primitives import Service, BaseOS, Stack, bases, stacks, is_stack_supported, run_barrister

# Base command implementing common func
class BaseCmd:
    """The Base Command"""
    @staticmethod
    def parse_cmds(subparsers, cmd_name, description, cls):
        sp = subparsers.add_parser(cmd_name, help=description, description=description)
        sp.set_defaults(func=cls)
        return sp

    def __init__(self, args):
        self.args = args

    @abc.abstractmethod
    def run(self):
        """Main entry point for a command with parsed cmd args"""
        pass

class HutCmd(BaseCmd):
    """Hut Commands are run from a Hut stack dir requiring a Hutfile"""
    def __init__(self, args):
        super().__init__(args)
        # import the hutfile
        self.hutcfg = utils.HutfileCfg()

# Base command implementing common func
class AdminCmd(BaseCmd):
    def __init__(self, args):
        super().__init__(args)
        self.usercfg = utils.StackHutCfg()


class InitCmd(AdminCmd):
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(InitCmd, InitCmd).parse_cmds(subparser, 'init',
            "Initialise a new StackHut service - we recommend alpine python", InitCmd)
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
        if 'username' in self.usercfg and len(self.usercfg['username']) > 0:
            self.author = (self.usercfg['username'].split('@')[0]).capitalize()
        else:
            log.error("Please login first")
            return 1

        if is_stack_supported(self.baseos, self.stack):
            self.service_name = os.path.basename(os.getcwd())
            log.info("Creating service {}".format(self.service_name))
            # copy the scaffold into the service
            shutil.copytree(utils.get_res_path('scaffold'), '.')

            # rename scaffold file to entrypoint and remove others
            os.rename(self.stack.scaffold_name, self.stack.entrypoint)
            [os.remove(f) for f in os.listdir(".") if f.startswith("scaffold-")]

            # run the templates
            template_env = Environment(loader=FileSystemLoader('.'))
            [self.render_file(template_env, f, dict(scaffold=self))
                for f in os.listdir('.') if os.path.isfile(f)]

            # add the package file if present?
            open(self.stack.package_file, 'w').close()

            # git commit
            if not self.args.no_git:
                sh.git.init()
                sh.git.add(".")
                sh.git.commit(m="Initial commit")
                sh.git.branch("stackhut")

        else:
            print("Sorry that combination is not supported")
            return 1


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


class HutBuildCmd(HutCmd, AdminCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, 'build',
                                                               "Build a StackHut service", HutBuildCmd)
#        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")
        subparser.add_argument("--no-cache", '-n', action='store_true', help="Disable cache during build")

    def __init__(self, args):
        super().__init__(args)

    # TODO - run clean cmd first
    def run(self, push=False):
        super().run()
        # setup
        run_barrister()
        # Docker build
        service = Service(self.hutcfg, self.usercfg)
        service.build(push, self.args.no_cache)
        log.info("{} build complete".format(self.hutcfg.name))


# Base command implementing common func
class LoginCmd(AdminCmd):
    def __init__(self, args):
        super().__init__(args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(LoginCmd, LoginCmd).parse_cmds(subparser, 'login',
                                                         "login to stackhut", LoginCmd)

    def run(self):
        super().run()

        username = input("Username: ")
        password = getpass.getpass("Password: ")

        # connect to Stackhut service to get token
        if True:
            self.usercfg['username'] = username
            self.usercfg['password'] = password
            # cfg['token'] = token
            self.usercfg.save()
        else:
            print("Incorrect username or password, please try again")


# Base command implementing common func
class LogoutCmd(AdminCmd):
    def __init__(self, args):
        super().__init__(args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(LogoutCmd, LogoutCmd).parse_cmds(subparser, 'logout',
                                                           "logout to stackhut", LogoutCmd)

    def run(self):
        super().run()
        # connect to Stackhut service to get token?
        print("Logged out {}".format(self.usercfg['username']))
        self.usercfg.wipe()
        self.usercfg.save()


# Base command implementing common func
# dockerImage: String, userName : String,
# password : String,
# methods : JsValue,
# githubUrl : Option[String],
# exampleRequest : Option[JsValue],
# description : String)
class DeployCmd(HutCmd, AdminCmd):
    def __init__(self, args):
        super().__init__(args)
        self.hutbuild = HutBuildCmd(args)

    @staticmethod
    def parse_cmds(subparser):
        subparser = super(DeployCmd, DeployCmd).parse_cmds(subparser, 'deploy',
                                                           "deploy service to StackHut", DeployCmd)

    def create_methods(self):
        with open(utils.CONTRACTFILE, 'r') as f:
            contract = json.load(f)

        # remove the barrister element
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

    def run(self):
        super().run()

        # call build+push first
        self.hutbuild.run(True)

        # build up the deploy message body
        example_request = None
        if os.path.exists('test_request.json'):
            with open('test_request.json') as f:
                example_request = json.load(f)

        # if self.usercfg['username'] != self.hutcfg.email:
        #     log.error("StackHut username ({}) not equal to Hutfile contact email ({})".format(self.usercfg['username'], self.hutcfg.email))
        #     return 1

        data = {
            'dockerImage': self.hutcfg.tag,
            'githubUrl': self.hutcfg.github_url,
            'exampleRequest': example_request,
            'description': self.hutcfg.description,
            'schema': self.create_methods()
        }

        log.info("Deploying image {} to StackHut".format(self.hutcfg.tag))
        r = utils.stackhut_api_secure_call('add', data, self.usercfg)
        log.info("Image {} has been {}".format(r['serviceName'], r['message']))

