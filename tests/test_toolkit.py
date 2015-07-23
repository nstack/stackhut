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

import stackhut
from stackhut.toolkit import commands
from stackhut.common import utils, primitives
from stackhut.common.primitives import bases, stacks, get_docker
import argparse
import json

# utils.DEBUG = 'localhost:8080' # None # args.debug
utils.set_log_level(2)

def create_args(d):
    args = argparse.Namespace()
    args.__dict__.update(d)
    return args


class TestToolkit1User(unittest.TestCase):
    backup_file = utils.CFGFILE + '.bak'

    @classmethod
    def setUpClass(cls):
        if os.path.exists(utils.CFGFILE):
            shutil.copy(utils.CFGFILE, cls.backup_file)

    def test_version(self):
        print("Toolkit version {}".format(stackhut.__version__))
        self.assertEqual(stackhut.__version__, stackhut.__version__)

    @unittest.skipIf(utils.DEBUG is None, 'Not running on debug server')
    def test_1_login(self):
        args = create_args(dict())
        cmd = commands.LoginCmd(args)
        self.assertEqual(0, cmd.run())

        usercfg = utils.UserCfg()
        self.assertIn('username', usercfg)
        self.assertIn('hash', usercfg)

    def test_2_info(self):
        args = create_args(dict())
        cmd = commands.InfoCmd(args)
        self.assertEqual(0, cmd.run())

    def test_3_logout(self):
        args = create_args(dict())
        cmd = commands.LogoutCmd(args)
        self.assertEqual(0, cmd.run())

        usercfg = utils.UserCfg()
        self.assertNotIn('username', usercfg)
        self.assertNotIn('hash', usercfg)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.backup_file):
            shutil.copy(cls.backup_file, utils.CFGFILE)


class TestToolkit2StackBuild(unittest.TestCase):

    def setUp(self):
        self.docker = get_docker()

    def check_image(self, image_name, dirs):
        """check docker build dir and docker image exists"""
        images = self.docker.images("{}/{}".format('stackhut', image_name))
        self.assertGreater(len(images), 0)
        self.assertIn(image_name, dirs)

    def test_stackbuild(self):
        args = create_args(dict(outdir='test-stackbuild', push=False, no_cache=False))
        cmd = commands.StackBuildCmd(args)
        self.assertEqual(0, cmd.run())

        os.chdir('test-stackbuild')
        dirs = {d for d in os.listdir() if os.path.isdir(d)}

        # check docker build dir and docker image exists
        [self.check_image(b.name, dirs) for b in primitives.bases.values()]
        [self.check_image("{}-{}".format(b.name, s.name), dirs)
         for b in bases.values()
         for s in stacks.values()]

    def tearDown(self):
        os.chdir('..')
        shutil.rmtree('test-stackbuild', ignore_errors=False)


class TestToolkit3Service(unittest.TestCase):
    image_name = 'mands/test-service:latest'
    repo_name = image_name.split(':')[0]

    @classmethod
    def setUpClass(cls):
        os.mkdir('test-service')
        os.chdir('test-service')

        cls.docker = get_docker()

        # delete any image if exists
        try:
            cls.docker.remove_image(cls.image_name, force=True)
        except Exception as e:
            pass

    # def test_service(self):
    #     self.test_1_init()
    #     self.test_2_build()
    #     self.test_3_run()
    #     # self.test_4_deploy()

    def test_1_init(self):
        args = create_args(dict(baseos='alpine', stack='python', no_git=False))
        cmd = commands.InitCmd(args)
        self.assertEqual(0, cmd.run())

        # check files copied across
        files = ['Hutfile', 'api.idl', 'README.md']
        [self.assertTrue(os.path.exists(f)) for f in files]

    def test_2_build(self):
        args = create_args(dict(no_cache=False, force=True))
        cmd = commands.HutBuildCmd(args)
        self.assertEqual(0, cmd.run())

        # check image exists
        images = self.docker.images(self.repo_name)
        self.assertGreater(len(images), 0)

    def assert_response(self, resp):
        self.assertIn('id', resp)
        self.assertIn('jsonrpc', resp)
        self.assertIn('result', resp)
        self.assertNotIn('error', resp)
        self.assertEqual(3, resp['result'])

    def test_3_run(self):
        args = create_args(dict(reqfile='test_request.json', force=False, verbose=True))
        cmd = commands.ToolkitRunCmd(args)
        self.assertEqual(0, cmd.run())

        # test by reading the response
        with open('run_result/response.json') as f:
            resp = json.load(f)
        self.assert_response(resp)

    @unittest.skipIf(utils.DEBUG is None, 'Not running on debug server')
    def test_4_deploy(self):
        args = create_args(dict(no_build=False, force=False))
        cmd = commands.ToolkitRunCmd(args)
        self.assertEqual(0, cmd.run())

        # test by making a request to live API and checking response
        time.sleep(20)  # is this needed?

        with open('test_request.json') as f:
            req = json.load(f)
        # make the request
        resp = utils.stackhut_api_call('run', req)
        self.assert_response(resp)

    @classmethod
    def tearDownClass(cls):
        os.chdir('..')
        shutil.rmtree('test-service', ignore_errors=False)
        cls.docker.remove_image(cls.image_name, force=True)


if __name__ == '__main__':
    unittest.main()


# tests to run  - commands and high-level func
# login and info
# build base os and stacks
# init project and build, run, (deploy?)
