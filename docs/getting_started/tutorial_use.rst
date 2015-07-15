Tutorial - Using a Service
==========================

This section repreesents a quick overview of how to access a StackHut service from within your application, be it written in Python, client-side/server-side JS, Ruby, .NET and more. The best way to start is to watch the following screen-cast that take us through setting up a simple, Python-based StackHut service.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/Y8vBQCgA944" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>


Selecting a service
-------------------

You can find all manner of services, from video encoding, to complression, onine-compilation, web scraping, and more, on the StackHut repository (ref). Even better, develop or fork an exiting dservice using the creating a service guide. (xref)


.. Login into StackHut
.. -------------------
.. __Coming Soon__ - all services are curently free to use and can be accessed anonymously.


Access a service directly
-------------------------

All StackHut services can be accessed and consumed via a direct HTTP POST request. On receving a request, the StackHut host platform will spin-up a container on demand with the required service and cmoplete your request. The whole StackHut infrastructure is abstrqcvtted away from the service code which is simply respnding to a fucntion call. Because of this we have decied to expose all services via JSON-RPC transported over a HTTP(S) POST request.

As a result any StackHut service can easily be consumed by construuted a JSON-RPC request in any language - thankfully JSON-RPC is a very simple protocol and this is much simpler than it sounds!

Request::

    {
        "serviceName" : "example-python",
        "req" : {
            "method" : "helloName",
            "params" : ["StackHut"]        
            "id" : 1
        } 
    }    

In the above request, we call the method ``helloName`` in the StackHut service ``example-python`` with a single parameter ``StackHut``. 
``Params`` is a JSON list that contain any JSON types, i.e. flaots, strings, lists and objects. The types expected by the method are defined by the serice and viewable on API section of the service page on the StackHut website. The types of the request are checked and an error will be returned if they do not match.
There is also an optional ``id`` element that will be added automatically if not present in the request. 


We can make the above call by simply sending it as a HTTP POST request, with content-type ``application/json`` to ``https://api.stackhut.com/run``. Let's save the above example as ``test_request.json`` and show this by using the great command-line tool ``http`` (www)::

    http POST https://api.stackhut.com/run < ./test_request.json 

The request will be made and you'll receive a bunch of output in your terminal including the responce body, which should be similar to the following,


Responce::

    {
        "response": {
            "jsonrpc": "2.0", 
            "id": 1 
            "result": "Hello, StackHut! :)"
        }, 
        "taskId": "71c530bb-8875-4143-8932-2e75ddaeddbd"
    }

The above sample shows a successful request object. The ``response`` object is a JSON-RPC response, where the data we're after can be found in the ``result`` field - in this case a string containing the text ``Hello, StackHut :)``. The ``id`` element is also present, to aid linking requests to repsonse if needed, and there is a top-level ``taskId`` element to uniquely represent this particular service request.

Let's say we call the same serice method ``helloName`` but with a number, rather than a string a expected. Let's edit the ``test_request.json`` and see::

    {
        "serviceName" : "example-python",
        "req" : {
            "method" : "helloName",
            "params" : [10],
            "id" : 1
        } 
    }    

    http POST https://api.stackhut.com/run < ./test_request.json 

    {
        "response": {
            "error": {
                "code": -32000, 
                "data": {
                    "exception": "object of type 'int' has no len()"
                }, 
                "message": "Server error. Check logs for details."
            }, 
            "id": "585e5ec6-f8bd-495a-9256-c8a69563c3aa", 
            "jsonrpc": "2.0"
        }, 
        "taskId": "b74579b0-7ce2-4522-824a-3733cd13176e"
    }

As before we receive a JSON-RPC repsonse object, however this time the HTTP status code is xx and  the ``result`` field has been replaced with an ``error`` field, contatining an object with an error code, a human readable text message, and an optional ``data`` object containing further information. You can use this information within your application to handle the error as required. (*NOTE* - the error codes are defined by the JSON-RPC spec and can be found here (ref)).



Access a service using client-side libraries
--------------------------------------------

Client-side libraries are provided/under-development for the following platforms

 * Python
 * Ruby
 * JavaScript
 * PHP
 * Java/JVM (coming soon)
 * C#/.NET (coming soon)




Usage Notes
-----------

Files
^^^^^

Batching
^^^^^^^^

State
^^^^^





