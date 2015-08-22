# -*- coding: utf-8 -*-
"""
    common.barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    http://common.barrister.bitmechanic.com/

    :copyright: 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""
__version__ = '0.1.7.stackhut'

from .runtime import contract_from_file, idgen_uuid, idgen_seq
from .runtime import RpcException, Server, Filter, HttpTransport, InProcTransport
from .runtime import Client, Batch
from .runtime import Contract, Interface, Enum, Struct, Function
from .runtime import err_response, ERR_PARSE, ERR_INVALID_REQ, ERR_METHOD_NOT_FOUND, \
    ERR_INVALID_PARAMS, ERR_INTERNAL, ERR_UNKNOWN, ERR_INVALID_RESP
from .parser import parse

