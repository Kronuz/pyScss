from scss.expression import Calculator
from scss.rule import Namespace
#from scss.types import Number
from scss.util import to_str

import pytest

# TODO fix constructors for various types, and stop using to_str in here

def test_reference_operations():
    """Test the example expressions in the reference document:

    http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html#operations
    """
    # TODO: break this into its own file and add the entire reference guide
    ns = Namespace()
    calc = lambda expr: to_str(Calculator(ns).calculate(expr))

    # Simple example
    assert calc('1in + 8pt') == '1.111in'

    # Division
    ns.set_variable('$width', '1000px')
    ns.set_variable('$font-size', '12px')
    ns.set_variable('$line-height', '30px')
    assert calc('10px/8px') == '10px/8px'   # plain CSS; no division
    assert calc('$width/2') == '500px'      # uses a variable; does division
    assert calc('(500px/2)') == '250px'     # uses parens; does division
    assert calc('5px + 8px/2px') == '9px'   # uses +; does division
    assert calc('#{$font-size}/#{$line-height}') == '12px/30px'
                                            # uses #{}; does no division

    # Color operations
    ns.set_variable('$translucent-red', 'rgba(255, 0, 0, 0.5)')
    ns.set_variable('$green', '#00ff00')
    assert calc('#010203 + #040506') == '#050709'
    assert calc('#010203 * 2') == '#020406'
    assert calc('rgba(255, 0, 0, 0.75) + rgba(0, 255, 0, 0.75)') == 'rgba(255, 255, 0, 0.75)'
    assert calc('opacify($translucent-red, 0.3)') == 'rgba(255, 0, 0, 0.9)'
    assert calc('transparentize($translucent-red, 0.25)') == 'rgba(255, 0, 0, 0.25)'
    assert calc("progid:DXImageTransform.Microsoft.gradient(enabled='false', startColorstr='#{ie-hex-str($green)}', endColorstr='#{ie-hex-str($translucent-red)}')"
                ) == "progid:DXImageTransform.Microsoft.gradient(enabled='false', startColorstr=#FF00FF00, endColorstr=#80FF0000)"

    # String operations
    ns.set_variable('$value', 'null')
    assert calc('e + -resize') == 'e-resize'
    assert calc('"Foo " + Bar') == '"Foo Bar"'
    assert calc('sans- + "serif"') == 'sans-serif'
    assert calc('3px + 4px auto') == '7px auto'
    assert calc('"I ate #{5 + 10} pies!"') == '"I ate 15 pies!"'
    assert calc('"I ate #{$value} pies!"') == '"I ate  pies!"'



# Operators: arithmetic (+ - * / %), comparison (== != < > <= >=), boolean
# Types: numbers, colors, strings, booleans, lists
# Test them all!

def test_addition():
    calc = lambda expr: to_str(Calculator(Namespace()).calculate(expr))

    assert calc('123 + 456') == '579'

    assert calc('1px + 2px') == '3px'

    assert calc('123 + abc') == '123abc'
    assert calc('abc + 123') == 'abc123'

    assert calc('abc + def') == 'abcdef'
    assert calc('abc + "def"') == '"abcdef"'
    assert calc('"abc" + def') == '"abcdef"'

    assert calc('#010305 + #050301') == '#060606'
    assert calc('#ffffff + #ffffff') == '#ffffff'

def test_subtraction():
    calc = lambda expr: to_str(Calculator(Namespace()).calculate(expr))

    assert calc('123 - 456') == '-333'
    assert calc('456 - 123') == '333'
    # TODO test that subtracting e.g. strings doesn't work

    assert calc('#0f0f0f - #050505') == '#0a0a0a'

def test_comparison_numeric():
    calc = Calculator(Namespace()).calculate

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

def test_comparison_stringerific():
    calc = Calculator(Namespace()).calculate

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
            '"xyz" >= "xyz"'):

        with pytest.raises(TypeError):
            calc(expression)

def test_comparison_null():
    calc = Calculator(Namespace()).calculate

    assert calc('null == null')
    assert calc('null != 0')

    with pytest.raises(TypeError):
        calc('null < null')



# TODO write more!  i'm lazy.
