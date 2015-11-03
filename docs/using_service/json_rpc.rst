.. _using_json_rpc:

Direct JSON-RPC Usage
=====================

This involves creating JSON-RPC compatible requests on demand, thankfully this is very simple and so it's easy to call your StackHut services from anywhere.
It can then be accessed in the cloud via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.
To make it easier to call and use StackHut services we have started building client-libraries in several languages. They are described further in :ref:`using_client_libs`, and currently exist for Python and JavaScript. 

However it's always possible to construct the JSON-RPC request yourself in any langauge to consume a StackHut service - thankfully JSON-RPC is a very simple protocol, as shown in :ref:`using_json_rpc`, and this is much simpler than it sounds! 

Request:

.. code-block:: JSON

    {
        "service" : "mands/demo-python",
        "req" : {
            "method" : "add",
            "params" : [2, 2]        
            "id" : 1
        } 
    }    

In the above request, we call the method ``add`` from the StackHut service ``mands/demo-python`` with two parameter, the numbers 2, and 2. 
``params`` is a JSON list that can contain any JSON types, i.e. floats, strings, lists and objects. The types expected by the method are defined by the service and are shown on API section of the `services page <https://stackhut.com/#/u/mands/demo-python>`_. The types of the request are checked and an error will be returned if they do not match.
The ``id`` element is optional and will be added automatically if not present.

We can perform this call by simply sending a HTTP POST request, with content-type ``application/json`` to ``https://api.stackhut.com/run``. Let's save the above example as ``test_request.json`` and demonstrate this using the fantastic tool `httpie <https://github.com/jkbrzt/httpie>`_,

.. code-block:: bash

    http POST https://api.stackhut.com/run @./test_request.json 

This will make the request and on completion will output a bunch of things to your terminal, including a response body similar to the following,

.. code-block:: JSON

    {
        "response": {
            "id": "f335bc80-4289-4599-b655-55341b40bd1a", 
            "jsonrpc": "2.0", 
            "result": 4
        }, 
        "taskId": "d2e186d6-e746-4a4f-bb76-b39185e588d5"
    }

The ``response`` object is the JSON-RPC response, containing the return value in the ``result`` field - in this case the number 4 (we created all this to show 2 + 2 = 4 - but now in the cloud! :)). The ``id`` element is also present, to aid linking requests to repsonses, and there is also a top-level ``taskId`` element to uniquely represent this individual request.

Let's try and call the service method ``multiply`` but with two strings, rather than two numbers as expected. We'll edit the ``test_request.json`` as follows,

.. code-block:: JSON

    {
        "service" : "mands/demo-python",
        "req" : {
            "method" : "multiply",
            "params" : ["two", "three"],
            "id" : 1
        } 
    }    

and run,::

    http POST https://api.stackhut.com/run @./test_request.json 

returning,

.. code-block:: JSON

    {
        "response": {
            "error": {
                "code": -32602, 
                "message": "Function 'Default.multiply' invalid param 'x'. 'two' is of type <class 'str'>, expected int"
            }, 
            "id": "d15a719a-70e3-4643-87d2-92cb7157bb81", 
            "jsonrpc": "2.0"
        }, 
        "taskId": "c405cb17-0d57-4aee-804b-ad29edad3000"
    }


As before we receive a JSON-RPC response object, however this time the ``result`` field has been replaced with an ``error`` field, an object with an error code, a human readable text message, and an optional ``data`` sub-object with further information. You can use this data to handle the error as required within your code 

.. note:: The error codes are as those defined by the `JSON-RPC spec <http://www.jsonrpc.org/specification#error_object>`_.

We hope this shows how you can call any StackHut service from your code - you may either use an existing JSON-RPC library or roll your own functions to make the request and handle the response respectively.


.. Login into StackHut
.. -------------------
.. __Coming Soon__ - all services are curently free to use and can be accessed anonymously.

