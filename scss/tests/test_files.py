"""Evaluates all the tests that live in `scss/tests/files`.

A test is any file with a `.scss` extension.  It'll be compiled, and the output
will be compared to the contents of a file named `foo.css`.

Currently, test files must be nested exactly one directory below `files/`.
This limitation is completely arbitrary. Files starting with '_' are skipped.

"""

from __future__ import absolute_import, unicode_literals

import os.path
import logging

import six

import scss


if six.PY2:
    from io import open


console = logging.StreamHandler()
logger = logging.getLogger('scss')
logger.setLevel(logging.ERROR)
logger.addHandler(console)


def test_pair_programmatic(scss_file_pair):
    scss_fn, css_fn = scss_file_pair

    with open(scss_fn, 'rb') as fh:
        source = fh.read()
    with open(css_fn, 'r', encoding='utf8') as fh:
        expected = fh.read()

    directory, _ = os.path.split(scss_fn)
    include_dir = os.path.join(directory, 'include')
    scss.config.STATIC_ROOT = os.path.join(directory, 'static')

    compiler = scss.Scss(scss_opts=dict(style='expanded'), search_paths=[include_dir, directory])
    actual = compiler.compile(source)

    # Normalize leading and trailing newlines
    actual = actual.strip('\n')
    expected = expected.strip('\n')

    assert expected == actual
