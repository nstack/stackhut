.. _tutorial_use:

Tutorial - Using a Service
==========================

In this tutorial presents a quick overview of how to access a StackHut service from within your application, whether it is written in Python, client/server-side JS, Ruby, .NET, and more. 
.. The best way to start is to watch the following screen-cast that take us through setting up a simple, Python-based StackHut service.

.. raw:: html

    <script type="text/javascript" src="https://asciinema.org/a/23990.js" id="asciicast-23990" async></script>

Selecting a service
-------------------

You can find all kinds of services, for instance, video encoding, compression, compilation, web scraping, and more, hosted at the `StackHut repository <https://stackhut.com/#/services>`_. 

For this tutorial we will be using the service *mands/demo-python*, created in :ref:`tutorial_create`.
We can view the documentation and API for this service on its `homepage <https://stackhut.com/#/u/mands/demo-python>`_, it has 2 methods, ``add`` and ``multiply``. 

Access a service directly
-------------------------

All StackHut services can be accessed and consumed via a direct HTTP POST request. On receiving a request, the StackHut host platform will spin-up a container on demand with the required service and complete your request. The whole StackHut infrastructure is abstracted away from the service code which is simply completing a function call. It can then be accessed in the cloud via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.

As a result any StackHut service can easily be consumed by constructing a JSON-RPC request in any language - thankfully JSON-RPC is a very simple protocol and this is much simpler than it sounds!

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


As before we receive a JSON-RPC response object, however this time the ``result`` field has been replaced with an ``error`` field, an object with an error code, a human readable text message, and an optional ``data`` sub-object with further information. You can use this data to handle the error as required within your code. (*NOTE* - the error codes are as those defined by the `JSON-RPC spec <http://www.jsonrpc.org/specification#error_object>`_.).

We hope this shows how you can call any StackHut service from your code - you may either use an existing JSON-RPC library or roll your own functions to make the request and handle the response respectively.
Thanks for reading this tutorial - you can find more information on calling services, for instance using the upcoming StackHut client-side libraries, in :ref:`usage_your_code`.

Want to develop a StackHut cloud API or fork an existing service? Read :ref:`tutorial_create` to get going - we can't wait to see what you come up with.
