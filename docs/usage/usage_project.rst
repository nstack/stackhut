.. _usage_project:

StackHut Project Description
============================

Introduction
------------
In this section we describe the files created when you initialise a StackHut project using ``stackhut init baseos language`` (e.g. ``stackhut init fedora python``).

.. _usage_project_hutfile:

Hutfile
-------

The Hutfile is a YAML file that describes the configuration of your StackHut service. It has several required fields that describe the project and let you control the packaging of your service.

Here's a sample,

.. code-block:: yaml

    # Name for the service - we recommend using snake-case
    name: demo-python

    # Service author - must be a valid StackHut user
    author: mands
    
    # Public GitHub repo
    github_url: http://www.github.com/StackHut/demo-python

    # description of the service
    description: Awesome service in python

    # stack we use, in terms of the OS and language runtime
    baseos: alpine
    stack: python

Let's go through all the fields.

``name``
^^^^^^^^

*Required*

The name of the service - this does not need to be unique. We recommend keeping this the same as your project-s name in source control (e.g. on GitHub) and using snake-case.

``author``
^^^^^^^^^^

*Required*

The author of the service, this should be the username of a valid StackHut that you have access too. If you have multiple accounts you may need to run ``stackhut logout`` and ``stackhut login`` again to build and push services for multiple authors.


``github_url``
^^^^^^^^^^^^^^

*Optional*

A link to the repository on GitHub - we use this to create links on the service homepage to the issue tracker and source, if available.

``description``
^^^^^^^^^^^^^^^

*Optional*

A short text description of the service.

``baseos``
^^^^^^^^^^

*Required*

The base OS to use when creating an image. Currently we support,

======  ===========
Name    Description    
======  ===========
fedora  `Fedora 22 <http://getfedora.org/>`_ 
alpine  `Alpine Linux <http://alpinelinux.org/>`_
======  ===========


.. _usage_project_hutfile_stack:

``stack``
^^^^^^^^^

*Required*


The base language stack to use when creating an image. Currently we support,

=======     ===========
Name        Description    
=======     ===========
python      `Python 3 <http://python.org/>`_ 
python2     `Python 2 <http://python.org/>`_ 
nodejs      `NodeJS <http://nodejs.org/>`_
=======     ===========

.. note:: Currently we only support one language stack per service (although you could use this to call anothor language you've bundled into the image)

.. note:: If your chosen language stack has a package manager, e.g. pip for Python or npm for Node, you can fill out the packages file, e.g. ``requirements.txt`` or ``package.json`` respectivly and they'll be installed within your image.

``files``
^^^^^^^^^

*Optional*

A list of files and directories within the project directory to include and bundle alongside the image. Useful for specifying resource files and binaries, for instance.

See <www.github.com/StackHut/image-process> for an example.

``os_deps``
^^^^^^^^^^^

*Optional*

A list of OS packages you wish to bundle with your service, i.e. those installable via ``yum``, or ``apt-get``, depending on your ``baseos``. You may need to check with your choosing base OS repository to find the names of the packages and their versions.

.. note:: you can also install lanauge specific packages using the language package manager as described in :ref:`_usage_project_hutfile_stack`.

See <www.github.com/StackHut/pdf-tools> for an example.


``docker_cmds``
^^^^^^^^^^^^^^^

*Optional*

If the default workflow is not flexible enough, you can specify any additional scripting commands as a list within this section. They will be run when building your container and follow the `Dockerfile builder specification <https://docs.docker.com/reference/builder/>`_.

See <www.github.com/StackHut/browser> for an example.

Interface Definition (``api.idl``)
------------------------------

**TODO**


App Code
--------

**TODO**


Notes
-----

**TODO**

