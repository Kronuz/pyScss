"""Evaluates all the tests that live in `scss/tests/files`.

A test is any file with a `.scss` extension.  It'll be compiled, and the output
will be compared to the contents of a file named `foo.css`.

Currently, test files must be nested exactly one directory below `files/`.
This limitation is completely arbitrary.
"""

from __future__ import absolute_import

import glob
import os.path

import pytest

from scss import Scss

HERE = os.path.join(os.path.split(__file__)[0], 'files')

@pytest.mark.parametrize(
    ('scss_fn', 'css_fn'), [
        (scss_fn, os.path.splitext(scss_fn)[0] + '.css')
        for scss_fn in glob.glob(os.path.join(HERE, '*/*.scss'))
    ]
)
def test_pair(scss_fn, css_fn):
    with open(scss_fn) as fh:
        source = fh.read()
    with open(css_fn) as fh:
        expected = fh.read()

    directory, _ = os.path.split(scss_fn)
    include_dir = os.path.join(directory, 'include')

    compiler = Scss(scss_opts=dict(compress=0), search_paths=[include_dir])
    actual = compiler.compile(source)

    # Normalize leading and trailing newlines
    actual = actual.strip('\n')
    expected = expected.strip('\n')

    assert expected == actual
