from scss.expression import Calculator
from scss.functions.core import CORE_LIBRARY
from scss.rule import Namespace
from scss.types import Color, Null, Number, String

import pytest

@pytest.fixture
def calc():
    return Calculator().evaluate_expression

def test_reference_operations():
    """Test the example expressions in the reference document:

    http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html#operations
    """
    # TODO: break this into its own file and add the entire reference guide

    # Need to build the calculator manually to get at its namespace, and need
    # to use calculate() instead of evaluate_expression() so interpolation
    # works
    ns = Namespace(functions=CORE_LIBRARY)
    calc = Calculator(ns).calculate

    # Simple example
    assert calc('1in + 8pt') == Number(1.11111111, "in")

    # Division
    ns.set_variable('$width', Number(1000, "px"))
    ns.set_variable('$font-size', Number(12, "px"))
    ns.set_variable('$line-height', Number(30, "px"))
    assert calc('10px/8px') == String('10px / 8px') # plain CSS; no division
    assert calc('$width/2') == Number(500, "px")      # uses a variable; does division
    assert calc('(500px/2)') == Number(250, "px")     # uses parens; does division
    assert calc('5px + 8px/2px') == Number(9, "px")   # uses +; does division
    # TODO: Ruby doesn't include these spaces
    assert calc('#{$font-size}/#{$line-height}') == String('12px / 30px')
                                            # uses #{}; does no division

    # Color operations
    ns.set_variable('$translucent-red', Color.from_rgb(1, 0, 0, 0.5))
    ns.set_variable('$green', Color.from_name('lime'))
    assert calc('#010203 + #040506') == Color.from_hex('#050709')
    assert calc('#010203 * 2') == Color.from_hex('#020406')
    assert calc('rgba(255, 0, 0, 0.75) + rgba(0, 255, 0, 0.75)') == Color.from_rgb(1, 1, 0, 0.75)
    assert calc('opacify($translucent-red, 0.3)') == Color.from_rgb(1, 0, 0, 0.9)
    assert calc('transparentize($translucent-red, 0.25)') == Color.from_rgb(1, 0, 0, 0.25)
    assert calc("progid:DXImageTransform.Microsoft.gradient(enabled='false', startColorstr='#{ie-hex-str($green)}', endColorstr='#{ie-hex-str($translucent-red)}')"
                ) == "progid:DXImageTransform.Microsoft.gradient(enabled='false', startColorstr=#FF00FF00, endColorstr=#80FF0000)"

    # String operations
    ns.set_variable('$value', Null())
    assert calc('e + -resize') == 'e-resize'
    assert calc('"Foo " + Bar') == '"Foo Bar"'
    assert calc('sans- + "serif"') == 'sans-serif'
    assert calc('3px + 4px auto') == '7px auto'
    assert calc('"I ate #{5 + 10} pies!"') == '"I ate 15 pies!"'
    assert calc('"I ate #{$value} pies!"') == '"I ate  pies!"'



# Operators: arithmetic (+ - * / %), unary (+ -), comparison (== != < > <= >=), boolean
# Types: numbers, colors, strings, booleans, lists
# Test them all!

def test_addition(calc):
    assert calc('123 + 456') == Number(579)

    assert calc('1px + 2px') == Number(3, "px")

    assert calc('123 + abc') == String('123abc')
    assert calc('abc + 123') == String('abc123')

    assert calc('abc + def') == String('abcdef')
    assert calc('abc + "def"') == String('abcdef')
    ret = calc('"abc" + def')
    assert ret == String('abcdef')
    assert ret.quotes == '"'
    ret = calc('"abc" + "def"')
    assert ret == String('abcdef')
    assert ret.quotes == '"'

    assert calc('#010305 + #050301') == Color.from_hex('#060606')
    assert calc('#ffffff + #ffffff') == Color.from_name('white')

def test_subtraction(calc):
    assert calc('123 - 456') == Number(-333)
    assert calc('456 - 123') == Number(333)
    # TODO test that subtracting e.g. strings doesn't work

    assert calc('#0f0f0f - #050505') == Color.from_hex('#0a0a0a')

def test_division(calc):
    assert calc('(5px / 5px)') == Number(1)
    assert calc('(5px / 5px)') == Number(1)

def test_comparison_numeric(calc):
    assert calc('123 < 456')
    assert calc('123 <= 456')
    assert calc('123 <= 123')
    assert calc('456 > 123')
    assert calc('456 >= 123')
    assert calc('456 >= 456')
    assert calc('123 == 123')
    assert calc('123 != 456')

    # Same tests, negated
    assert not calc('123 > 456')
    assert not calc('123 >= 456')
    assert not calc('456 < 123')
    assert not calc('456 <= 123')
    assert not calc('123 != 123')
    assert not calc('123 == 456')

def test_comparison_stringerific(calc):
    assert calc('"abc" == "abc"')
    assert calc('"abc" != "xyz"')

    # Same tests, negated
    assert not calc('"abc" != "abc"')
    assert not calc('"abc" == "xyz"')

    # Interaction with other types
    assert calc('123 != "123"')

    # Sass strings don't support ordering
    for expression in (
            '"abc" < "xyz"',
            '"abc" <= "xyz"',
            '"abc" <= "abc"',
            '"xyz" > "abc"',
            '"xyz" >= "abc"',
            '"xyz" >= "xyz"',
            '123 < "456"'):

        with pytest.raises(TypeError):
            calc(expression)

def test_comparison_null(calc):
    assert calc('null == null')
    assert calc('null != 0')

    with pytest.raises(TypeError):
        calc('null < null')



# TODO write more!  i'm lazy.
