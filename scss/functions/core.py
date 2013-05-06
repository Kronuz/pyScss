"""Functions from the Sass "standard library", i.e., built into the original
Ruby implementation.
"""

from __future__ import absolute_import

import colorsys
import logging
import math
import operator

from scss.cssdefs import _conv_type, _units, _units_weights, _variable_re
from scss.functions.library import FunctionLibrary
from scss.types import BooleanValue, ColorValue, ListValue, NumberValue, QuotedStringValue, StringValue, Value

log = logging.getLogger(__name__)

CORE_LIBRARY = FunctionLibrary()
register = CORE_LIBRARY.register

# ------------------------------------------------------------------------------
# Color creation

def _color_type(color, a, type):
    color = ColorValue(color).value
    a = NumberValue(a).value if a is not None else color[3]
    col = list(color[:3])
    col += [0.0 if a < 0 else 1.0 if a > 1 else a]
    col += [type]
    return ColorValue(col)


@register('rgba', 4)
def rgba(r, g, b, a, type='rgba'):
    c = NumberValue(r), NumberValue(g), NumberValue(b), NumberValue(a)

    col = [c[i].value * 255.0 if (c[i].unit == '%' or c[i].value > 0 and c[i].value <= 1) else
            0.0 if c[i].value < 0 else
            255.0 if c[i].value > 255 else
            c[i].value
            for i in range(3)
          ]
    col += [0.0 if c[3].value < 0 else 1.0 if c[3].value > 1 else c[3].value]
    col += [type]
    return ColorValue(col)

@register('rgb', 3)
def rgb(r, g, b, type='rgb'):
    return rgba(r, g, b, 1.0, type)


@register('rgba', 1)
@register('rgba', 2)
def rgba2(color, a=None):
    return _color_type(color, a, 'rgba')

@register('rgb', 1)
def rgb1(color):
    return _color_type(color, 1.0, 'rgb')


@register('hsla', 4)
def hsla(h, s, l, a, type='hsla'):
    c = NumberValue(h), NumberValue(s), NumberValue(l), NumberValue(a)
    col = [c[0] if (c[0].unit == '%' and c[0].value > 0 and c[0].value <= 1) else (c[0].value % 360.0) / 360.0]
    col += [0.0 if cl <= 0 else 1.0 if cl >= 1.0 else cl
            for cl in [
                c[i].value if (c[i].unit == '%' or c[i].value > 0 and c[i].value <= 1) else
                c[i].value / 100.0
                for i in range(1, 4)
              ]
           ]
    col += [type]
    c = [c * 255.0 for c in colorsys.hls_to_rgb(col[0], 0.999999 if col[2] == 1 else col[2], 0.999999 if col[1] == 1 else col[1])] + [col[3], type]
    col = ColorValue(c)
    return col

@register('hsl', 3)
def hsl(h, s, l, type='hsl'):
    return hsla(h, s, l, 1.0, type)


@register('hsla', 1)
@register('hsla', 2)
def hsla2(color, a=None):
    return _color_type(color, a, 'hsla')

@register('hsl', 1)
def hsl1(color):
    return _color_type(color, 1.0, 'hsl')


