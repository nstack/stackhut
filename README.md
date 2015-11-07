# StackHut Toolkit
## Deploy classes as Microservices

[![image](https://img.shields.io/pypi/v/stackhut.svg)](https://pypi.python.org/pypi/stackhut)

`stackhut` is a platform to develop and deploy microservices without writing any server-logic. It takes a regular class (in Python or JavaScript for now), a YAML file describing your stack, and deploys a microservice whose functions can be called natively in other languages, or through REST.

The `stackhut` command tool provides CLI functionality into creating, running, and deploying StackHut images. 

Available to download in both source and binary form for Linux and OSX.

More info found on the [main StackHut repo](https://github.com/StackHut/StackHut), download the toolkit from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases).

* Homepage: https://www.stackhut.com
* User Manual & Docs: https://stackhut.readthedocs.org
* Free software: Apache license

---
## Installing the toolkit

All releases found on this repo's [release page](https://github.com/StackHut/stackhut-toolkit/releases).

### Binary/Standalone Install

You can download a standalone executable for Linux and OSX. 
 * On OSX there are two binary install methods:
    * Using brew - `brew install stackhut/stackhut/toolkit` (a 3rd-party tap you can also upgrade with `brew upgrade stackhut/stackhut/toolkit` - make sure you have an up-to-date brew with `brew update`)
    * Download and run the latest `.pkg` file from the [releases page](https://github.com/StackHut/stackhut-toolkit/releases) (standalone that you can remove simply by `sudo rm -rf /usr/local/bin/stackhut /usr/local/opt/stackhut`)
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

---

## Contributing

Contributions are welcome, and greatly appreciated! Every little bit helps us approach the NoOps dream, and credit will always be given :)

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for more info.
