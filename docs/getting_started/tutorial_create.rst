.. _tutorial_create:

Tutorial - Creating a Service
=============================

StackHut allows you to rapidly deploy your code as an API in the cloud. Your code is wrapped up and runs inside a container whose functions you can call over HTTP. 

This tutorial briefly describes how you can develop, test and deploy a simple service on StackHut within a few minutes. Fristly just check you've installed the dependencies as described in :ref:`installation`. We also recommend watching the following, short, companion video that walks you through setting up a Python-based service.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/Y8vBQCgA944" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>


Further information on creating a service can be found in :ref:`usage_cli` and :ref:`usage_project`.


Create an Account
-----------------

.. note:: An account is only needed to deploy services to the hosted StackHut platform, but it's easier to just set one up when starting out.

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

.. We hope this will keep things simple and help you get up a running quickly without having to create another login.

Currently we also ask that you create a `Docker Hub <hub.docker.com>`_ account if you don't already have one - this is used to store your StackHut builds and images for deployment on the platform. You can again use your GitHub authentication with DockerHub and we recommend using the same username across all if possible for ease of use.

Ok, now that's all done let's log in to StackHut from the Toolkit, type

.. code-block:: bash

    [mands@laptop ~]$ stackhut login
    >> Username: mands
    >> Password: *****
    >> User mands logged in successfully

and enter your username and password as created earlier. This will securely connect to StackHut and validate your login.

.. note:: The ``stackhut login`` command may fail and ask that you run ``docker login`` first using your Docker Hub credentials.  This is so that StackHut will use the correct Docker Hub account to store images.

To logout just run ``stackhut logout``.

.. note:: StackHut deploys and hosts APIs using the currently logged-in user, if you have multiple accounts with both/either StackHut or DockerHub with different hosted APIs you may have to run ``stackhut logout/login`` as neccessary. 


Initialise a Project
--------------------

We start by initialising a StackHut project, let's call this one ``demo-python``,

.. code-block:: bash

    # create and cd into the project directory
    [mands@laptop ~]$ mkdir demo-python
    [mands@laptop ~]$ cd demo-python
    # run stackhut init to initialise the project
    [mands@laptop demo-python]$ stackhut init alpine python

The ``stackhut init`` command takes two parameters, the base operating system, in this case `Alpine Linux <http://alpinelinux.org/>`_ (a minimal Linux distribution ideal for use with containers), and the language stack to use, here Python (short for Python 3). In return it creates a working skeleton project for you to quickly get going with, including an initial Git commit.
This contains all the files a StackHut service needs, already configured using sensible defaults for the chosen system,

.. code-block:: bash

    [mands@laptop demo-python]$ ls
    api.idl  app.py  Hutfile  README.md  requirements.txt  test_request.json

There are several files here - and we'll cover the important ones in the following sections - they are all discussed further in :ref:`usage_project_hutfile`.
The ``Hutfile`` is a *YAML* file containing configuration regarding our stack and dependencies - more information regarding its parameters can be found in :ref:`usage_project_hutfile`.

.. There is also a README.md markdown file to further describe your service.


Signature
---------

The ``api.idl`` interface-definition (IDL) file describes our service interface - after deployment these entry-points are accessible over HTTP.
The file uses a Java-like syntax to describe the service interface using JSON types, e.g. numbers, strings, lists, and objects. This is based on the `Barrister RPC project <http://barrister.bitmechanic.com/>`_, the format of which is described in the `project documentation <http://barrister.bitmechanic.com/docs.html>`_.

Let's take a look,

.. code-block:: java

    interface Default {
        // add 2 integers and return the result
        add(x int, y int) int
    }


By default we are exposing a single function, ``add``, that takes two ``ints``, and returns an ``int``. Now let's add a new function, ``multiply``, and write the corresponding signature - all pretty straightforward,

.. code-block:: java

    interface Default {
        // add 2 integers and return the result
        add(x int, y int) int

        // multiply 2 integers and return the result
        multiply(x int, y int) int
    }


Code
----

Having defined our interface we may now write our code. The app code lives in ``app.py`` (or ``app.js`` for JS, and so on), as follows,

