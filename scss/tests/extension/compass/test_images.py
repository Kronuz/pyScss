"""Tests for the Compass images functions.

Not all of Compass is implemented, and the arrangement of Compass functions
doesn't exactly match the arrangement in the original documentation.
Regardless, this is a good starting place:

http://compass-style.org/reference/compass/helpers/

Some functions appear to be undocumented, but nonetheless are part of Compass's
Ruby code.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys

import pytest

from scss import config
from scss.calculator import Calculator
from scss.extension.compass import CompassExtension
from scss.tests.util import needs_PIL


# TODO many of these tests could also stand to test for failure cases

@pytest.fixture
def calc():
    return Calculator(CompassExtension.namespace).evaluate_expression


def test_image_url(calc):
    # nb: config.IMAGES_URL is None and defaults to this
    images_url = config.STATIC_URL
    assert calc('image-url("/some_path.jpg")').render() == 'url({0}some_path.jpg)'.format(images_url)


# inline-image
@needs_PIL
def test_inline_image(calc, monkeypatch):
    monkeypatch.setattr(config, 'IMAGES_ROOT', os.path.join(config.PROJECT_ROOT, 'tests/files/images'))

    with open(os.path.join(config.PROJECT_ROOT, 'tests/files/images/test-qr.base64.txt'), 'r') as f:
        font_base64 = f.read()
    assert 'url(data:image/png;base64,%s)' % font_base64 == calc('inline_image("/test-qr.png")').render()

@needs_PIL
def test_inline_plaintext_image(calc, monkeypatch):
    monkeypatch.setattr(config, 'IMAGES_ROOT', os.path.join(config.PROJECT_ROOT, 'tests/files/images'))

    with open(os.path.join(config.PROJECT_ROOT, 'tests/files/images/test-svg.base64.txt'), 'r') as f:
        svg_base64 = f.read()
    assert 'url(data:image/svg+xml;base64,%s)' % svg_base64 == calc('inline_image("/test-svg.svg")').render()


@pytest.mark.skipif(sys.platform == 'win32', reason='cur mimetype is defined on windows')
@needs_PIL
def test_inline_cursor(calc, monkeypatch):
    monkeypatch.setattr(config, 'IMAGES_ROOT', os.path.join(config.PROJECT_ROOT, 'tests/files/cursors'))

    with open(os.path.join(config.PROJECT_ROOT, 'tests/files/cursors/fake.base64.txt'), 'r') as f:
        font_base64 = f.read()
    assert 'url(data:image/cur;base64,%s)' % font_base64 == calc('inline_image("/fake.cur")').render()
