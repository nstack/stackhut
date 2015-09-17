.. _examples_index:

********
Examples
********

This section contains a list of more complex services we've built using StackHut. They are all `open-source <http://www.github.com/StackHut>`_ and each project has detailed documentation describing the service's creation.

Each service showcases different features/techniques that can be used to build StackHut services for your application.


PDF Tools
=========

* Documented Source - http://www.github.com/StackHut/pdf-tools
* Service Homepage - http://www.stackhut.com/#/u/stackhut/pdf-tools

``pdf-tools`` is a StackHut service that converts PDFs to various formats, including to text and multiple image formats. This Python-based service demonstrates the following features,

* File manipulation
* OS dependencies
* *Shelling*-out to binary/command-line tools from within a service

<!--

Image Process
=============

* Documented Source - http://www.github.com/StackHut/image-process
* Service Homepage - http://www.stackhut.com/#/u/stackhut/image-process

``image-process`` is a StackHut service that performs various image manipulation tasks and can be used to generate *memes*. This Python-based service demonstrates the following features,

* File manipulation
* OS dependencies
* Embedding resource files within a service

-->
Web Tools
=========

* Documented Source - http://www.github.com/StackHut/web-tools
* Service Homepage - http://www.stackhut.com/#/u/stackhut/web-tools

``web-tools`` is a StackHut service that performs several web-developer related functions. This service wraps up the `PhantomJS <http://phantomjs.org/>`_ and `Selenium <http://www.seleniumhq.org/>`_ libraries to provide a headless web-browser. 

It uses these to provide a screen-shotting service that works for JS-heavy sites but will be expanded in the future. This Python-based service demonstrates the following features,

* OS dependencies
* Embedding resource files within a service
* Custom binaries and dependencies
* Running arbitrary `Docker <http://www.docker.com>`_ build commands

