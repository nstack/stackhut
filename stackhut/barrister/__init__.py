# -*- coding: utf-8 -*-
"""
    barrister
    ~~~~~~~~~

    A RPC toolkit for building lightweight reliable services.  Ideal for
    both static and dynamic languages.

    http://barrister.bitmechanic.com/

    :copyright: 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""
__version__ = '0.1.7_stackhut'

from .runtime import contract_from_file, idgen_uuid, idgen_seq
from .runtime import RpcException, Server, Filter, HttpTransport, InProcTransport
from .runtime import Client, Batch
from .runtime import Contract, Interface, Enum, Struct, Function
from .runtime import ERR_PARSE, ERR_INVALID_REQ, ERR_METHOD_NOT_FOUND, \
    ERR_INVALID_PARAMS, ERR_INTERNAL, ERR_UNKNOWN, ERR_INVALID_RESP

from .parser import parse

import json
# from barrister.docco import docco_html
# from barrister.graphviz import to_dotfile


def generate_contract(idl_fname, contract_fname):
    with open(idl_fname, 'r') as idl_file:
        parsed = parse(idl_file, idl_fname)

    with open(contract_fname, "w") as contract_file:
        contract_file.write(json.dumps(parsed))
