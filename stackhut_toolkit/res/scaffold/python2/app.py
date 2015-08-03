#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
{{ scaffold.name }} service
"""
import stackhut

class DefaultService:
    def __init__(self):
        pass

    def hello(self):
        return "Hello, StackHut! :)"

    def helloName(self, name):
        return "Hello, {}! :)".format(name)

    def add(self, x, y):
        return x + y

# export the services here
SERVICES = {"Default": DefaultService()}
