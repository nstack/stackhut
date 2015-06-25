#!/usr/bin/env python3
import logging
import os
import abc
from jinja2 import Environment, FileSystemLoader
from multipledispatch import dispatch

logging.basicConfig(level=logging.DEBUG)

template_dir = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "../res/templates"))
logging.debug("Template dir is {}".format(template_dir))
env = Environment(loader=FileSystemLoader(template_dir))

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
            'rm -rf /tmp/* &&',
        ]
        
    def setup_cmds(self):
        return self.install_os_pkg(self.base_pkgs)


class Alpine(BaseOS):
    name = 'alpine'

    base_pkgs = ['python3', 'ca-certificates']

    def os_pkg_cmd(self, pkgs):
        return 'apk --update add {}'.format(' ' .join(pkgs))

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



bases = [Fedora(), Alpine()]

# Language stacks that we support
class Stack:
    name = ''

class Python(Stack):
    name = 'python'

class NodeJS(Stack):
    name = 'nodejs'

stacks = [Python(), NodeJS()]


def build_base(base):
    logging.info("Building Dockerfile for base {}".format(base.name))
    template = env.get_template('Dockerfile-base.txt')
    rendered_template = template.render(base=base)
    logging.debug(rendered_template)


# Our BaseOS / Stack Dispatchers (e.g. pattern matching)
# we need this as pkds installed per OS are OS dependent
@dispatch(Fedora, Python)
def get_stack_install_cmd(base_os, stack):
    return ''  # installed by default

@dispatch(Alpine, Python)
def get_stack_install_cmd(base_os, stack):
    return ''  # installed by default

@dispatch(Fedora, NodeJS)
def get_stack_install_cmd(base_os, stack):
    return ''  # not supported

@dispatch(Alpine, NodeJS)
def get_stack_install_cmd(base_os, stack):
    pkgs = ['iojs@testing']
    return base_os.install_os_pkg(pkgs)

@dispatch(object, object)
def get_stack_install_cmd(base_os, stack):
    logging.error("Os / Stack combo for {}/{} not implemented".format(base_os.name, stack.name))
    raise NotImplementedError()


def build_stack(base, stack):
    logging.info("Building Dockerfile for base {} with stack {}".format(base.name, stack.name))
    template = env.get_template('Dockerfile-stack.txt')

    stack_install_cmds = get_stack_install_cmd(base, stack)

    rendered_template = template.render(base=base, stack=stack, stack_install_cmds=stack_install_cmds)
    logging.debug(rendered_template)



if __name__ == '__main__':
    #[build_base(b) for b in bases]
    [build_stack(b, s) for b in bases for s in stacks]

