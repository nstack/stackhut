# StackHut Platform (Central Repo)
## Deploy classes as Microservices

StackHut is a platform to develop and deploy microservices without writing any server-logic. It takes a regular class (in Python or JavaScript for now), a YAML file describing your stack, and deploys a microservice whose functions can be called natively in other languages, or through REST.

StackHut is pure Software Defined Infrastructure, and abstracts away web-frameworks, servers, and infrastructure entirely.

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

All toolkit releases can be found on the toolkit's repo [releases page](https://github.com/StackHut/stackhut-toolkit/releases).

### Binary/Standalone Install

We now have a new build process that packages up toolkit with all dependent libraries into a standalone executable (including an embedded Python 3) for Linux and OSX. It's now much easier for users to quickly get started using our binary installs for Linux and OSX,
 * On OSX there are several binary install methods,
    * Using brew - `brew install stackhut/stackhut/toolkit` (a 3rd-party tap you can also upgrade with `brew upgrade stackhut/stackhut/toolkit` - make sure you have an up-to-date brew with `brew update`)
    * Download and run the latest `.pkg` file from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases) (standalone that you can remove simply by `sudo rm -rf /usr/local/bin/stackhut /usr/local/opt/stackhut`)
    * Download and unpack the portable `.txz`-archive from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases)
 * Linux
    * Download and unpack the portable `.txz`-archive from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases)

### Source Install

Source builds are always available using `pip` and are the recommended way to install if you already have Python 3,

 * On OSX, `brew install python3; pip3 install stackhut --user` (or just `pip3 install stackhut --user` if you already have Python 3),
 * On Linux, `pip3 install stackhut --user` (you may need to install Python 3 first - it's installed by default on newer distros).

_Note_ - StackHut requires [Docker](www.docker.com) to be installed  - on OSX/Windows download [Docker Toolbox](https://www.docker.com/docker-toolbox) and on Linux we recommend using your distro version.

### Follow the tutorial

An in-depth tutorial showing how to create, call and deploy a simple service can be found in the [user manual](http://docs.stackhut.com/getting_started/tutorial.html).

