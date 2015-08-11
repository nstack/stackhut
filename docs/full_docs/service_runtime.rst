StackHut Runtime Library
========================

When running a StackHut service there are many common functions you may wish to perform and interact with the host environment, be t running locally on your machine or when hosted on the StackHut platform.

In this section we describe the StackHut library full of common functionality yo can use in your service to make the process a lot easier.


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


put_file
^^^^^^^^

.. code-block:: python

    stackhut.put_file(fname, make_public)

This function uploads the file referenced by ``fname`` in the service working directory to cloud storage (S3) where it can be downloaded by yourself or others.
``make_public`` is an optional boolean that triggers whether the uploaded file is made accessible as a public URL, by default this is True.

Returns the URL of the uploaded file.


run_command
^^^^^^^^^^^

.. code-block:: python

    stackhut.run_command(cmd, stdin)

Runs the command specified by ``cmd`` as an external process and waits for completeion. ``stdin`` is an optional string that, when specified, will be used as the STDIN to the command.

Function waits for the subprocess to complete and returns STDOUT as a string.



General Notes
-------------

All functions are blocking by default, however each call runs in a separate thread so you may make multiple calls without blocking the runtime library itself. However dealing with the associate blocks on the client side is a matter for your particular service and language stack.


Language Specific Notes
-----------------------

Python (2 and 3)
^^^^^^^^^^^^^^^^

As mentioned above all calls to the server are blocking (although handled in multiple threads).

There are two methods to deal with this on the Python side.
Firstly Python has a good threading library that works very well when used with blocking IO calls. 
Secondly Python 3.5 will introduce ``async`` and ``await`` type-functionality as seen in C# that can be used to interleave these calls.


Node.js / ES6
^^^^^^^^^^^^^

The Node.js story is more complex as StackHut is primarily a request->response system exhibited through functions as entrypoints. This conflicts with the callback-based model of Node at present.

However things are looking much better with both ES6 and ES7 on the horizon.
StackHut's Node support is based on the latest io.js with support for ES6, and promises in particular (`this <http://www.html5rocks.com/en/tutorials/es6/promises/>`_ is a good intro).

.. note:: We currently utilise `io.js v3 <https://iojs.org/>`_ to provide a compatible version of Node.js with ES6 features. These projects have now remerged and we will follow io.js in moving to the Node.js project accordingly.

The StackHut runtime is promise-based on Node, with each call returning a promise than resolves on completion.

Similarly the main entrypoints to a service are also promise-based. The StackHut runner expects each entrypoint to return a promise that resolves on completion of the service request.
This gives you two choices when implementing a service function depending on if it's a synchronous or a callback-based asynchronous service.

**Synchronous Services**

Write your function as normal and simply wrap the result in a Promise.resolve().

.. code-block:: js

    add(x, y) {
        let res = x + y;
        return Promise.resolve(res);
    }

**Asynchronous Services**

Wrap your service block in a single promise that is returned to the system. Within this block write your normal code and call with ``resolve`` or ``reject`` as required on completion. This method interacts nicely with new promise-based and legacy callback-based async code.

.. code-block:: js

    asyncAdd(x, y) {
        return new Promise(function(resolve, reject) {
            someAsyncCall(x, y)
            .then(function (res) {
                resolve(res);
            
            })   
        })
    }


.. note:: As we support regular ES6 with node packages, feel free to add any helpers libraries to your ``package.json`` to ease writing async services, i.e. `co <https://github.com/tj/co>`_.

Similar to Python 3.5, ``async`` and ``await`` are coming with ES7 and will provide a better model for async code that will be easier to integrate with StackHut.


