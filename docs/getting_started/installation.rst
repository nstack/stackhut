.. _installation:

Platform Installation
=====================

This page describes installing the command-line StackHut Toolkit so you can rapidly develop, test, and deploy your services.

Quick Instructions
------------------

Requirements
^^^^^^^^^^^^

* `Python 3.4 <http://www.python.org>`_

Install Steps
^^^^^^^^^^^^^

#. Install above requirements
#. Install StackHut - ``sudo pip3 install stackhut``
#. There is no Step 3 - but try out the walkthrough in :ref:`tutorial_create`

.. Having installed the Toolkit you can go through the walk-through in :ref:`tutorial_create`.

.. The StackHut Toolkit is written in Python 3 and requires a few dependencies to get going.


Linux Install Instructions
--------------------------

* Install Docker and Python 3 (including the Pip installer) from your OS repository, e.g.

  * Fedora - ``sudo dnf install python3 python3-pip``
  * Debian/Ubuntu - ``sudo apt-get install python3 python3-pip``
  
* Install the StackHut Toolkit

  * ``sudo pip3 install stackhut``

.. note:: By default ``pip`` installs globally and requires root access, however passing the ``--user`` flag will install to the user's' ``$HOME`` directory, e.g. ``pip3 install --user stackhut``


OSX Install Instructions
------------------------

* Install Python 3 using `Brew <http://brew.sh/>`_
  
  * ``brew install python3``

* Install StackHut CLI

  * ``sudo pip3 install stackhut``

.. note:: As with Linux, ``pip`` installs globally and requires root access. You can again using the ``--user`` flag to install to the user ``$HOME`` directory, however on OSX you'll have to manually add the binary to your PATH.


Windows Install Instructions
----------------------------

We are adding Windows support soon. Email us at hi@stackhut.com, if it's a blocker for you.

Upgrading
---------

Development on the StackHut Toolkit moves pretty fast, so if you find a bug it may be worth updating first before reporting an issue. Using ``pip`` this is easy

* ``pip3 install --upgrade stackhut``

