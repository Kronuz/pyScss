#!/usr/bin/env python
from setuptools import setup, Extension

from scss.scss_meta import PROJECT, URL, VERSION, AUTHOR, AUTHOR_EMAIL, LICENSE, DOWNLOAD_URL


def read(fname):
    import os
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()
    except IOError:
        return ''


extra = {}
import sys
if sys.version_info >= (3, 0):
    extra.update(
        use_2to3=True,
    )


EXT_MODULES = [Extension('scss._scss', sources=['scss/src/_scss.c'], optional=True)]
if '--with-accel' in sys.argv:
    sys.argv.remove('--with-accel')
if '--without-accel' in sys.argv:
    sys.argv.remove('--without-accel')
    EXT_MODULES = []
if EXT_MODULES:
    print
    print '+------------------------------------------------------------------+'
    print '|                                                                  |'
    print '| pyScss, a Scss compiler for Python                               |'
    print '| ==================================                               |'
    print '|                                                                  |'
    print '| This package comes with an acceleration module in C.             |'
    print '|                                                                  |'
    print '| By default,the acceleration module is compiled and installed.    |'
    print '| Build and install without it by passing: --without-accel         |'
    print '|                                                                  |'
    print '+#################################################################-+'
    print
else:
    print
    print '+------------------------------------------------------------------+'
    print '|                                                                  |'
    print '| pyScss, a Scss compiler for Python                               |'
    print '| ==================================                               |'
    print '|                                                                  |'
    print '| Acceleration module disabled by the user.                        |'
    print '|                                                                  |'
    print '+#################################################################-+'
    print

setup(name=PROJECT,
    version=VERSION,
    description=read('DESCRIPTION'),
    long_description=read('README.rst'),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    packages=['scss'],
    license=LICENSE,
    keywords='css oocss xcss sass scss less precompiler',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Text Processing :: Markup",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    ext_modules=EXT_MODULES,
    package_data={'scss': ['scss/tests.rst', 'LICENSE', 'CHANGELOG']},
    entry_points="""
    [console_scripts]
    pyscss = scss:main
    """,
    **extra
)
