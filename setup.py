#!/usr/bin/env python
from setuptools import setup

from pyscss.scss_meta import PROJECT, URL, VERSION, AUTHOR, AUTHOR_EMAIL, LICENSE, DOWNLOAD_URL

def read(fname):
    import os
    try:
        return open(os.path.join(os.path.dirname( __file__ ), fname)).read().strip()
    except IOError:
        return ''

extra = {}
import sys
if sys.version_info >= (3, 0):
    extra.update(
        use_2to3=True,
    )

setup(name=PROJECT,
    version=VERSION,
    description=read('DESCRIPTION'),
    long_description=read('README.rst'),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    packages=['pyscss'],
    license=LICENSE,
    keywords='css oocss xcss sass scss less precompiler',
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 3",
                 "Topic :: Software Development :: Code Generators",
                 "Topic :: Text Processing :: Markup",
                 "Topic :: Software Development :: Libraries :: Python Modules"
                 ],
    entry_points = """
    [console_scripts]
    pyscss = pyscss.scss:main
    """,
    **extra
    )
