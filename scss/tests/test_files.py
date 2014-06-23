"""Evaluates all the tests that live in `scss/tests/files`.

A test is any file with a `.scss` extension.  It'll be compiled, and the output
will be compared to the contents of a file named `foo.css`.

Currently, test files must be nested exactly one directory below `files/`.
This limitation is completely arbitrary. Files starting with '_' are skipped.

"""

from __future__ import absolute_import

import os.path
import logging

import scss


console = logging.StreamHandler()
logger = logging.getLogger('scss')
logger.setLevel(logging.ERROR)
logger.addHandler(console)


def test_pair_programmatic(scss_file_pair):
    scss_fn, css_fn = scss_file_pair

    if scss_fn.endswith('sprite-import.scss'):
        # disable cache_buster on sprite_map
        sprite_map_0 = scss.sprite_map
        def sprite_map_patch(g, **kwargs):
            kwargs.setdefault('cache_buster', scss.types.Boolean(False))
            return sprite_map_0(g, **kwargs)
        scss.sprite_map = sprite_map_patch

    with open(scss_fn) as fh:
        source = fh.read()
    try:
        with open(css_fn) as fh:
            expected = fh.read()
    except IOError:
        expected = ''

    directory, _ = os.path.split(scss_fn)
    include_dir = os.path.join(directory, 'include')
    scss.config.STATIC_ROOT = os.path.join(directory, 'static')

    compiler = scss.Scss(scss_opts=dict(style='expanded'), search_paths=[include_dir, directory])
    actual = compiler.compile(source)

    # Normalize leading and trailing newlines
    actual = actual.strip('\n')
    expected = expected.strip('\n')

    assert expected == actual
