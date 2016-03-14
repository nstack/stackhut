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
import json
import os
import time
from threading import Thread

import sh
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import Terminal256Formatter
from prompt_toolkit import prompt

from .common import utils
from .common.utils import log
from .common.runtime import rpc
from .common.runtime.backends import LocalBackend
from .common.runtime.runner import ServiceRunner
from .common.commands import HutCmd
from .common.exceptions import ConfigError
from .toolkit_utils import *
from .builder import Service, stacks, get_docker, OS_TYPE
from .commands import UserCmd


class TestRunner:
    def __init__(self, port):
        # set server url
        utils.SERVER_URL = "http://localhost:{}/".format(port)

    def call_service(self, msg):
        r = stackhut_api_call('run', msg)
        result = highlight(json.dumps(r, indent=4), JsonLexer(), Terminal256Formatter())
        log.info("Service {} returned - \n{}".format(utils.SERVER_URL, result))

    def test_file(self, fname):
        with open(fname, "r") as f:
            msg = json.load(f)
            self.call_service(msg)

    def test_interactive(self, service_name):
            # get the contract
            contract = rpc.load_contract_file()
            interfaces = contract.interfaces
            log.info("Service has {} interface(s) - {}".format(len(interfaces), list(interfaces.keys())))

            for i in contract.interfaces.values():
                log.info("Interface '{}' has {} function(s):".
                         format(i.name, len(i.functions)))
                for f in i.functions.values():
                    log.info("\t{}".format(rpc.render_signature(f)))

            while True:
                (iface, fname) = prompt('Enter Interface.Function to test: ').split('.')
                f = contract.interface(iface).function(fname)

                values = [prompt('Enter "{}" value for {}: '.format(p.type, p.name))
                          for p in f.params]
                eval_values = [json.loads(x) for x in values]

                if utils.VERBOSE:
                    pp_values = highlight(json.dumps(eval_values, indent=4), JsonLexer(), Terminal256Formatter())
                    log.debug("Calling {} with {}".format(f.full_name, pp_values))

                msg = {
                    "service": service_name,
                    "request": {
                        "method": f.full_name,
                        "params": eval_values
                    }
                }

                self.call_service(msg)


class TestRequestCmd(HutCmd, UserCmd):
    """Concrete Run Command using Local system for dev on Host OS"""
    name = 'test'
    description = "Construct a test request to a running local/hosted service"

    @staticmethod
    def register(sp):
        sp.add_argument("port", nargs='?', default='4001', help="Port to host API on locally", type=int)
        sp.add_argument("--file", '-f', metavar='FILE', help="File containing sample json request (e.g. test_request.json")
        sp.add_argument("--interactive", '-i', action='store_true', help="Run interactive requests to service")

    def __init__(self, args):
        super().__init__(args)
        self.port = args.port
        self.fname = args.file
        self.interactive = args.interactive

    def run(self):
        tester = TestRunner(self.port)
        if self.fname is not None:
            tester.test_file(self.fname)
        elif self.interactive:
            tester.test_interactive(self.hutcfg.service_short_name(self.usercfg.username))
        else:
            raise AssertionError("Must run with either --file or --interactive flag")
        return 0



