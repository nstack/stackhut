.. _tutorial_use:

Tutorial - Using a Service
==========================

In this tutorial presents a quick overview of how to access a StackHut service from within your application, whether it is written in Python, client/server-side JS, Ruby, .NET, and more. 
.. The best way to start is to watch the following screen-cast that take us through setting up a simple, Python-based StackHut service.

.. .. raw:: html

..    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/Y8vBQCgA944" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
..    </div>


Selecting a service
-------------------

You can find all kinds of services, for instance, video encoding, compression, compilation, web scraping, and more, hosted at the `StackHut repository <https://stackhut.com/#/services>`_. Even better, develop or fork an exiting service as desribed in :ref:`tutorial_create`.


Access a service directly
-------------------------

All StackHut services can be accessed and consumed via a direct HTTP POST request. On receiving a request, the StackHut host platform will spin-up a container on demand with the required service and complete your request. The whole StackHut infrastructure is abstracted away from the service code which is simply completing a function call. It can then be accessed in the cloud via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.

As a result any StackHut service can easily be consumed by constructing a JSON-RPC request in any language - thankfully JSON-RPC is a very simple protocol and this is much simpler than it sounds!

Request:

.. code-block:: JSON

    {
        "serviceName" : "example-python",
        "req" : {
            "method" : "helloName",
            "params" : ["StackHut"]        
            "id" : 1
        } 
    }    

In the above request, we call the method ``helloName`` from the StackHut service ``example-python`` with a single parameter ``StackHut``. 
``Params`` is a JSON list that can contain any JSON types, i.e. floats, strings, lists and objects. The types expected by the method are defined by the service and are shown on API section of the `services page <https://stackhut.com/#/example-python>`_. The types of the request are checked and an error will be returned if they do not match.
The ``id`` element is optional and will be added automatically if not present.

We can perform this call by simply sending a HTTP POST request, with content-type ``application/json`` to ``https://api.stackhut.com/run``. Let's save the above example as ``test_request.json`` and demonstrate this using the fantastic tool ```http`` <https://github.com/jkbrzt/httpie>`_::

    http POST https://api.stackhut.com/run < ./test_request.json 

This will make the request and on completion will output a bunch of things to your terminal, including a response body similar to the following,

Response

.. code-block:: JSON

    {
        "response": {
            "jsonrpc": "2.0", 
            "id": 1 
            "result": "Hello, StackHut! :)"
        }, 
        "taskId": "71c530bb-8875-4143-8932-2e75ddaeddbd"
    }

The ``response`` object is the JSON-RPC response, containing the return value in the ``result`` field - in this case the string  *Hello, StackHut :)*. The ``id`` element is also present, to aid linking requests to repsonses, and there is also a top-level ``taskId`` element to uniquely represent this individual request.

Let's try and call the same service method ``helloName`` but with a number, rather than a string as expected. We edit the ``test_request.json`` as follows,

.. code-block:: JSON

    {
        "serviceName" : "example-python",
        "req" : {
            "method" : "helloName",
            "params" : [10],
            "id" : 1
        } 
    }    

and run,::

    http POST https://api.stackhut.com/run < ./test_request.json 

returning,

.. code-block:: JSON

    {
        "response": {
            "error": {
                "code": -32602, 
                "message": "Function 'Default.helloName' invalid param 'name'. '1' is of type <class 'int'>, expected string"
            }, 
            "id": "8cb2b084-029b-405c-8ba1-480e792aab9f", 
            "jsonrpc": "2.0"
        }, 
        "taskId": "5e5b5b50-0c86-4db8-ab66-e5f7225ff260"
    }

As before we receive a JSON-RPC response object, however this time the ``result`` field has been replaced with an ``error`` field, containing an object with an error code, a human readable text message, and an optional ``data`` object containing further information. You can use this information to handle the error as required within your code. (*NOTE* - the error codes are as those defined by the `JSON-RPC spec <http://www.jsonrpc.org/specification#error_object>`_.).

We hope this shows how you can call any StackHut service from your code - you may either use an existing JSON-RPC library or roll your own functions to make the request and handle the response respectively.
Thanks for reading this tutorial - you can find more information on calling services, for instance using StackHut client-side libraries, in :ref:`usage_your_code`.