@register('mix', 2)
@register('mix', 3)
def mix(color1, color2, weight=None):
    """
    Mixes together two colors. Specifically, takes the average of each of the
    RGB components, optionally weighted by the given percentage.
    The opacity of the colors is also considered when weighting the components.

    Specifically, takes the average of each of the RGB components,
    optionally weighted by the given percentage.
    The opacity of the colors is also considered when weighting the components.

    The weight specifies the amount of the first color that should be included
    in the returned color.
    50%, means that half the first color
        and half the second color should be used.
    25% means that a quarter of the first color
        and three quarters of the second color should be used.

    For example:

        mix(#f00, #00f) => #7f007f
        mix(#f00, #00f, 25%) => #3f00bf
        mix(rgba(255, 0, 0, 0.5), #00f) => rgba(63, 0, 191, 0.75)

    """
    # This algorithm factors in both the user-provided weight
    # and the difference between the alpha values of the two colors
    # to decide how to perform the weighted average of the two RGB values.
    #
    # It works by first normalizing both parameters to be within [-1, 1],
    # where 1 indicates "only use color1", -1 indicates "only use color 0",
    # and all values in between indicated a proportionately weighted average.
    #
    # Once we have the normalized variables w and a,
    # we apply the formula (w + a)/(1 + w*a)
    # to get the combined weight (in [-1, 1]) of color1.
    # This formula has two especially nice properties:
    #
    #   * When either w or a are -1 or 1, the combined weight is also that number
    #     (cases where w * a == -1 are undefined, and handled as a special case).
    #
    #   * When a is 0, the combined weight is w, and vice versa
    #
    # Finally, the weight of color1 is renormalized to be within [0, 1]
    # and the weight of color2 is given by 1 minus the weight of color1.
    #
    # Algorithm from the Sass project: http://sass-lang.com/

    c1 = ColorValue(color1).value
    c2 = ColorValue(color2).value
    p = NumberValue(weight).value if weight is not None else 0.5
    p = 0.0 if p < 0 else 1.0 if p > 1 else p

    w = p * 2 - 1
    a = c1[3] - c2[3]

    w1 = ((w if (w * a == -1) else (w + a) / (1 + w * a)) + 1) / 2.0

    w2 = 1 - w1
    q = [w1, w1, w1, p]
    r = [w2, w2, w2, 1 - p]

    color = ColorValue(None).merge(c1).merge(c2)
    color.value = [c1[i] * q[i] + c2[i] * r[i] for i in range(4)]

    return color


# ------------------------------------------------------------------------------
# Color inspection

@register('red', 1)
def red(color):
    c = ColorValue(color).value
    return NumberValue(c[0])


@register('green', 1)
def green(color):
    c = ColorValue(color).value
    return NumberValue(c[1])


@register('blue', 1)
def blue(color):
    c = ColorValue(color).value
    return NumberValue(c[2])


@register('opacity', 1)
@register('alpha', 1)
def alpha(color):
    c = ColorValue(color).value
    return NumberValue(c[3])


