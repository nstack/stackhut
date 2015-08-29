.. _tutorial_use:

Tutorial - Using a Service
==========================

In this tutorial presents a quick overview of how to access a StackHut service from within your application, whether it is written in Python, client/server-side JS, Ruby, .NET, and more. 

Overview
--------

All StackHut services can be accessed and consumed via a direct HTTP POST request. On receiving a request, the StackHut host platform will route the request on demand to the required service to  complete it. 
The whole StackHut infrastructure is abstracted away from your service code, from its point of view it's simply executing a function call.


It can then be accessed in the cloud via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.
To make it easier to call and use StackHut services we have started building client-libraries in several lanauges. They are described further in :ref:`using_client_libs_`, and currently exist for Python and JavaScript. 

However it's always possible to contsruct the JSON-RPC request yourself in any lanauge to consume a StackHut service - thankfully JSON-RPC is a very simple protocol, as shown in :ref:`using_json_rpc_`, and this is much simpler than it sounds! 


Selecting a service
-------------------

You can find all kinds of services, for instance, video encoding, compression, compilation, web scraping, and more, hosted at the `StackHut repository <https://stackhut.com/#/services>`_. 

Sercices are prefixed by their author, such as ``stackhut/demo-python``. We can view the documentation and API for this service on its `homepage <https://stackhut.com/#/u/stackhut/demo-python>`_, it has 2 methods, ``add`` and ``multiply``. 


Calling a service
-----------------

For this tutorial we'll use the ``demo-python`` service created in above (if you didn't create one you can use ``stackhut/demo-python`` instead). We'll use the Python 3.x client library (described in :ref:`using_client_libs_`) to call this service.

First we'll create a ``SHService`` object to reference the service,

.. code-block:: python

    import stackhut_client as client
    service = client.SHService('stackhut', 'demo-python')

where ``stackhut`` is the service author (replace with your own service name), and ``demo-python`` is the service name. Now we have the service we can just call the methods on the ``Default`` interface,

.. code-block:: python

    service.Default.add(1, 2)
    >> 3
    service.Default.multiply(2, 3)
    >> 6


Thanks for reading this tutorial - you can find more information on calling services in :ref:`using`. Further detailes decribed how we built and can call more complex services, such as a web-scraper, or an image-processor, can be found in :ref:`examples`.

.. Want to develop a StackHut cloud API or fork an existing service? Read :ref:`tutorial_create` to get going - we can't wait to see what you come up with.
