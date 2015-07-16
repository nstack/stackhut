#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 service
"""
import stackhut

class DefaultService:
    def __init__(self):
        pass

    def add(self, x, y):
        return x + y

# export the services
SERVICES = {"Default": DefaultService()}