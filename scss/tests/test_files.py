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

    compiler = Scss(scss_opts=dict(compress=0))
    actual = compiler.compile(source)

    # Normalize leading and trailing newlines
    actual = actual.strip('\n')
    expected = expected.strip('\n')

    assert actual == expected
