from __future__ import absolute_import

import os.path

from scss import Scss

HERE = os.path.join(os.path.split(__file__)[0], 'simple_data')

def test_general():
    with open(os.path.join(HERE, '000-general.scss')) as fg:
        source = fg.read()
    with open(os.path.join(HERE, '000-general.css')) as fg:
        expected = fg.read()

    compiler = Scss(scss_opts=dict(compress=0))
    actual = compiler.compile(source)

    assert actual == expected
