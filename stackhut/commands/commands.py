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
import os
import shutil
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
        with open(utils.HUTFILE, 'r') as f:
            self.hutfile = yaml.safe_load(f)

# Base command implementing common func
class AdminCmd(BaseCmd):
    def __init__(self, args):
        super().__init__(args)


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
        service = Service(self.hutfile)
        service.build(self.args.push, self.args.no_cache)

        log.info("{} build complete".format(service.name))


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

        name = self.hutfile['name'].lower()
        author = self.hutfile['author'].lower()
        version = 'latest'
        tag = "{}/{}:{}".format(author, name, version)
        infile = os.path.abspath(self.infile)

        log.info("Running test service with {}".format(self.infile))
        out = sh.docker.run('-v', '{}:/workdir/example_request.json:ro'.format(infile),
                            '--entrypoint=/usr/bin/stackhut', tag, '-vv', 'runlocal', _out=lambda x: print(x, end=''))
        log.info("Finished test service")
