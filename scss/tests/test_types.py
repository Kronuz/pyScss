"""Tests for the type system."""

from scss.types import Color, Null, Number, String

import pytest


# Operators: arithmetic (+ - * / %), unary (+ -), comparison (== != < > <= >=), boolean
# Types: numbers, colors, strings, booleans, lists
# Test them all!

def test_addition():
    assert Number(123) + Number(456) == Number(579)

    assert Number(1, "px") + Number(2, "px") == Number(3, "px")

    assert Number(123) + String('abc') == String('123abc')
    assert String('abc') + Number(123) == String('abc123')

    ret = String('abc', quotes=None) + String('def', quotes=None)
    assert ret == String('abcdef')
    assert ret.quotes is None

    ret = String('abc', quotes='"') + String('def', quotes=None)
    assert ret == String('abcdef')
    assert ret.quotes is '"'

    ret = String('abc', quotes=None) + String('def', quotes='"')
    assert ret == String('abcdef')
    assert ret.quotes is None

    assert Color.from_hex('#010305') + Color.from_hex('#050301') == Color.from_hex('#060606')
    assert Color.from_name('white') + Color.from_name('white') == Color.from_name('white')


def test_subtraction():
    assert Number(123) - Number(456) == Number(-333)
    assert Number(456) - Number(123) == Number(333)
    # TODO test that subtracting e.g. strings doesn't work

    assert Color.from_hex('#0f0f0f') - Color.from_hex('#050505') == Color.from_hex('#0a0a0a')


def test_division():
    assert Number(5, "px") / Number(5, "px") == Number(1)
    assert Number(1, "in") / Number(6, "pt") == Number(12)


def test_comparison_numeric():
    lo = Number(123)
    hi = Number(456)
    assert lo < hi
    assert lo <= hi
    assert lo <= lo
    assert hi > lo
    assert hi >= lo
    assert hi >= hi
    assert lo == lo
    assert lo != hi

    # Same tests, negated
    assert not lo > hi
    assert not lo >= hi
    assert not hi < lo
    assert not hi <= lo
    assert not lo != lo
    assert not lo == hi


def test_comparison_stringerific():
    abc = String('abc')
    xyz = String('xyz')

    assert abc == abc
    assert abc != xyz
    assert not abc == xyz
    assert not abc != abc

    # Interaction with other types
    assert Number(123) != String('123')
    assert String('123') != Number(123)

    # Sass strings don't support ordering
    with pytest.raises(TypeError):
        abc < xyz

    with pytest.raises(TypeError):
        abc <= xyz

    with pytest.raises(TypeError):
        abc > xyz

    with pytest.raises(TypeError):
        abc >= xyz

    with pytest.raises(TypeError):
        Number(123) < String('123')


def test_comparison_null():
    null = Null()

    assert null == null
    assert null != Number(0)

    with pytest.raises(TypeError):
        null < null


# TODO write more!  i'm lazy.
