# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='kubedifflib',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.0',

    description='Library for diffing Kubernetes configs',
    long_description="",

    # The project's main homepage.
    url='https://github.com/weaveworks/kubediff',

    # Author details
    author='Weaveworks',
    author_email='help@weave.works',

    # Choose your license
    license='MIT',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=["kubedifflib"],
)
