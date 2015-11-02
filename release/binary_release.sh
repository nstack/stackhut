#!/usr/bin/env bash
# Start a new release from scratch
# run from platform specific release dir

# wipe state
rm -rf ./src-release ./venv-release

# setup the virtualenv
virtualenv ./venv-release
. ./venv-release/bin/activate

# get the source and install deps
git clone git@github.com:StackHut/stackhut-toolkit.git ./src-release
cd src-release
pip3 install -r ./requirements.txt

# build and deploy the release
pip3 install -r ./release/rel_requirements.txt

if [[ "$OSTYPE" == "linux-gnu" ]]; then
        stackhut-scripts -v release-linux
elif [[ "$OSTYPE" == "darwin"* ]]; then
        stackhut-scripts -v release-osx
elif [[ "$OSTYPE" == "msys" ]]; then
        stackhut-scripts -v release-win
else
        # Unknown.
        echo "Unknown OS - $OSTYPE"
fi

# Done
echo "Done!"
