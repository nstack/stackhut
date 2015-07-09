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


class ScaffoldCmd(BaseCmd):
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(ScaffoldCmd, ScaffoldCmd).parse_cmds(subparser, 'scaffold',
            "Configure a new StackHut service - we recommend alpine python", ScaffoldCmd)
        subparser.add_argument("baseos", help="Base Operating System", choices=bases.keys())
        subparser.add_argument("stack", help="Language stack to support", choices=stacks.keys())
        subparser.add_argument("name", help="Service name", type=str)

    def __init__(self, args):
        super().__init__(args)
        self.baseos = bases[args.baseos]
        self.stack = stacks[args.stack]
        self.service_name = args.name

    def render_file(self, env, fname, params):
        rendered_template = env.get_template(fname).render(params)
        with open(fname, 'w') as f:
            f.write(rendered_template)

    def run(self):
        super().run()
        if is_stack_supported(self.baseos, self.stack):
            log.info("Creating service {}".format(self.service_name))
            # checkout the scaffold into the service
            sh.git.clone("git@github.com:StackHut/scaffold-{}.git".format(self.stack.name), self.service_name)
            os.chdir(self.service_name)
            shutil.rmtree(".git")

            # now modify any files as required
            template_env = Environment(loader=FileSystemLoader(utils.get_res_path('.')))
            files = ['Hutfile', 'example_request.json', 'service.idl',
                     self.stack.entrypoint, 'README.md']
            for f in files:
                self.render_file(template_env, f, dict(scaffold=self))
        else:
            print("Sorry that combination is not supported")


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


class HutBuildCmd(HutCmd):
    """Build StackHut service using docker"""
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(HutBuildCmd, HutBuildCmd).parse_cmds(subparser, 'build',
                                                               "Build a StackHut service", HutBuildCmd)
        subparser.add_argument("--push", '-p', action='store_true', help="Push image to public after")
        subparser.add_argument("--no-cache", '-n', action='store_true', help="Disable cache during build")

    def __init__(self, args):
        super().__init__(args)

    # TODO - run clean cmd first
    def run(self):
        super().run()
        # setup
        run_barrister()

        # Docker build
        service = Service(self.hutcfg)
        service.build(self.args.push, self.args.no_cache)

        log.info("{} build complete".format(self.hutcfg.name))


class TestLocalCmd(HutCmd):
    @staticmethod
    def parse_cmds(subparser):
        subparser = super(ScaffoldCmd, ScaffoldCmd).parse_cmds(subparser, 'testlocal',
                            "Test Service inside container using specified input", TestLocalCmd)
        subparser.add_argument("--infile", '-i', default='example_request.json',
                               help="Local file to use for test input")

    def __init__(self, args):
        super().__init__(args)
        self.infile = self.args.infile

    def run(self):
        super().run()
        tag = self.hutcfg.tag
        infile = os.path.abspath(self.infile)

        log.info("Running test service with {}".format(self.infile))
        out = sh.docker.run('-v', '{}:/workdir/example_request.json:ro'.format(infile),
                            '--entrypoint=/usr/bin/stackhut', tag, '-vv', 'runlocal', _out=lambda x: print(x, end=''))
        log.info("Finished test service")


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

        # connect to Stackhut service to get token
        print("Logged out {}".format(self.usercfg['username']))
        # blank out the cfg file
        self.usercfg['username'] = ''
        self.usercfg['token'] = ''
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
            return "{} ({}) {}".format(method['name'], params_t, render_param(method['returns']))

        for i in interfaces:
            for f in i['functions']:
                f['signature'] = render_signature(f)
                log.debug("Signature for {}.{} is \"{}\"".format(i['name'], f['name'], f['signature']))

        return interfaces

    def run(self):
        super().run()

        # build up the deploy message body
        example_request = None
        if os.path.exists('example_request.json'):
            with open('example_request.json') as f:
                example_request = json.load(f)

        if self.usercfg['username'] != self.hutcfg.email:
            log.error("StackHut username ({}) not equal to Hutfile contact email ({})".format(self.usercfg['username'], self.hutcfg.email))
            return 1

        data = {
            'dockerImage': self.hutcfg.name,
            'githubUrl': None,
            'exampleRequest': example_request,
            'desc': self.hutcfg.description,
            'methods': self.create_methods()
        }

        log.info("Deploying image {} to StackHut".format(self.hutcfg.tag))
        utils.stackhut_api_secure_call('add', data, self.usercfg)
        log.info("Image deployed")

