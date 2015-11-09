.. _getting_started_installation:

Platform Installation
=====================

This page describes installing the command-line StackHut Toolkit so you can rapidly develop, test, and deploy your services.

All releases can be found on the stackhut repo's `release page <https://github.com/stackhut/stackhut/releases>`_.

Binary/Standalone Install
-------------------------

You can download a standalone executable for Linux and OSX. 

OSX
^^^

On OSX there are three binary install methods:

    *   Use brew,

        ``brew install stackhut/stackhut/toolkit``

        This is a 3rd-party tap from which you can upgrade using ``brew upgrade stackhut/stackhut/toolkit``,

        .. note:: Make sure you have an up-to-date brew with ``brew update``.

    *   OR - download and run the latest ``.pkg`` file from the `release page <https://github.com/stackhut/stackhut/releases>`_. This is a standalone package you can remove with ``sudo rm -rf /usr/local/bin/stackhut /usr/local/opt/stackhut``,

    *   OR - download and unpack the portable ``.txz``-archive from the `release page <https://github.com/stackhut/stackhut/releases>`_.

Linux
^^^^^

    * Download and unpack the portable ``.txz``-archive from the `release page <https://github.com/stackhut/stackhut/releases>`_

Source Install
--------------

Alternatively, source builds are always available using ``pip`` and are the recommended way to install if you already have Python 3:

OSX
^^^

    ``brew install python3; pip3 install stackhut --user`` (or just ``pip3 install stackhut --user`` if you already have Python 3),

Linux
^^^^^

    ``pip3 install stackhut --user`` (you may need to install Python 3 first - it's installed by default on newer distros).

.. note:: Using the ``--user`` flag will install in the user's ``$HOME`` directory. However on OSX you'll have to manually add ``~/Libraries/Python/3.4/bin`` to your ``$PATH``. Omitting the ``--user`` flag it will require ``sudo`` and install globally instead.


Developer Install
-----------------

Want to run the latest code from Git? Awesome! 

    #) ``git clone git@github.com:stackhut/stackhut.git`` (Clone the repo)
    #) ``cd stackhut``
    #) ``pip3 install -r ./requirements.txt`` (Install the dependencies)
    #) ``python3 ./setup.py develop --user`` 

.. note:: You may need to re-run the last command occasionally after updating from ``git``.


Install Notes
-------------


Requirements
^^^^^^^^^^^^

    * `Docker <https://www.docker.com/>`_ to develop and test services locally. On OSX/Windows download `Docker Toolbox <https://www.docker.com/docker-toolbox>`_ and on Linux we recommend using your distro version.

.. note:: Currently we support Linux and OSX - with Windows support launching shortly.

Upgrading
^^^^^^^^^

Development on the StackHut Toolkit moves pretty fast, so if you find a bug it may be worth updating first before reporting an issue. On the binary releases it's just as easy as re-installing the latest package. For the source releases, just run ``pip3 install --upgrade stackhut``.


Next Steps
----------

An in-depth tutorial showing how to create, call and deploy a simple service can be found in the :ref:`getting_started_tutorial`.


