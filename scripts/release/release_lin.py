# Script to release on OSX
# this is executed from the root toolkit src dir

import os
import requests
from uritemplate import expand

import sh
from sh import git, make, pyinstaller

root_dir = os.getcwd()
user = "mands"
password = 'abc' # input("Enter password for github user {}: ".format(user))

make.clean()

try:
    # update code to latest tag
    git.reset("--hard")
    git.clean("-f", "-d")
    git.pull("origin", "master", "--tags")
    version = str(git.describe("--abbrev=0", "--tags")).strip()
    git.checkout(version)

    # run pyinstaller
    sh.mkdir("-p", "./scripts/release")
    sh.cp("../../toolkit/stackhut.py", "./")
    sh.cp("../../toolkit/scripts/release/stackhut_lin.spec", "./scripts/release/")

    pyinstaller('-y', '--clean', "./scripts/release/stackhut_lin.spec")

    # TODO - run tests on bin version...

    # build tarball
    rel_name = "stackhut-{}-linux-x86_64.txz".format(version)
    os.chdir("dist")
    sh.tar("-cJf", rel_name, "./stackhut")

    # upload to github releases
    header = {'Accept': 'application/vnd.github.v3+json'}

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

        upload_header = {'Accept': 'application/vnd.github.v3+json',
                         'Content-Type': 'application/octet-stream'
                         }

        r = requests.post(upload_url, headers=upload_header, auth=(user, password), data=rel_file)
        r.raise_for_status()

    print("Uploaded linux64 binary release - {}".format(version))

finally:
    os.chdir(root_dir)
    make.clean()

exit(0)
