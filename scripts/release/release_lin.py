# Script to release on OSX
# this is executed from the root toolkit src dir

import os
import requests
from uritemplate import expand

import sh
from sh import git, make, pyinstaller

root_dir = os.getcwd()
user = "mands"
password = input("Enter password for github user {}: ".format(user))

make.clean()

try:
    # update code to latest tag
    git.reset("--hard")
    git.clean("-f", "-d")
    git.pull("--tags")
    version = git.describe("--abbrev=0", "--tags")
    git.checkout(version)

    # run pyinstaller
    pyinstaller('-y', '--clean', "./scripts/release/stackhut_lin.spec")

    # TODO - run tests on bin version...

    # build tarball
    rel_name = "stackhut-{}-linux-x86_64.txz".format(version)
    os.chdir("dist")
    sh.tar("-cJf", rel_name, "./stackhut")

    # upload to github releases
    header = {'Accept': 'application/vnd.github.v3+json'}

    "GET /repos/:owner/:repo/releases/:id"

    # get the release info
    r = requests.get("https://api.github.com/repos/StackHut/stackhut-toolkit/releases/tags/{}".format(version),
                     headers=header)

    if r.status_code == requests.codes.ok:
        upload_url = r.json()["upload_url"]
    else:
        r.raise_for_status()

    # upload the asset
    with open(rel_name, 'rb') as rel_file:
        upload_url = expand(upload_url, {"name": rel_name})
        r = requests.post(upload_url, headers=header, auth=(user, password), data=rel_file)
        r.raise_for_status()

finally:
    os.chdir(root_dir)
    make.clean()


print("Uploaded linux64 binary release - {}".format(version))
