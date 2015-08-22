#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
test_stackhut
----------------------------------

Tests for `stackhut` module.
"""

import unittest
import os
import time
import shutil

import sh

from stackhut_common import config
from stackhut_common.runtime import rpc
from stackhut_toolkit.builder import get_docker, bases, stacks
from stackhut_toolkit import client


def copy_config(suffix):
    src = os.path.expanduser(os.path.join('~', '.stackhut.cfg.{}'.format(suffix)))
    dest = os.path.expanduser(os.path.join('~', '.stackhut.cfg'))
    shutil.copy(src, dest)



class SHToolkitTest(unittest.TestCase):
    # def __init__(self):
    #     super().__init__()
    #     self.out = None

    def run_toolkit(self, subcmd, _args=None, server=None, verbose=False, **kwargs):
        def do_args(args):
            a = (x[1] if (type(x) is tuple) and x[0] else x for x in args)
            b = (x for x in a if x and type(x) is not tuple)
            return list(b)

        _args = _args if _args else []
        args = do_args(['-v', (server, '-s'), (server, server), subcmd] + _args)
        print(kwargs)
        if verbose:
            self.out = sh.stackhut(args, _out=lambda x: print(x.strip()), **kwargs)
        else:
            self.out = sh.stackhut(args, **kwargs)


        self.assertEqual(0, self.out.exit_code)

        return self.out

    def assertInStdout(self, substring, msg=None):
        self.assertIn(substring, self.out.stdout.decode(), msg)


    # asserts taken from https://github.com/iLoveTux/CLITest
    def assertFileExists(self, filename, msg=None):
        """Return True if filename exists and is a file, otherwise raise an
        AssertionError with msg"""
        if msg is None:
            msg = "An assertion Failed, file '{}' ".format(filename)
            msg += "does not exist or is not a file."
        if not (os.path.exists(filename)) or not (os.path.isfile(filename)):
            raise AssertionError(msg)
        return True

    def assertFileNotExists(self, filename, msg=None):
        """Return True if filename does not exist or is not a file,
        otherwise raise an AssertionError with msg"""
        if msg is None:
            msg = "An assertion Failed, file '{}' exists.".format(filename)
        if os.path.exists(filename) and os.path.isfile(filename):
            raise AssertionError(msg)
        return True

    def assertDirectoryExists(self, path, msg=None):
        """Return True if path exists and is a directory, otherwise
        raise an AssertionError with msg"""
        if msg is None:
            msg = "An assertion Failed, directory '{}' ".format(path)
            msg += "does not exist or is not a directory."
        if not (os.path.exists(path)) or not (os.path.isdir(path)):
            raise AssertionError(msg)
        return True

    def assertDirectoryNotExists(self, path, msg=None):
        """Return True if path does not exist or is not a directory,
        otherwise raise an AssertionError with msg"""
        if msg is None:
            msg = "An assertion Failed, directory '{}' exists.".format(path)
        if os.path.exists(path) and os.path.isdir(path):
            raise AssertionError(msg)
        return True



class TestToolkit1User(SHToolkitTest):
    backup_file = config.UserCfg.config_fpath + '.bak'

    @classmethod
    def setUpClass(cls):
        copy_config('mands')

    @unittest.skip('disabled for now')
    def test_1_login(self):
        self.run_toolkit('login', verbose=True)

        usercfg = config.UserCfg()
        self.assertIn('username', usercfg)
        self.assertIn('hash', usercfg)

    def test_2_info(self):
        out = self.run_toolkit('info')
        self.assertInStdout('username', 'User logged in')

    @unittest.skip('disabled for now')
    def test_3_logout(self):
        self.run_toolkit('logout')
        usercfg = config.UserCfg()
        self.assertNotIn('username', usercfg)
        self.assertNotIn('hash', usercfg)

    @classmethod
    def tearDownClass(cls):
        pass

class TestToolkit2StackBuild(SHToolkitTest):
    def setUp(self):
        self.docker = get_docker()
        copy_config('stackhut')

    def check_image(self, image_name, dirs):
        """check docker build dir and docker image exists"""
        images = self.docker.client.images("{}/{}".format('stackhut', image_name))
        self.assertGreater(len(images), 0)
        self.assertIn(image_name, dirs)

    def test_stackbuild(self):
        out = self.run_toolkit('stackbuild', ['--outdir', 'test-stackbuild'], verbose=True)
        os.chdir('test-stackbuild')
        dirs = {d for d in os.listdir('.') if os.path.isdir(d)}

        # check docker build dir and docker image exists
        [self.check_image(b.name, dirs) for b in bases.values()]
        [self.check_image("{}-{}".format(b.name, s.name), dirs)
         for b in bases.values()
         for s in stacks.values()]

    def tearDown(self):
        os.chdir('..')
        shutil.rmtree('test-stackbuild', ignore_errors=False)

class TestToolkit3Service(SHToolkitTest):
    repo_name = 'registry.stackhut.com:5000/mands/test-service'
    image_name = '{}:latest'.format(repo_name)

    @classmethod
    def setUpClass(cls):
        copy_config('mands')
        os.mkdir('test-service')
        os.chdir('test-service')

        cls.docker_client = get_docker().client

        # delete any image if exists
        try:
            cls.docker_client.remove_image(cls.image_name, force=True)
        except:
            pass

    def test_1_init(self):
        out = self.run_toolkit('init', ['debian', 'python'], verbose=True)
        # check files copied across
        files = ['Hutfile', 'api.idl', 'README.md', 'app.py']
        [self.assertTrue(os.path.exists(f)) for f in files]

    def test_2_build(self):
        out = self.run_toolkit('build', ['--force', '--full', '--dev'], verbose=True)
        # check image exists
        images = self.docker_client.images(self.repo_name)
        self.assertGreater(len(images), 0)

    def test_3_run(self):
        # out = self.run_toolkit('run', verbose=True, _bg=True)
        out = sh.stackhut('-v', 'run', _out=lambda x:print(x.strip()), _bg=True)
        time.sleep(5)

        # use the client lib to send some requests
        sh_client = client.SHService('mands', 'test-service', host='http://localhost:6000')
        # valid request
        res = sh_client.add(1,2)
        self.assertEqual(res, 3)
        # invalid request
        try:
            res = sh_client.sub(1,2)
        except client.SHRPCError as e:
            self.assertEqual(e.code, rpc.ERR_METHOD_NOT_FOUND)
            self.assertIn('sub', e.msg)

        out.process.signal(2)
        out.wait()
        self.assertEqual(0, out.exit_code)

    @unittest.skip('Not ready')
    def test_4_deploy(self):
        out = self.run_toolkit('deploy', ['--local'], verbose=True)

        # test by making a request to live API and checking response
        time.sleep(20)  # is this needed?

        c = client.SHService('mands', 'test-service')
        res = c.add(1,2)
        self.assertEqual(res, 3)

    @classmethod
    def tearDownClass(cls):
        os.chdir('..')
        shutil.rmtree('test-service', ignore_errors=False)
        cls.docker_client.remove_image(cls.image_name, force=True)


if __name__ == '__main__':
    unittest.main()


# tests to run  - commands and high-level func
# login and info
# build base os and stacks
# init project and build, run, (deploy?)
