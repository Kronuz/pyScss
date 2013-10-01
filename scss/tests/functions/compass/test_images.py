"""Tests for the Compass images functions.

Not all of Compass is implemented, and the arrangement of Compass functions
doesn't exactly match the arrangement in the original documentation.
Regardless, this is a good starting place:

http://compass-style.org/reference/compass/helpers/

Some functions appear to be undocumented, but nonetheless are part of Compass's
Ruby code.
"""

from scss.expression import Calculator
from scss.functions.compass.images import COMPASS_IMAGES_LIBRARY
from scss.rule import Namespace


import pytest
from scss import config
import os
from _pytest.monkeypatch import monkeypatch
xfail = pytest.mark.xfail

# TODO many of these tests could also stand to test for failure cases


@pytest.fixture
def calc():
    ns = Namespace(functions=COMPASS_IMAGES_LIBRARY)
    return Calculator(ns).evaluate_expression


def test_image_url(calc):
    assert calc('image-url("/some_path.jpg")').render() == ('url(%(images_url)ssome_path.jpg)' % {'images_url': config.IMAGES_URL})
    

# inline-image
def test_inline_image(calc):
    monkeypatch().setattr(config, 'IMAGES_ROOT', os.path.join(config.PROJECT_ROOT, 'tests/files/images'))
    
    f = open(os.path.join(config.PROJECT_ROOT, 'tests/files/images/test-qr.base64.txt'), 'rb')
    font_base64 = f.read()
    f.close()
    assert 'url(data:image/png;base64,%s)' % font_base64 == calc('inline_image("/test-qr.png")').render()


# for debugging uncomment next lines
#if __name__=='__main__':
#    test_image_url(calc())
#    test_inline_image(calc())
