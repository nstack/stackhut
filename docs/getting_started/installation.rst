Platform Installation
=====================

StackHut is comprised of 2 major parts - the hosting platform full of live APIs that you can call from your code, and the development platform with which to create your own live APIs.

To use a StackHut service from within your own code you just need to make a JSON-RPC HTTP request - as described in :ref:`tutorial_create`.

.. There are a few parts to StackHut - the website and hosting platform from which you can call services in your own code, the command line tool, and the library of functions you an use when writing your services.

This page describes installing the command line tool so you can rapidly develop, test, and deploy your services rapidly from your computer to the StackHut platform.
The StackHut command-line tool (StackHut CLI) is written in Python and requires a few dependencies to get going.


General Requirements
--------------------

* Python 3.4
* Docker
* Barrister RPC system (Python 2 package)

Linux Install Instructions
--------------------------

* Install Docker, Python 3 and Python 2 (and pip installer)from OS repository, e.g.

  * ``sudo dnf install docker python3 python3-pip python python-pip``
  * or ``sudo apt-get install docker python3 python3-pip python python-pip``

* Install Barrister RPC system (currently uses Python 2)
  
  * ``sudo pip2 install barrister``
  
* Install StackHut CLI

  * ``sudo pip3 install stackhut``

*Note* - by default ``pip`` installs globally and requires root access, however you can pass the ``--user`` flag to install to the user ``$HOME`` directory, e.g. ``pip3 install --user stackhut``


OSX Install Instructions
------------------------

* Install Docker

  * We have tested StackHut using `Boot2docker <http://boot2docker.io/>`_ and recommend this approach
  
* Install Python 3

  * Install either direct from <https://www.python.org/downloads/mac-osx/> or via `Brew <http://brew.sh/>_` 


* Install Barrister RPC System (currently uses Python 2)

  * Get Pip for Python 2
    
    *  ``sudo easy_install pip``
  
  * ``sudo pip install barrister``

* Install StackHut CLI

  * ``sudo pip3 install stackhut``

*Note* - again similar to Linux ``pip`` installs globally and requires root access. You can again using the ``--user`` flag to install to the user ``$HOME`` directory, however on OSX you'll have to manually add the binary to your PATH.

*Note* - remember to run ``boot2docker up`` to startup Docker before using the StackHut CLI.


Windows Install Instructions
----------------------------

We haven't tested StackHut on Windows yet, however the code-base is cross-platform and it should work as long as you install the dependencies. Similar to OSX you'll have to install  `Boot2docker <http://boot2docker.io/>`_ and obtain both Python 2 and 3 before ``pip`` installing StackHut.

Please let us know how it goes, we'd love to get Windows support working.

Upgrading
---------

Development on the StackHut CLI moves pretty fast, so if you find a bug it may be worth updating first before reporting an issue. Using pip this is easy

* ``pip3 install --upgrade stackhut``

