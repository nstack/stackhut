# StackHut Platform (Main Repo)
## Deploy classes as Microservices

StackHut is a plaftorm for simply devloping your backend code and deploying it to the cooud as microservices that you can call from you front-end web and mobile applications.

This is the main repo for StackHut, holding the main documention and tracking issues. It serves as a central point to coordinate development efforts.

Happy hacking! :)

## Repos

* [StackHut CLI Toolkit](https://github.com/StackHut/stackhut-toolkit) - Use this to develop and test your services locally and then deploy them to the cloud

## Useful Links

* [Issues (on waffle.io Kanban Board)](http://waffle.io/StackHut/StackHut)
* [Issues (on GitHub)](https://github.com/StackHut/StackHut/issues)
* [Wiki](https://github.com/StackHut/StackHut/wiki)
* [User Manual / Main Docs](http://stackhut.readthedocs.org)

[![Stories in Ready](https://badge.waffle.io/StackHut/StackHut.svg?label=ready&title=Ready)](http://waffle.io/StackHut/StackHut)

## Getting started

## Installing the toolkit

### [Get the latest release now from GitHub](https://github.com/StackHut/stackhut-toolkit/releases)

### Binary/Standalone Install

We now have a new build process that packages up toolkit with all dependent libraries into a standalone executable (including an embedded Python 3) for Linux and OSX. It's now much easier for users to quickly get started using our binary installs for Linux and OSX,
 * On OSX there are several binary install methods,
    * Using brew - `brew install stackhut/stackhut/toolkit`
    * Download and run the latest `.pkg` file from the releases page
    * Download and unpack the portable `.txz`-archive
 * Linux
    * Download and unpack the portable `.txz`-archive

### Source Install

Source builds are always available using `pip` and are the recommended way to install if you already have Python 3,

 * On OSX, `brew install python3; pip3 install stackhut --user` or install Python3 from elsewhere, and run `pip3 install stackhut --user` again,
 * On Linux, install Python 3 from you distribution (it's installed by default on newer distros) and `pip3 install stackhut --user`.

_Note_ - StackHut requires [Docker](www.docker.com) to be installed  - on OSX/Windows download [Docker Toolbox](https://www.docker.com/docker-toolbox) and on Linux we recommend using your distro version.
