.. _getting_started_tutorial:

Tutorial
========

StackHut turns classes into cloud APIs, so you can call your functions over HTTP or natively using our client libraries.

This tutorial briefly describes how you can develop, test and deploy a simple service on StackHut. This one will only take a few minutes, but services can be as complex as you like. Firstly, check you've installed the StackHut dependencies as described in :ref:`getting_started_installation`. 

You don't need an account to develop and run services locally, however if you wish to deploy online you need to register on the `StackHut website <https://www.stackhut.com>`_ and log in locally, as described later in this tutorial.

Further information on creating a service can be found in :ref:`creating_toolkit` and :ref:`creating_structure`.

Creating a Service
------------------

Initialise a Project
^^^^^^^^^^^^^^^^^^^^

We start by initialising a StackHut project, let's call this one ``demo-python``,

.. code-block:: bash

    # create and cd into the project directory
    [~]$ mkdir demo-python
    [~]$ cd demo-python
    # run stackhut init to initialise the project
    [demo-python]$ stackhut init fedora python

The ``stackhut init`` command takes two parameters: the base operating system, in this case `Fedora Linux <http://getfedora.org/>`_, and the language stack to use, here Python (short for Python 3). When run, StackHut will create a working skeleton project for you to quickly get started with, including an initial Git commit.
This contains all the files a StackHut service needs, already configured using sensible defaults for the chosen system.

.. code-block:: bash

    [demo-python]$ ls
    api.idl  app.py  Hutfile.yaml  README.md  requirements.txt  test_request.json

There are several files here - and we'll cover the important ones in the following sections. They are all discussed further in :ref:`creating_structure_hutfile`.
The ``Hutfile.yaml`` is a *YAML* file containing configuration regarding our stack and dependencies - more information regarding its parameters can be found in :ref:`creating_structure_hutfile`.

.. There is a README.md markdown file to further describe your service.


Signature
^^^^^^^^^

The ``api.idl`` interface-definition (IDL) file describes our service interface. After you deploy your service, these functions will act as 'entry-points' into your code: i.e., you will be able to call them over HTTP, and they will run the corresponding function in your code.

The file uses a Java-like syntax to describe the service interface using JSON types, e.g. numbers, strings, lists, and objects. This is based on the `Barrister RPC project <http://barrister.bitmechanic.com/>`_, the format of which is described in the `project documentation <http://barrister.bitmechanic.com/docs.html>`_.

Let's take a look,

.. code-block:: java

    interface Default {
        // add 2 integers and return the result
        add(x int, y int) int
    }


By default we are exposing a single function, ``add``, that takes two ``ints``, and returns an ``int``. Now let's add a new function, ``multiply``, and write the corresponding signature. Your comment will be used to generate documentation for your function:

.. code-block:: java

    interface Default {
        // add 2 integers and return the result
        add(x int, y int) int

        // multiply 2 integers and return the result
        multiply(x int, y int) int
    }


Code
^^^^

Having defined our interface, we can now write the code for ``multiply``. Your app code lives in ``app.py`` (or ``app.js`` for JS, and so on), as follows:

.. code-block:: python

    #!/usr/bin/env python3
    """Demo Service"""
    import stackhut

    class Default(stackhut.Service):

        def add(self, x, y):
            return x + y

    # export the services
    SERVICES = {"Default": Default()}

As seen, the service is a plain old Python class with a function for each entrypoint. The ``add`` function has already been implemented and is simple enough. Now let's add the ``multiply`` function: no surprises here. 

.. code-block:: python

    #!/usr/bin/env python3
    """Demo Service"""
    import stackhut

    class Default(stackhut.Service):

        def add(self, x, y):
            return x + y

        def multiply(self, x, y):
            return x * y

    # export the services
    SERVICES = {"Default": Default()}



Hosting your Service
--------------------

Now you've developed your service you can host it locally to test it further, or you can go straight ahead and deploy live to the StackHut hosting platform. 

.. note:: We're also working hard to provide a private, self-hosted solution that runs on any cloud-provider and on-prem.

Hosting locally
^^^^^^^^^^^^^^^

.. Now we're done coding, and because we're all responsible developers, let's run, and test our service before we deploy. 

To run our service locally, we have two options. Firstly, we can use ``stackhut runhost`` which will run the code with our own Operating System and version of Python/Node.

Secondly, we can use ``stackhut runcontainer``. This will do a full test by building a Docker container which will be exactly the same as the one that runs on the StackHut platform. It will package up the OS and dependencies you specified and run it with Docker.


