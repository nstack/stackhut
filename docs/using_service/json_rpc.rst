.. _usage_your_code:

Direct Usage
============

Please read :ref:`tutorial_use` for basic information on how to access a service via JSON-RPC.



Access a service directly
-------------------------

This involves creating JSON-RPC compatible requests on demand, thankfully this is very simple and so it's easy to call your StackHut services from anywhere. See :ref:`tutorial_use` for basic info.

.. Login into StackHut
.. -------------------
.. __Coming Soon__ - all services are curently free to use and can be accessed anonymously.


Notes
-----

Files
^^^^^
.. _usage_your_code_files:

Often you will want to pass a file from your code to be processed by a StackHut service, for instance when processing a video or converting a PDF.

Currently files must to be uploaded separately to a online location from where they can be retrieved by the service over HTTP, for instance AWS S3, rather than embedded within the remote message.

To aid this we provide an endpoint, ``https://api.stackhut.com/files``, that you can ``POST`` to obtain a signed URL. The content of this ``POST`` request is a single JSON object, ``auth``, that contains both the username and either a ``hash`` or ``token`` element, similar to ``SHAuth`` above,

.. code-block:: JSON

    {
        "auth" : {
            "username" : "USERNAME",
            "hash" : "HASH"
        }
    }


The request returns a single object containing both, ``key``, a signed URL to which you may ``PUT`` a resource, and ``key``, a key to be passed to the StackHut service identifying the file. Within the StackHut service, a service author can call `stackhut.get_file(key)` from the StackHut runtime library (see :ref:`usage_runtime`) to download the file to the working directory.
We recognise this is an extra step and are working hard to remove this limitation. File handling using this endpoint is not supported in the client libraries at present.

Result files can are automatically placed onto S3 for easy retrieval by clients although can be uploaded elsewhere if required.

State
^^^^^

Similar to files, we are currently hard at work on providing a standardised solution to handling state within a service - at the moment all services are state-less by default. 
However a service may be programmed in such a sway to store data on an external platform, e.g. a hosted database, on an individual service basis.

Batching
^^^^^^^^

We have currently only described StackHut as performing a single request per call, however it's also possible to collect several request and perform them sequentially within a single call. This is termed ``batching`` mode and is easily accomplished in StackHut by simply sending a list of reesusts within the ``req`` object in the call,

.. code-block:: JSON

    {
        "service" : "stackhut/demo-nodejs-state",
        "req" : [
            {
                "method" : "inc",
                "params" : [10]        
                "id" : 1
            },
            {
                "method" : "inc",
                "params" : [20]        
                "id" : 2
            },
            {
                "method" : "getCur",
                "params" : []        
                "id" : 3
            }
        ]
    }    

These request will all be performed within a single service-call, great for increasing throughput and keeping your external calls over the cloud to StackHut to a minimum.
We have some exciting features planned involving batching that will allow you to setup complex cloud-based processing pipelines easily.

Batching is not supported in the client libraries at present.
