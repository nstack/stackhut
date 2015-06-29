import os
from setuptools import setup, find_packages

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='stackhut',
    version='0.1.0',
    description="Run your software in the cloud",
    long_description=(read('README.rst') + '\n\n' +
                      read('HISTORY.rst') + '\n\n' +
                      read('AUTHORS.rst')),
    url='https://github.com/stackhut/stackhut-app',
    license='MIT',
    author='Mandeep Gill',
    author_email='mandeep@stackhut.com',
    py_modules=find_packages(exclude=['res']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'stackhut = stackhut.__main__:main',
        ],
    },

    install_requires=open('requirements.txt').read().splitlines(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        'Topic :: Software Development',
        'Private :: Do Not Upload', # hack to force invalid package for upload

    ],
)
