.. _tutorial_create:

Tutorial - Creating a Service
=============================

StackHut turns classes into cloud APIs, so you can call your functions over HTTP or natively using our client libraries.

This tutorial briefly describes how you can develop, test and deploy a simple service on StackHut. This one will only take a few minutes, but services can be as complex as you like. Firstly, check you've installed the StackHut dependencies as described in :ref:`installation`. 

Further information on creating a service can be found in :ref:`usage_cli` and :ref:`usage_project`.


Create an Account
-----------------

Go to the `StackHut website <www.stackhut.com>`_ and click the link on the front-page that says *Sign up with GitHub*. This will use *OAuth* to authenticate and create a user on StackHut using your GitHub username and email. 

.. note:: We only request access to your GitHub email address to set up the StackHut account and have no access to your repositories.

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

    [mands@laptop ~]$ stackhut login
    >> Username: mands
    >> Password: *****
    >> User mands logged in successfully

and enter your username and password as created earlier. This will securely connect to StackHut and validate your login.

To logout just run ``stackhut logout``.


Initialise a Project
--------------------

We start by initialising a StackHut project, let's call this one ``demo-python``,

.. code-block:: bash

    # create and cd into the project directory
    [mands@laptop ~]$ mkdir demo-python
    [mands@laptop ~]$ cd demo-python
    # run stackhut init to initialise the project
    [mands@laptop demo-python]$ stackhut init fedora python

The ``stackhut init`` command takes two parameters: the base operating system, in this case `Fedora Linux <http://getfedora.org/>`_, and the language stack to use, here Python (short for Python 3). When run, StackHut will create a working skeleton project for you to quickly get started with, including an initial Git commit.
This contains all the files a StackHut service needs, already configured using sensible defaults for the chosen system.

.. code-block:: bash

    [mands@laptop demo-python]$ ls
    api.idl  app.py  Hutfile.yaml  README.md  requirements.txt  test_request.json

There are several files here - and we'll cover the important ones in the following sections. They are all discussed further in :ref:`usage_project_hutfile`.
The ``Hutfile.yaml`` is a *YAML* file containing configuration regarding our stack and dependencies - more information regarding its parameters can be found in :ref:`usage_project_hutfile`.

.. There is a README.md markdown file to further describe your service.


Signature
---------

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
----

Having defined our interface, we can now write the code for ``multiply``. Your app code lives in ``app.py`` (or ``app.js`` for JS, and so on), as follows:

.. code-block:: python

    #!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    """
    Demo Service
    """
    import stackhut

    class Default(stackhut.Service):

        def add(self, x, y):
            return x + y

    # export the services
    SERVICES = {"Default": Default()}

As seen, the service is a plain old Python class with a function for each entrypoint. The ``add`` function has already been implemented and is simple enough. Now let's add the ``multiply`` function: no surprises here. 

.. code-block:: python

    #!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    """
    Demo Service
    """
    import stackhut

    class Default(stackhut.Service):

        def add(self, x, y):
            return x + y

        def multiply(self, x, y):
            return x * y

    # export the services
    SERVICES = {"Default": Default()}



Build, Run, and Test
--------------------

Now we're done coding, and because we're all responsible developers, let's run, and test our service before we deploy. 

To run our service locally, we have two options. Firstly, we can use ``stackhut runhost`` which will run the code with our own Operating System and version of Python/Node.

Secondly, we can use ``stackhut runcontainer``. This will do a full test by building a Docker container which will be exactly the same as the one that runs on the StackHut platform. It will package up the OS and dependencies you specified and run it with Docker.

.. note:: This requires Docker to be up and running.

When you do either, StackHut will run a local HTTP server on port 4001 which you can use to simulate a request to StackHut.

By default there is a file called ``test_request.json`` that represents a HTTP request to our service. This file specifies the ``service``, the ``method``, and ``parameters`` already configured for the ``add`` endpoint,

.. code-block:: json

    {
        "service": "mands/demo-python",
        "request": {
            "method": "add",
            "params": [2, 2]
        }
    }

.. note:: This format is actually `JSON-RPC <www.json-rpc.org>`_ - described further in :ref:`tutorial_use`

Let's pipe this request into our server using ``curl``.

.. code-block:: bash

    [mands@laptop demo-python]$ curl -H "Content-Type: application/json" -X POST -d @test_request.json http://127.0.0.1:4001

This gives us the output:

.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "7fad6810-35ef-4891-b6b3-769aeb3c1d25"
        "result": 4
    }


We can modify the ``test_request.json`` as follows to test our ``multiply`` function, and run it again,

.. code-block:: json

    {
        "service": "mands/demo-python",
        "request": {
            "method": "multiply",
            "params": [3, 2]
        }
    }

.. code-block:: bash

    [mands@laptop demo-python]$ curl -H "Content-Type: application/json" -X POST -d @test_request.json http://127.0.0.1:4001

.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "73a04803-ff37-4f7a-9763-349d57e54123"
        "result": 6
    }

Having ran our tests, we're now ready to deploy and host the service on the StackHut platform.

Deploy
------

This couldn't be simpler,

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut deploy

This uploads your code, packages it up, builds your service, and then deploys it to StackHut. The first time you run this, it may be take a couple of minutes to build. Subsequent builds will be faster.

 
Use
---

The service is live and ready to receive requests right now in the browser or from anywhere else via HTTP or our client libraries. 

.. code-block:: bash

    [mands@laptop demo-python]$ curl -H "Content-Type: application/json" -X POST -d @test_request.json https://api.stackhut.com/run

.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "73a04803-ff37-4f7a-9763-349d57e54123"
        "result": 6
    }


You can view your new API on your StackHut homepage. 

Further documentation on how to call and make use of a StackHut from your code can be found in :ref:`tutorial_use`.
This is a super simple example, but you can build anything you can in Python or Node: we've been using StackHut to create web-scrapers, image processing tools, video conversion APIs and more. We'd love to see what you come up with. 