.. code-block:: python

    """
    Demo service
    """
    import stackhut

    class DefaultService:
        def __init__(self):
            pass

        def add(self, x, y):
            return x + y

    # export the services
    SERVICES = {"Default": DefaultService()}

As seen, the service is a plain old Python class with a function for each entrypoint. The ``add`` function has already been implemented and is simple enough. Now let's add the ``multiply`` function, no surprises here. 

.. code-block:: python

    """
    Demo service
    """
    import stackhut

    class DefaultService:
        def __init__(self):
            pass

        def add(self, x, y):
            return x + y

        def multiply(self, x, y):
            return x * y

    # export the services
    SERVICES = {"Default": DefaultService()}



Build, Run, and Test
--------------------

Now we're done coding, and because we're all responsible developers let's build, run, and test our service before we deploy. 


We can build our service, this means packaging up all the code, dependencies, and anything else into a container image that can be deployed into the cloud,

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut build

If this completes sucessfully your code can be deployed to the cloud - however it would be great to test if it runs correctly beforehand.

.. note:: The build command is called indirectly by the ``run`` and ``deploy`` commands and is smart enough to run only if any files within the project directory have changed. However you can force a build by running ``stackhut build --force``.

By default there is a file called ``test_request.json`` that represents a HTTP request to our service. This file specifies the ``service``, the ``method``, and ``parameters`` already configured for the ``add`` endpoint,

.. code-block:: json

    {
        "service": "mands/demo-python",
        "req": {
            "method": "add",
            "params": [2, 2]
        }
    }

.. note:: This format is actually `JSON-RPC <www.json-rpc.org>`_ - described further in :ref:`tutorial_use`

Let's run our service using this file as-is to test our ``add`` function,

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut run test_request.json

This builds the image and simulates the request against your code in the service container, using the ``test_request.json`` file from the host project directory. 
The output from calling this service method can be found in the ``run_results`` directory on the host - let's look at the request output in ``response.json``,

.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "7fad6810-35ef-4891-b6b3-769aeb3c1d25"
        "result": 4
    }

.. note :: Running an image requires Docker to be installed and configured correctly. If you get errors try running `docker info`, and if you're on OSX remember to run `boot2docker up` first.

We can modify the ``test_request.json`` as follows to test our ``multiply`` function, and run it again,

.. code-block:: json

    {
        "service": "mands/demo-python",
        "req": {
            "method": "multiply",
            "params": [3, 2]
        }
    }

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut run test_request.json

.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "73a04803-ff37-4f7a-9763-349d57e54123"
        "result": 6
    }

Great, so we've built and tested a container with your code, and it's all working against the stack and dependencies specified in the ``Hutfile``. You can be sure that it'll be running the exact same code, in the same container, when it's deployed on the server.

However sometimes the delay when rebuilding the image and run the service inside the container can get in the way of rapid development. To help with this is the ``runhost`` command, this runs the service using your main OS and any dependencies you have installed. 
Let's try this using the same test sample, 

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut runhost test_request.json


.. code-block:: json

    {
        "jsonrpc": "2.0", 
        "id": "7fad6810-35ef-4891-b6b3-769aeb3c1d25"
        "result": 6
    }

Fantastic - we get the same result using ``runhost``, using dependencies installed on your main OS and things are much quicker.

Having ran our tests we're now ready to deploy and host the service on the StackHut live platform.

Deploy
------

This couldn't be simpler,

.. code-block:: bash

    [mands@laptop demo-python]$ stackhut deploy

This packages and builds your service, and then deploys it to StackHut along with metadata such that it may be searched, viewed, and importantly, used, on the platform. 
As soon as this completes, your API is live on `https://api.stackhut.com/run` and can be browsed from our `repository of existing APIs <https://www.stackhut.com/#/services>`_.
 
Use
---

We can view the API from `its repository homepage <https://www.stackhut.com/#/services/demo-python>`_, browse the documentation, and for instance, call the ``multiply`` function.
The service is live and ready to receive requests right now in the browser or from anywhere else via HTTP. 

Further documentation on how to call and make use of a StackHut from your code can be found in :ref:`tutorial_use`.
Thanks for reading this - we've been using StackHut to create web-scrapers, image processing tools, video conversion APIs and more and we'd love to see what you come up with. 

