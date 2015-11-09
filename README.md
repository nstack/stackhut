# StackHut Platform
## Deploy classes as Microservices

[![image](https://img.shields.io/pypi/v/stackhut.svg)](https://pypi.python.org/pypi/stackhut)

StackHut is a platform to develop and deploy microservices without writing any server-logic. It takes a regular class (in Python or JavaScript for now), a YAML file describing your stack, and deploys a microservice whose functions can be called natively in other languages, or through REST.

StackHut is pure Software Defined Infrastructure, and abstracts away web-frameworks, servers, and infrastructure entirely.

The `stackhut` command tool provides CLI functionality into creating, running, and deploying StackHut images. 

Happy hacking! :)

* Homepage: [https://www.stackhut.com]()
* Documentation: [https://stackhut.readthedocs.org]()
* Free software: Apache license

Available to download in both source and binary form for Linux and OSX. Free software under the Apache license.

---

## Other Repos
TODO


## Useful Links

* Homepage: https://www.stackhut.com
* User Manual & Docs: https://stackhut.readthedocs.org
* [GitHub Issues](https://github.com/stackHut/stackHut/issues)
* [GitHub Wiki](https://github.com/stackhut/stackhut/wiki)

---

# Getting started
## Installing the toolkit

All releases found on this repo's [release page](https://github.com/stackhut/stackhut/releases).

### Binary/Standalone Install

You can download a standalone executable for Linux and OSX. 
 * On OSX there are three binary install methods:
    * Using brew - `brew install stackhut/stackhut/toolkit` (a 3rd-party tap you can also upgrade with `brew upgrade stackhut/stackhut/toolkit` - make sure you have an up-to-date brew with `brew update`)
    * Download and run the latest `.pkg` file from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases) (standalone that you can remove simply by `sudo rm -rf /usr/local/bin/stackhut /usr/local/opt/stackhut`)
    * Download and unpack the portable `.txz`-archive from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases)
 * Linux
    * Download and unpack the portable `.txz`-archive from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases)

### Source Install

Alternatively, source builds are always available using `pip` and are the recommended way to install if you already have Python 3:

 * On OSX, `brew install python3; pip3 install stackhut --user` (or just `pip3 install stackhut --user` if you already have Python 3),
 * On Linux, `pip3 install stackhut --user` (you may need to install Python 3 first - it's installed by default on newer distros).

_Note_ - StackHut requires [Docker](www.docker.com) to be installed  - on OSX/Windows download [Docker Toolbox](https://www.docker.com/docker-toolbox) and on Linux we recommend using your distro version.

### Developer Install

Want to run the latest code from Git? Awesome! 
* clone this repo - `git clone git@github.com:StackHut/stackhut-toolkit.git`
* `cd stackhut-toolkit`
* `pip3 install -r ./requirements.txt`
* `python3 ./setup.py develop --user` (you may need to re-run this command occasionally after updating from git)



### Follow the tutorial

An in-depth tutorial showing how to create, call and deploy a simple service can be found in the [user manual](http://docs.stackhut.com/getting_started/tutorial.html).

---

## Contributing

Contributions are welcome, and greatly appreciated! Every little bit helps us approach the NoOps dream, and credit will always be given :)

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for more info.
