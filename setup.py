#!/usr/bin/env python

import setuptools

import sfrtvctl

setuptools.setup(
    name=sfrtvctl.__title__,
    version=sfrtvctl.__version__,
    description=sfrtvctl.__doc__,
    url=sfrtvctl.__url__,
    author=sfrtvctl.__author__,
    author_email=sfrtvctl.__author_email__,
    license=sfrtvctl.__license__,
    long_description=open("README.md").read(),
    entry_points={
        "console_scripts": ["sfrtvctl=sfrtvctl.__main__:main"]
    },
    packages=["sfrtvctl"],
    install_requires=[],
    extras_require={
        "websocket": ["websocket-client"],
        "interactive_ui": ["curses"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Home Automation",
    ],
)
