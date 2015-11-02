#!/usr/bin/env bash
# Start a new pip/source release
set -e

if [[ $# -eq 0 ]] ; then
    echo 'Run with new bumpversion {major/minor/patch}'
    exit 0
fi

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

