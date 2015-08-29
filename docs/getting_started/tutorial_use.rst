.. _tutorial_use:

Tutorial - Using a Service
==========================

In this tutorial presents a quick overview of how to access a StackHut service from within your application, whether it is written in Python, client/server-side JS, Ruby, .NET, and more. 

.. The best way to start is to watch the following screen-cast that walks you through using a StackHut service from the command-line.

.. .. raw:: html

.. <script type="text/javascript" src="https://asciinema.org/a/23990.js" id="asciicast-23990" async></script>

Selecting a service
-------------------

You can find all kinds of services, for instance, video encoding, compression, compilation, web scraping, and more, hosted at the `StackHut repository <https://stackhut.com/#/services>`_. 

Sercices are prefixed by their author, such as ``stackhut/demo-python``. We can view the documentation and API for this service on its `homepage <https://stackhut.com/#/u/stackhut/demo-python>`_, it has 2 methods, ``add`` and ``multiply``. 

For this tutorial we'll use the ``demo-python`` service created in :ref:`tutorial_create` (if you didn't create one you can use ``stackhut/demo-python`` instead).


Access a service directly
-------------------------

All StackHut services can be accessed and consumed via a direct HTTP POST request. On receiving a request, the StackHut host platform will route the request on demand to the required service to  complete it. 
The whole StackHut infrastructure is abstracted away from your service code, from its point of view it's simply executing a function call.

Thanks for reading this tutorial - you can find more information on calling services, for instance using the upcoming StackHut client-side libraries, in :ref:`usage_your_code`.

Want to develop a StackHut cloud API or fork an existing service? Read :ref:`tutorial_create` to get going - we can't wait to see what you come up with.
