.. _getting_started_installation:

Platform Installation
=====================

This page describes installing the command-line StackHut Toolkit so you can rapidly develop, test, and deploy your services.

Quick Install
-------------

Requirements
^^^^^^^^^^^^

* `Python 3.4 <http://www.python.org>`_
* Unix-based OS (tested on Linux and OSX, others should work)

.. note:: We are adding Windows support soon. Email us at hi@stackhut.com if this is a blocker so we can plan as needed.

Install Steps
^^^^^^^^^^^^^

#. Install above requirements
#. Install StackHut - ``sudo pip3 install stackhut``
#. There is no Step 3 - but try out the walkthrough in :ref:`tutorial_create`

Upgrading
^^^^^^^^^

Development on the StackHut Toolkit moves pretty fast, so if you find a bug it may be worth updating first before reporting an issue. Using ``pip`` this is easy

* ``sudo pip3 install --upgrade stackhut``


Linux Install Instructions
--------------------------

* Install and Python 3 (including the Pip installer) from your OS repository, e.g.

  * Fedora - ``sudo dnf install python3 python3-pip``
  * Debian/Ubuntu - ``sudo apt-get install python3 python3-pip``
  
* Install the StackHut Toolkit

  * ``sudo pip3 install stackhut``

.. note:: By default ``pip`` installs globally and requires root access, however passing the ``--user`` flag will install to the user's ``$HOME`` directory, e.g. ``pip3 install --user stackhut``


OSX Install Instructions
------------------------

* Install Python 3 using `Brew <http://brew.sh/>`_
  
  * ``brew install python3``

* Install StackHut CLI

  * ``sudo pip3 install stackhut``

.. note:: As with Linux, ``pip`` installs globally and requires root access. You can again using the ``--user`` flag to install to the user ``$HOME`` directory, however on OSX you'll have to manually add ``~/Libraries/Python/3.4/bin`` to your ``$PATH``.

