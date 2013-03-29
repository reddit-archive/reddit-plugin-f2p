#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='reddit_f2p',
    description='reddit free to play mode',
    version='0.1',
    author='reddit',
    author_email='',
    packages=find_packages(),
    install_requires=[
        'r2',
        'python-openid',
    ],
    entry_points={
        'r2.plugin':
            ['f2p = reddit_f2p:FreeToPlay']
    },
    package_data={
        'reddit_f2p': ['data/*.json'],
    },
    include_package_data=True,
    zip_safe=False,
)
