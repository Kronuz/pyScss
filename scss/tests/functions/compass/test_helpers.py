"""Tests for the Compass helper functions.

Not all of Compass is implemented, and the arrangement of Compass functions
doesn't exactly match the arrangement in the original documentation.
Regardless, this is a good starting place:

http://compass-style.org/reference/compass/helpers/

Some functions appear to be undocumented, but nonetheless are part of Compass's
Ruby code.
"""

from scss.expression import Calculator
from scss.functions.compass.helpers import COMPASS_HELPERS_LIBRARY
from scss.rule import Namespace
from scss.types import ColorValue, NumberValue

import pytest
xfail = pytest.mark.xfail

# TODO many of these tests could also stand to test for failure cases

@pytest.fixture
def calc():
    ns = Namespace(functions=COMPASS_HELPERS_LIBRARY)
    return Calculator(ns).evaluate_expression

# ------------------------------------------------------------------------------
# Listish functions
# See: http://ruby-doc.org/gems/docs/c/compass-0.12.2/Compass/SassExtensions/Functions/Lists.html

def test_blank(calc):
    assert calc('blank(false)')
    assert calc('blank("")')
    assert calc('blank(" ")')
    # TODO this is a syntax error; see #166
    #assert calc('blank(())')

    assert not calc('blank(null)')  # yes, really
    assert not calc('blank(1)')
    assert not calc('blank((1, 2))')
    assert not calc('blank(0)')

def test_compact(calc):
    assert calc('compact(1 2 3 false 4 5 null 6 7)') == calc('1 2 3 4 5 6 7')

def test_reject(calc):
    assert calc('reject(a b c d, a, c)') == calc('b d')
    assert calc('reject(a b c d, e)') == calc('a b c d')

def test_first_value_of(calc):
    assert calc('first-value-of(a b c d)') == calc('a')
    assert calc('first-value-of("a b c d")') == calc('"a"')