@register('hue', 1)
def hue(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(h * 360.0)
    ret.units = {'deg': _units_weights.get('deg', 1), '_': 'deg'}
    return ret


@register('saturation', 1)
def saturation(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(s)
    ret.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return ret


@register('lightness', 1)
def lightness(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(l)
    ret.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return ret


@register('ie-hex-str', 1)
def ie_hex_str(color):
    c = ColorValue(color).value
    return StringValue('#%02X%02X%02X%02X' % (round(c[3] * 255), round(c[0]), round(c[1]), round(c[2])))


# ------------------------------------------------------------------------------
# Color modification

def __rgba_op(op, color, r, g, b, a):
    color = ColorValue(color)
    c = color.value
    a = [
        None if r is None else NumberValue(r).value,
        None if g is None else NumberValue(g).value,
        None if b is None else NumberValue(b).value,
        None if a is None else NumberValue(a).value,
    ]
    # Do the additions:
    c = [op(c[i], a[i]) if op is not None and a[i] is not None else a[i] if a[i] is not None else c[i] for i in range(4)]
    # Validations:
    r = 255.0, 255.0, 255.0, 1.0
    c = [0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4)]
    color.value = tuple(c)
    return color


@register('fade-in', 2)
@register('fadein', 2)
@register('opacify', 2)
def opacify(color, amount):
    return __rgba_op(operator.__add__, color, 0, 0, 0, amount)


@register('fade-out', 2)
@register('fadeout', 2)
@register('transparentize', 2)
def transparentize(color, amount):
    return __rgba_op(operator.__sub__, color, 0, 0, 0, amount)


def __hsl_op(op, color, h, s, l):
    color = ColorValue(color)
    c = color.value
    h = None if h is None else NumberValue(h)
    s = None if s is None else NumberValue(s)
    l = None if l is None else NumberValue(l)
    a = [
        None if h is None else h.value / 360.0,
        None if s is None else s.value / 100.0 if s.unit != '%' and s.value >= 1 else s.value,
        None if l is None else l.value / 100.0 if l.unit != '%' and l.value >= 1 else l.value,
    ]
    # Convert to HSL:
    h, l, s = list(colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0))
    c = h, s, l
    # Do the additions:
    c = [0.0 if c[i] < 0 else 1.0 if c[i] > 1 else op(c[i], a[i]) if op is not None and a[i] is not None else a[i] if a[i] is not None else c[i] for i in range(3)]
    # Validations:
    c[0] = (c[0] * 360.0) % 360
    r = 360.0, 1.0, 1.0
    c = [0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(3)]
    # Convert back to RGB:
    c = colorsys.hls_to_rgb(c[0] / 360.0, 0.999999 if c[2] == 1 else c[2], 0.999999 if c[1] == 1 else c[1])
    color.value = (c[0] * 255.0, c[1] * 255.0, c[2] * 255.0, color.value[3])
    return color


@register('lighten', 2)
def lighten(color, amount):
    return __hsl_op(operator.__add__, color, 0, 0, amount)


@register('darken', 2)
def darken(color, amount):
    return __hsl_op(operator.__sub__, color, 0, 0, amount)


@register('saturate', 2)
def saturate(color, amount):
    return __hsl_op(operator.__add__, color, 0, amount, 0)


@register('desaturate', 2)
def desaturate(color, amount):
    return __hsl_op(operator.__sub__, color, 0, amount, 0)


@register('greyscale', 2)
@register('grayscale', 2)
def grayscale(color):
    return __hsl_op(operator.__sub__, color, 0, 100.0, 0)


@register('spin', 2)
@register('adjust-hue', 2)
def adjust_hue(color, degrees):
    return __hsl_op(operator.__add__, color, degrees, 0, 0)


@register('complement', 1)
def complement(color):
    return __hsl_op(operator.__add__, color, 180.0, 0, 0)


@register('invert', 1)
def invert(color):
    """
    Returns the inverse (negative) of a color.
    The red, green, and blue values are inverted, while the opacity is left alone.
    """
    col = ColorValue(color)
    c = col.value
    c[0] = 255.0 - c[0]
    c[1] = 255.0 - c[1]
    c[2] = 255.0 - c[2]
    return col


@register('adjust-lightness', 2)
def adjust_lightness(color, amount):
    return __hsl_op(operator.__add__, color, 0, 0, amount)


@register('adjust-saturation', 2)
def adjust_saturation(color, amount):
    return __hsl_op(operator.__add__, color, 0, amount, 0)


@register('scale-lightness', 2)
def scale_lightness(color, amount):
    return __hsl_op(operator.__mul__, color, 0, 0, amount)


@register('scale-saturation', 2)
def scale_saturation(color, amount):
    return __hsl_op(operator.__mul__, color, 0, amount, 0)


def _asc_color(op, color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    if lightness or saturation:
        color = __hsl_op(op, color, 0, saturation, lightness)
    if red or green or blue or alpha:
        color = __rgba_op(op, color, red, green, blue, alpha)
    return color


@register('adjust-color')
def adjust_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(operator.__add__, color, saturation, lightness, red, green, blue, alpha)


@register('scale-color')
def scale_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(operator.__mul__, color, saturation, lightness, red, green, blue, alpha)


@register('change-color')
def change_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(None, color, saturation, lightness, red, green, blue, alpha)


# ------------------------------------------------------------------------------
# String type manipulation

@register('e', 1)
@register('escape', 1)
@register('unquote')
def unquote(*args):
    return StringValue(' '.join([StringValue(s).value for s in args]))


@register('quote')
def quote(*args):
    return QuotedStringValue(' '.join([StringValue(s).value for s in args]))


# ------------------------------------------------------------------------------
# Number functions

@register('percentage', 1)
def percentage(value):
    value = NumberValue(value)
    value.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return value

CORE_LIBRARY.add(Value._wrap(abs), 'abs', 1)
CORE_LIBRARY.add(Value._wrap(round), 'round', 1)
CORE_LIBRARY.add(Value._wrap(math.ceil), 'ceil', 1)
CORE_LIBRARY.add(Value._wrap(math.floor), 'floor', 1)


# ------------------------------------------------------------------------------
# List functions
def __parse_separator(separator):
    if separator is None:
        return None
    separator = StringValue(separator).value
    if separator == 'comma':
        return ','
    elif separator == 'space':
        return ' '
    elif separator == 'auto':
        return None
    else:
        raise ValueError('Separator must be auto, comma, or space')


# TODO get the compass bit outta here
@register('-compass-list-size')
@register('length')
def _length(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst)
    return NumberValue(len(lst))


# TODO get the compass bit outta here
@register('-compass-nth', 2)
@register('nth', 2)
def nth(lst, n):
    """
    Return the Nth item in the string
    """
    n = StringValue(n).value
    lst = ListValue(lst).value
    try:
        n = int(float(n)) - 1
        n = n % len(lst)
    except:
        if n.lower() == 'first':
            n = 0
        elif n.lower() == 'last':
            n = -1
    try:
        ret = lst[n]
    except KeyError:
        lst = [v for k, v in sorted(lst.items()) if isinstance(k, int)]
        try:
            ret = lst[n]
        except:
            ret = ''
    return ret.__class__(ret)


@register('join', 2)
@register('join', 3)
def join(lst1, lst2, separator=None):
    ret = ListValue(lst1)
    lst2 = ListValue(lst2).value
    lst_len = len(ret.value)
    ret.value.update((k + lst_len if isinstance(k, int) else k, v) for k, v in lst2.items())
    separator = __parse_separator(separator)
    if separator is not None:
        ret.value['_'] = separator
    return ret


@register('min')
def min_(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst).value
    return min(lst.values())


@register('max')
def max_(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst).value
    return max(lst.values())


@register('append', 2)
@register('append', 3)
def append(lst, val, separator=None):
    separator = __parse_separator(separator)
    ret = ListValue(lst, separator)
    val = ListValue(val)
    for v in val:
        ret.value[len(ret)] = v
    return ret


@register('index', 2)
def index(lst, val):
    for i in xrange(len(lst)):
        if lst.value[i] == val:
            return NumberValue(i + 1)
    return BooleanValue(False)


# ------------------------------------------------------------------------------
# Meta functions

@register('type-of', 1)
def _type_of(obj):  # -> bool, number, string, color, list
    if isinstance(obj, BooleanValue):
        return StringValue('bool')
    if isinstance(obj, NumberValue):
        return StringValue('number')
    if isinstance(obj, ColorValue):
        return StringValue('color')
    if isinstance(obj, ListValue):
        return StringValue('list')
    if isinstance(obj, basestring) and _variable_re.match(obj):
        return StringValue('undefined')
    return StringValue('string')


@register('unit', 1)
def _unit(number):  # -> px, em, cm, etc.
    unit = NumberValue(number).unit
    return StringValue(unit)


@register('unitless', 1)
def unitless(value):
    value = NumberValue(value)
    return BooleanValue(not bool(value.unit))


@register('comparable', 2)
def comparable(number1, number2):
    n1, n2 = NumberValue(number1), NumberValue(number2)
    type1 = _conv_type.get(n1.unit)
    type2 = _conv_type.get(n2.unit)
    return BooleanValue(type1 == type2)


# ------------------------------------------------------------------------------
# Miscellaneous

@register('if', 2)
@register('if', 3)
def if_(condition, if_true, if_false=''):
    condition = bool(False if not condition or isinstance(condition, basestring) and (condition in ('0', 'false', 'undefined') or _variable_re.match(condition)) else condition)
    return if_true.__class__(if_true) if condition else if_true.__class__(if_false)


# ------------------------------------------------------------------------------
# Units -- not strictly functions, but implemented as such

def convert_to_unit(value, type):
    return value.convert_to(type)


for unit in _units:
    CORE_LIBRARY.add(convert_to_unit, unit, 2)
