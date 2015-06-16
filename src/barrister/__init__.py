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
__version__ = '0.1.7'

from barrister.runtime import contract_from_file, idgen_uuid, idgen_seq
from barrister.runtime import RpcException, Server, Filter, HttpTransport, InProcTransport
from barrister.runtime import Client, Batch
from barrister.runtime import Contract, Interface, Enum, Struct, Function
# from barrister.docco import docco_html
# from barrister.graphviz import to_dotfile
