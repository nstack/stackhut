# StackHut Platform Main Repo
## Deploy classes as Microservices

StackHut is a plaftorm for simply devloping your backend code and deploying it to the cooud as microservices that you can call from you front-end web and mobile applications.

This is the main repo for StackHut, holding the main documention and tracking issues. It serves as a central point to coordinate development efforts.

## Main Repos

## Where to go

* [Issues (on waffle.io Kanban Board)](http://waffle.io/StackHut/StackHut)
* [Issues (on GitHub)](https://github.com/StackHut/StackHut/issues)
* [Wiki](https://github.com/StackHut/StackHut/wiki)
* [Main Documentation](http://stackhut.readthedocs.org)

Happy hacking! :)

[![Stories in Ready](https://badge.waffle.io/StackHut/StackHut.svg?label=ready&title=Ready)](http://waffle.io/StackHut/StackHut)

## Getting started

## Installing the toolkit

[Get the latest release now from GitHub](https://github.com/StackHut/stackhut-toolkit/releases)

We now have a new build process that packages up toolkit with all dependent libraries into a standalone executable (including an embedded Python 3) for Linux and OSX. This will lead to much more reproducible issues, as these users will be running the same versions of Python and support libraries, whereas previously Python and OpenSSL interaction on OSX was a big source of issues in particular,

As a result, it's now much easier for users to quickly get started using our binary installs for Linux and OSX,
 * On OSX there are several binary install methods,
    * `brew install stackhut/stackhut/toolkit` (a 3rd-party tap that you can also upgrade using `brew upgrade stackhut/stackhut/toolkit`)
    * Download the `.pkg` file from the releases page (fully standalone that upgrades simply by installing a newer version)
    * A `.txz`-archive you can unpack and run/link from anywhere
 * Linux
    * A `.txz`-archive you can unpack and run/link from anywhere

* Many many smaller bugfixes and better error supporting (thanks to @collingreen for these!)

Source builds are always available using `pip` and are the recommended way to install if you already have Python 3,

 * On OSX, `brew install python3; pip3 install stackhut --user` or install Python3 from elsewhere, and run `pip3 install stackhut --user` again,
 * On Linux, install Python 3 from you distribution (it's installed by default on newer distros) and `pip3 install stackhut --user`.

Note - [Docker](www.docker.com) is now a requirement - on Linux we recommend using your distro version, and on OSX/Windows use [Docker Toolbox](https://www.docker.com/docker-toolbox).



