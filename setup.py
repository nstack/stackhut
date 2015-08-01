#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup
import os

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

here = os.path.abspath(os.path.dirname(__file__))

# put package test requirements here
requirements = [
    "wheel",
    "sh",
    "boto",
    "requests",
    "jinja2",
    "pyconfig",
    "PyYaml",
    "redis",
    "multipledispatch",
    "werkzeug",
    "json-rpc",
    "docker-py",
    "arrow",
]

# conditional requirements for py 2 or 3
# NOTE - switch to extra_require at some point to build uni-wheel
# if sys.version_info[0] == 2:
#     requirements += ['common.barrister']
# else:
#     requirements += []

# put package test requirements here
test_requirements = [

]

setup(
    name='stackhut',
    version='0.3.21',
    description="Run your software in the cloud",
    long_description=(read('README.rst') + '\n\n' +
                      read('HISTORY.rst').replace('.. :changelog:', '') + '\n\n' +
                      read('AUTHORS.rst')),
    license='Apache',
    author="Mandeep Gill  Leo Anthias",
    author_email='mandeep@stackhut.com',
    url='https://github.com/stackhut/stackhut-tool',
    # download_url = 'https://github.com/stackhut/stackhut-tool/tarball/0.1.0'
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", ""]),
    # package_dir={'stackhut-tool':
    #              'stackhut-tool'},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'stackhut = stackhut.__main__:main',
        ],
    },
    install_requires=requirements,
    zip_safe=False,
    test_suite='tests',
    tests_require=test_requirements,

    keywords='stackhut',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        #'Private :: Do Not Upload',  # hack to force invalid package for upload

    ],
)
