#!/usr/bin/env python
import sys
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext as _build_ext
import os


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


class build_ext(_build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)
        self.build_temp = './'
        self.build_lib = '../grammar/'


if len(sys.argv) == 1:
    sys.argv.append('build')

setup(ext_modules=[
    Extension(
        '_scanner',
        sources=['_speedups.c', 'block_locator.c', 'scanner.c', 'hashtable.c'],
        libraries=['pcre'],
    ),
], cmdclass={'build_ext': build_ext})
