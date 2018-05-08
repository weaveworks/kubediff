# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

setup(
    name='kubedifflib',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.0',
    description='Library for diffing Kubernetes configs',
    long_description="",
    url='https://github.com/weaveworks/kubediff',
    author='Weaveworks',
    author_email='help@weave.works',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=['PyYAML', 'attrs', 'future'],
    scripts=['kubediff', 'compare-images'],
    setup_requires=['pytest-runner',],
    tests_require=['pytest',],
)
