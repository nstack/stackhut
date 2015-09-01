.. _using_general:

General Usage Notes
===================

StackHut services can be accessed easily either through client side libraries, or directly using the underlying JSON+HTTP protocol. Either way there are several pints to note to make communicating with your services as easy and efficient as possible.


.. _using_general_files:

Files
-----

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


The request returns a single object containing both, ``key``, a signed URL to which you may ``PUT`` a resource, and ``key``, a key to be passed to the StackHut service identifying the file. Within the StackHut service, a service author can call `stackhut.get_file(key)` from the StackHut runtime library (see :ref:`creating_runtime`) to download the file to the working directory.
We recognise this is an extra step and are working hard to remove this limitation. File handling using this endpoint is not supported in the client libraries at present.

Result files can are automatically placed onto S3 for easy retrieval by clients although can be uploaded elsewhere if required.

.. _using_general_auth:

Authentication
--------------

Authentication is provided within StackHut - this is used restrict service requests to the service author and explicitly allowed clients only. This can be enabled or disabled on a per-service basis by setting ``private`` to ``True`` or ``False`` respectively within the ``Hutfile.yaml``.

Authentication requires specifying both the StackHut ``username`` and either the user ``hash`` or a generatated API token that can be shared with clients. A registered StackHut user's ``hash`` can be found by running ``stackhut info`` and can used with private services to authenticate the user.

.. note:: Do not share your hash or use it directly within code that is run on untrusted devices, e.g. client-side JS. Generate and use an API token instead (however, API Tokens are currently in development. sorry!)

Authentication is supported within the client-side libs - create an ``SHAuth`` object and pass it to the ``SHService``, as shown in :ref:`using_client_libs`.
This ``auth`` object is added at the top-level to service message, in accordance with the JSON-RPC protocol described in :ref:`using_json_rpc`. You may need to do this manually if creating JSON-RPC messages directly,

.. code-block:: JSON

    {
        "auth" : {
            "username" : "$USERNAME",
            "hash" : "$HASH"
        }
    }


By default if an ``auth`` object exists in the request it is check by the API layer and only allowed through to the service if the auth object is valid for **any** StackHut user, regardless if the service is public or private. Authorisation is handled within services themselves, as described in :ref:`creating_app_auth`.

.. note:: To call a public service anonymously it's easiest to just not add an ``auth`` object to the request. We're aware that this can be confusing and are working on a simpler API. 

State
-----

Similar to files, we are currently hard at work on providing a standardised solution to handling state within a service - services are generally state-less by default and are fully destroyed and reconstructed between requests.

However, setting ``persistent: True`` in the ``Hutfile.yaml`` with keep the service alive between calls, and can be used to store state within application memory/local filesystem during the life-cycle of a service. This can be used, for instance, to cache long-running/complex computations or to keep database connections open. However due to the nature of the platform services may be restarted at anytime without warning and we recommend  treating this state as ephemeral.

To store state persistently, outside of the service life-cycle, it's possible to call and store data on an external platform, e.g. a hosted database, on an individual service basis. This is currently outside of StackHut's scope and you'll have to refer to your favourite hosted database documentation to integrate it with your chosen service language.

Batching
--------

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
