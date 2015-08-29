.. _creating_runtime:

StackHut Runtime Library
========================

When running a StackHut service there are many common functions you may wish to perform and interact with the host environment, be t running locally on your machine or when hosted on the StackHut platform.

In this section we describe the StackHut library full of common functionality you can use in your service to make the process a lot easier.


Usage
-----

The StackHut library is available on all supported language stacks. 
It exposes a common set of functions across them all for interacting with the hosting platform and the wider world when running a service.

In most languages you simply import the ``stackhut`` module within your service and use the functions directly. (If you used ``stackhut init`` this will already be done within the created skeleton service.)

API
---

download_file
^^^^^^^^^^^^^

.. code-block:: python

    stackhut.download_file(url, fname)

Downloads a file from the given ``url`` into the working directory. If ``fname`` is provided will rename the download file to this value, else will use the original filename. 

Returns the filename of the downloaded file.

get_file
^^^^^^^^

.. code-block:: python

    stackhut.get_file(key)

This function is used to download files uploaded using the ``/files`` endpoint (see :ref:`using_general_files`). It securly downloads the file refernced by the given ``key`` into the working directory and returns the filename.


put_file
^^^^^^^^

.. code-block:: python

    stackhut.put_file(fname, make_public)

This function uploads the file referenced by ``fname`` in the service working directory to cloud storage (S3) where it can be downloaded by yourself or others.
``make_public`` is an optional boolean that triggers whether the uploaded file is made accessible as a public URL, by default this is True.

Returns the URL of the uploaded file.


get_stackhut_user
^^^^^^^^^^^^^^^^^

.. code-block:: python

    stackhut.get_stackhut_user()

Returns the authenticated StackHut username of the request originator as a string, or ``null`` if not present. This has been authenticated by the server and can be used securely to know who made the request. 

run_command
^^^^^^^^^^^

.. code-block:: python

    stackhut.run_command(cmd, stdin)

Runs the command specified by ``cmd`` as an external process and waits for completeion. ``stdin`` is an optional string that, when specified, will be used as the STDIN to the command.

Function waits for the subprocess to complete and returns STDOUT as a string.


General Notes
-------------

All functions are blocking by default, however each call runs in a separate thread so you may make multiple calls without blocking the runtime library itself. However dealing with the associate blocking on the client side is a matter for your particular service and language stack. This issue is described further in xref.

