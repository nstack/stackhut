#!/usr/bin/env python3
import logging
import os
import abc
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.DEBUG)

template_dir = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "../res/templates"))
logging.debug("Template dir is {}".format(template_dir))
env = Environment(loader=FileSystemLoader(template_dir))

# Base OS's that we support
class BaseOS:
    image_name = ''

    def get_description(self):
        return "Base OS image using {}".format(self.image_name)

    @abc.abstractmethod
    def get_cmds(self):
        pass

class Fedora(BaseOS):
    image_name = 'fedora'

    def __init__(self):
        pass

    def get_cmds(self):
        cmds = [
            'dnf -y install python3 python3-pip',
            #'pip3 install --no-cache-dir --compile boto sh requests markdown',
            'dnf -y autoremove',
            'dnf -y clean all',
            'rm -rf /usr/share/locale/*',
            'rm -rf /usr/share/doc/*',
            'journalctl --vacuum-size=0',
            'rm -rf /var/log/* || true',
            'rm -rf /var/cache/*',
            'rm -rf /tmp/* &&',
        ]

        return cmds


class Alpine(BaseOS):
    image_name = 'alpine'

    def get_cmds(self):
        cmds = [
            'echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories',
            'echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories',
            'apk --update add python3 ca-certificates',
            #'pip3 install --no-cache-dir --compile boto sh PyYaml requests markdown redis'
            'rm -rf /usr/share/locale/*',
            'rm -rf /usr/share/doc/*',
            'rm -rf /var/log/* || true',
            'rm -rf /var/cache/*',
            'rm -rf /tmp/*',
            'mkdir /var/cache/apk',
        ]

        return cmds

bases = [Fedora(), Alpine()]

# Language stacks that we support
class Stack:
    stack_name = ''

class Python(Stack):
    stack_name = 'python'

    def get_cmds =
        cmds = []


        return cmds



class NodeJS(Stack):
    stack_name = 'nodejs'

stacks = [Python(), NodeJS()]


def build_base(base):
    logging.info("Building Dockerfile for base {}".format(base.image_name))

    template = env.get_template('Dockerfile-base.txt')
    rendered_template = template.render(base=base)
    logging.debug(rendered_template)

def build_stack(base, stack):
    logging.info("Building Dockerfile for base {} with stack {}".format(base.image_name, stack.name))




if __name__ == '__main__':
    [build_base(b) for b in bases]
    [build_stack(b, s) for b in bases for s in stacks]


