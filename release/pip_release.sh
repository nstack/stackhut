#!/usr/bin/env bash
# Start a new pip/source release

set -e

make clean
make lint

# TODO - setup tests properly
# test locally
# make test

# test in venv
# make test-all

bumpversion $1
make release
make clean