.. note:: ``stackhut runcontainer`` requires `Docker <https://www.docker.com/>`_ to be installed and running.

When you do either, StackHut will run a local HTTP server on port 4001 which you can use to call and test your service, as described in the below section.


Hosting on StackHut
^^^^^^^^^^^^^^^^^^^

To deploy your service live on the cloud you need to create an account first and then login locally.

Create an Account
"""""""""""""""""

Go to the `StackHut website <https://www.stackhut.com>`_ and click the link on the front-page that says *Sign up with GitHub*. This will use *OAuth* to authenticate and create a user on StackHut using your GitHub username and email. 

.. note:: We only request access to your GitHub email address to set up the StackHut account and have no access to your repositories or SSH keys.

Upon completion you'll be asked to enter a password for your StackHut account. Thus your StackHut credentials will be,

========    ===== 
Param       Value 
========    ===== 
Username    Github Username 
Email       GitHub email 
Password    StackHut password
========    ===== 

Now that is done, we can login in to StackHut from the Toolkit. In your console, type

.. code-block:: bash

    [~]$ stackhut login
    >> Username: mands
    >> Password: **********
    >> User mands logged in successfully

and enter your username and password as created earlier. This will securely connect to StackHut and validate your login.

To logout just run ``stackhut logout``.

Deploy your service
"""""""""""""""""""

This couldn't be simpler: your code will be deployed and hosted on the high-availability StackHut platform. Just run,

.. code-block:: bash

    [demo-python]$ stackhut deploy

This will upload your code, package it, build your service, and then deploy it to StackHut. The first time you run ``deploy`` it may take a couple of minutes to build, however subsequent builds will be faster.

The service is live and ready to receive requests right now in the browser or from anywhere else via HTTP or our client libraries. 
You can view your new API on your StackHut account, where you can test it and see your functions <https://www.stackhut.com/#/u/user/demo-python>`_ (replace ``user`` with your stackhut username).


Using your Service
------------------

All local and hosted StackHut services can be accessed and consumed via a direct HTTP POST request. On receiving a request, StackHut will route the request on-demand to the required service to complete it. 
The whole StackHut infrastructure is abstracted away from your service code, from its point of view it's simply executing a function call.

.. It can then be accessed locally or in the cloud via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.

To make it easier to use local and hosted StackHut services, we have built client-libraries. They are described further in :ref:`using_client_libs`, and are currently available for Python and JavaScript. 

.. note:: It's always possible to construct the JSON-RPC request yourself and send it over HTTP. JSON-RPC is a very simple protocol, as shown in :ref:`using_json_rpc`, and this is much simpler than it sounds! 



Calling a service
^^^^^^^^^^^^^^^^^


Services are prefixed by their author, such as ``stackhut/demo-python``. We can view the documentation and API for this service on its `homepage <https://stackhut.com/#/u/stackhut/demo-python>`_, it has 2 methods, ``add`` and ``multiply``. 

For this tutorial we'll use the ``demo-python`` service created in above (if you didn't create one you can use ``stackhut/demo-python`` instead). We'll use the Python 3.x client library (described in :ref:`using_client_libs`) to call this service.

First we'll create a ``SHService`` object to reference the service,

.. code-block:: python

    import stackhut_client as client
    service = client.SHService('stackhut', 'demo-python')

where ``stackhut`` is the service author (replace with your own username), and ``demo-python`` is the service name. 
Now we have the service we can just call the methods on the ``Default`` interface,

.. code-block:: python

    service.Default.add(1, 2)
    >> 3
    service.Default.multiply(2, 3)
    >> 6

We can use the same client libraries to call local services for testing, e.g. a service started using ``stackhut runcontainer``, just by passing the local service URL to the service constructor,

.. code-block:: python

    service = client.SHService('stackhut', 'demo-python', host='localhost:4001')
    service.Default.add(1, 2)
    >> 3

This makes it much easier to integrate StackHut into your client code whilst developing and testing a service.


Further Information
-------------------


Thanks for reading this tutorial - you can find more information on calling services in :ref:`using_index`. 

This was a super simple example, but you can build anything you can in Python or Node: we've been using StackHut to create web-scrapers, image processing tools, video conversion APIs and more. Several of these are hosted publicly at the `StackHut repository <https://stackhut.com/#/services>`_, and in :ref:`examples_index` we describe how we built them.

.. You can find all kinds of services, for instance, video encoding, compression, compilation, web scraping, and more, 

We'd love to see what you come up with. 



