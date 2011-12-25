#!/bin/sh
cd .. && python setup.py build && cp build/lib.macosx-10.7-intel-2.7/_scss.so src/ && cd -
