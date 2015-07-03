#!/usr/bin/env python2
# -*- coding: utf-8 -*-
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
Demo StackHut service
"""
from __future__ import (unicode_literals, print_function, division, absolute_import)
from future import standard_library
standard_library.install_aliases()
from builtins import *
from app import SERVICES
import json

def gen_error(code, msg=''):
    return dict(error=code, msg=msg)

def run(req):
    iface_name, func_name = req['method'].split('.')
    params = req['params']

    if iface_name in SERVICES:
        iface_impl = SERVICES[iface_name]
        try:
            func = getattr(iface_impl, func_name)
        except AttributeError:
            return gen_error(-32601)
        # if hasattr(iface_impl, "barrister_pre"):
        #     pre_hook = getattr(iface_impl, "barrister_pre")
        #     pre_hook(context, params)
        if params:
            result = func(*params)
        else:
            result = func()
        return dict(result=result)
    else:
        return gen_error(-32601)

if __name__ == "__main__":
    # open the input
    with open("req.json", "r") as f:
        req = json.loads(f.read())

    # run the command
    try:
        resp = run(req)
    except Exception as e:
        resp = gen_error(-32000, str(e))

    # save the output
    with open("resp.json", "w") as f:
        f.write(unicode(json.dumps(resp)))

    exit(0)
