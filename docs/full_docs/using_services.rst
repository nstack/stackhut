.. _usage_your_code:

Using Services
==============

Please read :ref:`tutorial_use` for basic information on how to access a service via JSON-RPC.


Access a service using client-side libraries
--------------------------------------------

Client-side libraries are have been/or are under development for the following platforms, please feel free to add support for your favourite langauge if not present, it's quite easy!

=============       ==============================  ===========   
Langauge            Install                         Source Code
=============       ==============================  ===========
Python              pip3 install stackhut-client    www.github.com/StackHut/client-python
JavaScript          npm install stackhut-client     www.github.com/StackHut/client-node
Ruby                *under development*
PHP                 *under development*
Java/JVM            *under development*
C#/.NET             *under development*
=============       ==============================  ===========


These libraries abstract away the entire JSON-RPC mechanism and make it as easy as calling a function to utilise a StackHut service. They marshal the data, collect the response, handling error messages along the way, and check the validity of the message before it's sent. For example, in the following code we create a service object to use an existing service called `demo-nodejs` by the user `stackhut`. Using this object we can call any functions on any interfaces exposed by the hosted `stackhut/demo-nodejs` service,


.. code-block:: python

    import stackhut_client as client
    service = client.SHService('stackhut', 'web-tools')
    result = service.Default.renderWebpage('http://www.stackhut.com', 1024, 768)
    print(result)
    >> http://stackhut-files.s3.amazonaws.com/stackhut/downloads/a77d49f6-af7d-4007-8630-f6f443de7680/5c77d73b-9c8c-4850-84eb-9196b19fb545/screen.png
  

Client-side Library API
^^^^^^^^^^^^^^^^^^^^^^^

The the gneeral behvous of the client libraries is similar in all lanauges and we describe it below using the Python client-library as a reference. 
There are 3 main classes in the library,

SHService
"""""""""

The main class representing a single StackHut service. It takes several parameters on construction, where those in square brackets are optional,

.. code:: python

    import stackhut_client as client
    client.SHService(author, service_name, [service_version], [auth], [host])

* author - The author of the service
* service_name - The service name
* version - The specific verion of the service (is `latest` if left blank)
* auth - An `SHAuth` object used to authenticate requests for private services
* host - URL for the StackHut API server, can be set to point to local servers during development, is `https://api.stackhut.com` if left blank

To make a remote call, just call the interface and method name on the service object, e.g.,

.. code:: python

    result = service.Interface.method(params, ...)


SHAuth
""""""

An optional class used to authenticate requests to a service, passed to a service on construction,

.. code:: python

    client.SHAuth(user, [hash], [token])

* user - Username of a registered StackHut user
* hash - Hash of the user's password (you can find this in ~/.stackhut.cfg). Be careful not to use in public-accessible code
* token - A valid API token created for the user

One of `hash` or `token` must be present in the `auth` object to authorise a request by the given user.

SHError
"""""""

Returned in the event of a remote service error as an exception/error depending on the specific client library.

The object has 3 parameters,

* code - A JSON-RPC error code
* message - A string describing the error
* data - An optional object that may contain additional structured data for handling the error



Access a service directly
-------------------------

This involes creating JSON-RPC compatible requests on demand, thanksfully this is very simple and so it's easy to call your StackHut services from anywhere. See :ref:`tutorial_use` for basic info.

.. Login into StackHut
.. -------------------
.. __Coming Soon__ - all services are curently free to use and can be accessed anonymously.


Notes
-----

Files
^^^^^

Often you will want to pass a file from your code to be processed by a StackHut service, for instance when processing a video or converting a PDF.



At the moment we require files to be uploaded separately to a online location from where it can be retrieved by the service over HTTP, for instance S3. We recognise this is an extra step and are working hard to remove this limitation.

Result files can are automatically placed onto S3 for easy retrieval by clients although can be uploaded elsewhere if required.

State
^^^^^

Similar to files, we are currently hard at work on providing a standardised solution to handling state within a service - at the moment all services are state-less by default. 
However a service may be programmed in such a sway to store data on an external platform, e.g. a hosted database, on an individual service basis.

Batching
^^^^^^^^

We have currently only described StackHut as performing a single request per call, however it's also possible to collect serveral request and perform them sequentially within a single call. This is termed ``batching`` mode and is easily accomplished in StackHut by simply sending a list of reesusts within the ``req`` object in the call,

.. code-block:: JSON

    {
        "service" : "stackhut/demo-nodejs-persistent",
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


