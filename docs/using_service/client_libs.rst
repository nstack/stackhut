.. _using_client_libs:

Client-side Libraries
=====================

Client-side libraries are have been/or are under development for the following platforms, please feel free to add support for your favourite language if not present, it's quite easy!

=============       ==============================  ===========   
Langauge            Install                         Source Code
=============       ==============================  ===========
Python              pip3 install stackhut-client    http://www.github.com/StackHut/client-python
JavaScript          npm install stackhut-client     http://www.github.com/StackHut/client-node
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
  

Client libraries API
--------------------

The the general behaviour of the client libraries is similar in all languages and we describe it below using the Python client-library as a reference. 
There are 3 main classes in the library,

SHService
^^^^^^^^^

The main class representing a single StackHut service. It takes several parameters on construction, where those in square brackets are optional,

.. code:: python

    import stackhut_client as client
    client.SHService(author, service_name, [service_version], [auth], [host])

* author - The author of the service
* service_name - The service name
* version - The specific version of the service (is `latest` if left blank)
* auth - An `SHAuth` object used to authenticate requests for private services
* host - URL for the StackHut API server, can be set to point to local servers during development, is `https://api.stackhut.com` if left blank

To make a remote call, just call the interface and method name on the service object, e.g.,

.. code:: python

    result = service.Interface.method(params, ...)


SHAuth
^^^^^^

An optional class used to authenticate requests to a service, passed to a service on construction,

.. code:: python

    client.SHAuth(user, [hash], [token])

* user - Username of a registered StackHut user
* hash - Hash of the user's password (you can find this in ~/.stackhut.cfg). Be careful not to use in public-accessible code
* token - A valid API token created for the user

One of `hash` or `token` must be present in the `auth` object to authorise a request by the given user.

SHError
^^^^^^^

Returned in the event of a remote service error as an exception/error depending on the specific client library.

The object has 3 parameters,

* code - A JSON-RPC error code
* message - A string describing the error
* data - An optional object that may contain additional structured data for handling the error