class RunService:
    def __init__(self, port, args, username, service_full_name):
        import random

        host_store_dir = os.path.abspath(LocalBackend.local_store)
        os.mkdir(host_store_dir) if not os.path.exists(host_store_dir) else None

        # Get port from kernel
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.bind(('', 0))
        # addr = s.getsockname()

        # call docker to run the same command but in the container
        # use data vols for response output files
        self.name = 'stackhut-{}'.format(random.randrange(10000))
        # NOTE - SELINUX issues - can remove once Docker 1.7 becomes mainstream
        res_flag = 'z' if OS_TYPE == 'SELINUX' else 'rw'
        verbose_mode = '-v' if args.verbose else None
        uid_gid = '{}:{}'.format(os.getuid(), os.getgid())
        args = [
                'run',
                '-p', '{}:4001'.format(port),
                '-v', '{}:/workdir/{}:{}'.format(host_store_dir, LocalBackend.local_store, res_flag),
                '--rm=true', '--name={}'.format(self.name),
                '--privileged' if args.privileged else None,
                '--entrypoint=/usr/bin/env', service_full_name, 'stackhut-runner', verbose_mode,
                'runcontainer', '--uid', uid_gid, '--author', username
                ]
        # filter out None args
        self.args = [x for x in args if x is not None]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        docker = get_docker()
        docker.run_docker_sh('stop', ['-t', '5', self.name])
        log.info("**** END SERVICE LOG ****")

    def start(self):
        log.info("**** START SERVICE LOG ****")
        docker_cmd = sh.Command("docker")
        self.p = docker_cmd(self.args, _bg=True, _out=lambda x: log.debug("Runner - {}".format(x.rstrip())),
                            _err=lambda x: log.error("Runner - {}".format(x.rstrip())))



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
        sp.add_argument("--clone", '-c', metavar='URL', help="Clone a remote service at URL and run locally")
        # testing
        sp.add_argument("--test", '-t', action='store_true', help="Run service with testing")
        sp.add_argument("--file", metavar='FILE', help="File containing sample json request (e.g. test_request.json")
        sp.add_argument("--interactive", '-i', action='store_true', help="Run interactive requests to service")

    def __init__(self, args):
        # self.reqfile = args.reqfile
        self.port = args.port
        self.force = args.force
        self.privileged = args.privileged
        self.clone = args.clone
        self.test = args.test

        # if clone, clone first
        if self.clone:
            from posixpath import basename
            from urllib.parse import urlparse
            dir = basename(urlparse(self.clone).path)

            try:
                sh.git.clone(self.clone)
            except sh.ErrorReturnCode_128:
                raise RuntimeError("Service '{}' already exists, can't clone".format(dir))

            log.debug("Cloned service from {} into {}".format(self.clone, dir))
            # update root dir
            utils.change_root_dir(dir)

        self.dir = utils.ROOT_DIR
        super().__init__(args)

    def sigterm_handler(self, signo, frame):
        log.debug("Got shutdown signal".format(signo))
        raise KeyboardInterrupt

    def run(self):
        from posixpath import basename
        import signal

        super().run()

        # Docker builder (if needed)
        service = Service(self.hutcfg, self.usercfg.username)
        service.build_push(force=self.force)

        docker = get_docker()
        log.info("Running service '{}' on http://{}:{}".
                 format(self.hutcfg.service_short_name(self.usercfg.username), docker.ip, self.port))
        log.info("Test by running 'curl -H \"Content-Type: application/json\" -X POST -d @test_request.json "
                 "http://{}:{}/run' from the '{}' dir".format(docker.ip, self.port, basename(utils.ROOT_DIR)))

        # setup shutdown handlers - needed for freeze?
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)

        try:
            with RunService(self.port, self.args, self.usercfg.username, service.full_name) as sh_service:
                sh_service.start()
                if self.test:
                    time.sleep(2)
                    TestRequestCmd(self.args).run()
                else:
                    log.debug("Waiting for sh_service")
                    sh_service.p.wait()

        except KeyboardInterrupt:
            log.debug("Shutting down service container, press again to force-quit...")

        log.info("Run completed successfully")
        return 0


class RunCmd(RunContainerCmd):
    """"Alias for runcontainer"""
    name = 'run'


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
        rpc.generate_contract_file()

        try:
            backend = LocalBackend(self.hutcfg, self.usercfg.username, port=self.port)
            with ServiceRunner(backend, self.hutcfg) as runner:
                log.info("Running service '{}' on http://127.0.0.1:{}".format(backend.service_short_name, self.port))
                runner.run()
        # surface errors caused by service configuration
        except ConfigError as err:
            log.error('Exception while running service: %s', str(err))
        finally:
            # cleanup project directory before exit
            toolkit_stack.del_shim()
            os.remove(rpc.REQ_FIFO) if os.path.exists(rpc.REQ_FIFO) else None
            os.remove(rpc.RESP_FIFO) if os.path.exists(rpc.RESP_FIFO) else None


COMMANDS = [
    RunContainerCmd, RunCmd, RunHostCmd, TestRequestCmd,
]
