"""Test utilities."""
from __future__ import absolute_import

import pytest

try:
    import PIL
except ImportError:
    try:
        import Image as PIL
    except ImportError:
        PIL = None


needs_PIL = pytest.mark.skipif(PIL is None, reason='image tests require PIL')
