from __future__ import absolute_import

import base64
import colorsys
import datetime
import glob
import hashlib
import logging
import math
import mimetypes
import operator
import os.path
import pickle
import random
import tempfile
import time

from scss.config import ASSETS_ROOT, ASSETS_URL, STATIC_ROOT, STATIC_URL
from scss.cssdefs import _conv_type, _units, _units_weights
from scss.types import BooleanValue, ColorValue, ListValue, NumberValue, QuotedStringValue, StringValue, Value
from scss.util import escape, split_params, to_float, to_str
from scss.parseutil import _append_selector, _convert_to, _elements_of_type, _enumerate, _headers, _nest, _range

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image, ImageDraw
except ImportError:
    try:
        import Image, ImageDraw
    except:
        Image = None

log = logging.getLogger(__name__)

# TODO copied from __init__.py
import re
_variable_re = re.compile('^\\$[-a-zA-Z0-9_]+$')
_undefined_re = re.compile('^(?:\\$[-a-zA-Z0-9_]+|undefined)$')
del re


################################################################################
# Function registry

class FunctionRegistry(object):
    def __init__(self):
        self._function_dict = {}

    def legacy_register(self, str_key, func):
        name, argc = str_key.split(':')
        if argc == "n":
            argc = None
        else:
            argc = int(argc)

        key = name, argc
        self._function_dict[key] = func

    def register(self, name, argc=None):
        key = (name, argc)

        def decorator(f):
            self._function_dict[key] = f
            return f

        return decorator

    def lookup(self, name, argc=None):
        """Find a function given its name and the number of arguments it takes.
        """
        try:
            # Try the given arity first
            if argc is not None:
                return self._function_dict[name, argc]
        except KeyError:
            # Fall back to arbitrary-arity
            return self._function_dict[name, None]

################################################################################
# Sass/Compass Library Functions:

scss_builtins = FunctionRegistry()
register = scss_builtins.register

def _rgb(r, g, b, type='rgb'):
    return _rgba(r, g, b, 1.0, type)


def _rgba(r, g, b, a, type='rgba'):
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


def _color_type(color, a, type):
    color = ColorValue(color).value
    a = NumberValue(a).value if a is not None else color[3]
    col = list(color[:3])
    col += [0.0 if a < 0 else 1.0 if a > 1 else a]
    col += [type]
    return ColorValue(col)


def _rgb2(color):
    return _color_type(color, 1.0, 'rgb')


def _rgba2(color, a=None):
    return _color_type(color, a, 'rgba')


def _hsl2(color):
    return _color_type(color, 1.0, 'hsl')


def _hsla2(color, a=None):
    return _color_type(color, a, 'hsla')


def _ie_hex_str(color):
    c = ColorValue(color).value
    return StringValue('#%02X%02X%02X%02X' % (round(c[3] * 255), round(c[0]), round(c[1]), round(c[2])))


def _hsl(h, s, l, type='hsl'):
    return _hsla(h, s, l, 1.0, type)


def _hsla(h, s, l, a, type='hsla'):
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


def _opacify(color, amount):
    return __rgba_op(operator.__add__, color, 0, 0, 0, amount)


def _transparentize(color, amount):
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


def _lighten(color, amount):
    return __hsl_op(operator.__add__, color, 0, 0, amount)


def _darken(color, amount):
    return __hsl_op(operator.__sub__, color, 0, 0, amount)


def _saturate(color, amount):
    return __hsl_op(operator.__add__, color, 0, amount, 0)


def _desaturate(color, amount):
    return __hsl_op(operator.__sub__, color, 0, amount, 0)


def _grayscale(color):
    return __hsl_op(operator.__sub__, color, 0, 100.0, 0)


def _adjust_hue(color, degrees):
    return __hsl_op(operator.__add__, color, degrees, 0, 0)


def _complement(color):
    return __hsl_op(operator.__add__, color, 180.0, 0, 0)


def _invert(color):
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


def _adjust_lightness(color, amount):
    return __hsl_op(operator.__add__, color, 0, 0, amount)


def _adjust_saturation(color, amount):
    return __hsl_op(operator.__add__, color, 0, amount, 0)


def _scale_lightness(color, amount):
    return __hsl_op(operator.__mul__, color, 0, 0, amount)


def _scale_saturation(color, amount):
    return __hsl_op(operator.__mul__, color, 0, amount, 0)


def _asc_color(op, color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    if lightness or saturation:
        color = __hsl_op(op, color, 0, saturation, lightness)
    if red or green or blue or alpha:
        color = __rgba_op(op, color, red, green, blue, alpha)
    return color


def _adjust_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(operator.__add__, color, saturation, lightness, red, green, blue, alpha)


def _scale_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(operator.__mul__, color, saturation, lightness, red, green, blue, alpha)


def _change_color(color, saturation=None, lightness=None, red=None, green=None, blue=None, alpha=None):
    return _asc_color(None, color, saturation, lightness, red, green, blue, alpha)


def _mix(color1, color2, weight=None):
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


def _red(color):
    c = ColorValue(color).value
    return NumberValue(c[0])


def _green(color):
    c = ColorValue(color).value
    return NumberValue(c[1])


def _blue(color):
    c = ColorValue(color).value
    return NumberValue(c[2])


def _alpha(color):
    c = ColorValue(color).value
    return NumberValue(c[3])


def _hue(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(h * 360.0)
    ret.units = {'deg': _units_weights.get('deg', 1), '_': 'deg'}
    return ret


def _saturation(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(s)
    ret.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return ret


def _lightness(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(l)
    ret.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return ret


def __color_stops(percentages, *args):
    if len(args) == 1:
        if isinstance(args[0], (list, tuple, ListValue)):
            return ListValue(args[0]).values()
        elif isinstance(args[0], (StringValue, basestring)):
            color_stops = []
            colors = split_params(args[0].value)
            for color in colors:
                color = color.strip()
                if color.startswith('color-stop('):
                    s, c = split_params(color[11:].rstrip(')'))
                    s = s.strip()
                    c = c.strip()
                else:
                    c, s = color.split()
                color_stops.append((to_float(s), c))
            return color_stops

    colors = []
    stops = []
    prev_color = False
    for c in args:
        if isinstance(c, ListValue):
            for i, c in c.items():
                if isinstance(c, ColorValue):
                    if prev_color:
                        stops.append(None)
                    colors.append(c)
                    prev_color = True
                elif isinstance(c, NumberValue):
                    stops.append(c)
                    prev_color = False
        else:
            if isinstance(c, ColorValue):
                if prev_color:
                    stops.append(None)
                colors.append(c)
                prev_color = True
            elif isinstance(c, NumberValue):
                stops.append(NumberValue(c))
                prev_color = False
    if prev_color:
        stops.append(None)
    stops = stops[:len(colors)]
    if percentages:
        max_stops = max(s and (s.value if s.unit != '%' else None) or None for s in stops)
    else:
        max_stops = max(s and (s if s.unit != '%' else None) or None for s in stops)
    stops = [s and (s.value / max_stops if s.unit != '%' else s.value) for s in stops]
    stops[0] = 0

    init = 0
    start = None
    for i, s in enumerate(stops + [1.0]):
        if s is None:
            if start is None:
                start = i
            end = i
        else:
            final = s
            if start is not None:
                stride = (final - init) / (end - start + 1 + (1 if i < len(stops) else 0))
                for j in range(start, end + 1):
                    stops[j] = init + stride * (j - start + 1)
            init = final
            start = None

    if not max_stops or percentages:
        stops = [NumberValue(s, '%') for s in stops]
    else:
        stops = [s * max_stops for s in stops]
    return zip(stops, colors)


def _grad_color_stops(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    color_stops = __color_stops(True, *args)
    ret = ', '.join(['color-stop(%s, %s)' % (to_str(s), c) for s, c in color_stops])
    return StringValue(ret)


def __grad_end_position(radial, color_stops):
    return __grad_position(-1, 100, radial, color_stops)


def __grad_position(index, default, radial, color_stops):
    try:
        stops = NumberValue(color_stops[index][0])
        if radial and stops.unit != 'px' and (index == 0 or index == -1 or index == len(color_stops) - 1):
            log.warn("Webkit only supports pixels for the start and end stops for radial gradients. Got %s", stops)
    except IndexError:
        stops = NumberValue(default)
    return stops


def _grad_end_position(*color_stops):
    color_stops = __color_stops(False, *color_stops)
    return NumberValue(__grad_end_position(False, color_stops))


def _color_stops(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    color_stops = __color_stops(False, *args)
    ret = ', '.join(['%s %s' % (c, to_str(s)) for s, c in color_stops])
    return StringValue(ret)


def _color_stops_in_percentages(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    color_stops = __color_stops(True, *args)
    ret = ', '.join(['%s %s' % (c, to_str(s)) for s, c in color_stops])
    return StringValue(ret)


def _get_gradient_position_and_angle(args):
    for arg in args:
        if isinstance(arg, (StringValue, NumberValue, basestring)):
            _arg = [arg]
        elif isinstance(arg, (list, tuple, ListValue)):
            _arg = arg
        else:
            continue
        ret = None
        skip = False
        for a in _arg:
            if isinstance(a, ColorValue):
                skip = True
                break
            elif isinstance(a, NumberValue):
                ret = arg
        if skip:
            continue
        if ret is not None:
            return ret
        for seek in (
            'center',
            'top', 'bottom',
            'left', 'right',
        ):
            if seek in _arg:
                return arg
    return None


def _get_gradient_shape_and_size(args):
    for arg in args:
        if isinstance(arg, (StringValue, NumberValue, basestring)):
            _arg = [arg]
        elif isinstance(arg, (list, tuple, ListValue)):
            _arg = arg
        else:
            continue
        for seek in (
            'circle', 'ellipse',
            'closest-side', 'closest-corner',
            'farthest-side', 'farthest-corner',
            'contain', 'cover',
        ):
            if seek in _arg:
                return arg
    return None


def _get_gradient_color_stops(args):
    color_stops = []
    for arg in args:
        if isinstance(arg, ColorValue):
            color_stops.append(arg)
        elif isinstance(arg, (list, tuple, ListValue)):
            for a in arg:
                if isinstance(a, ColorValue):
                    color_stops.append(arg)
                    break
    return color_stops or None


def _radial_gradient(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()

    position_and_angle = _get_gradient_position_and_angle(args)
    shape_and_size = _get_gradient_shape_and_size(args)
    color_stops = _get_gradient_color_stops(args)
    color_stops = __color_stops(False, *color_stops)

    args = [
        _position(position_and_angle) if position_and_angle is not None else None,
        shape_and_size if shape_and_size is not None else None,
    ]
    args.extend('%s %s' % (c, to_str(s)) for s, c in color_stops)

    to__s = 'radial-gradient(' + ', '.join(to_str(a) for a in args or [] if a is not None) + ')'
    ret = StringValue(to__s)

    def to__css2():
        return StringValue('')
    ret.to__css2 = to__css2

    def to__moz():
        return StringValue('-moz-' + to__s)
    ret.to__moz = to__moz

    def to__pie():
        log.warn("PIE does not support radial-gradient.")
        return StringValue('-pie-radial-gradient(unsupported)')
    ret.to__pie = to__pie

    def to__webkit():
        return StringValue('-webkit-' + to__s)
    ret.to__webkit = to__webkit

    def to__owg():
        args = [
            'radial',
            _grad_point(position_and_angle) if position_and_angle is not None else 'center',
            '0',
            _grad_point(position_and_angle) if position_and_angle is not None else 'center',
            __grad_end_position(True, color_stops),
        ]
        args.extend('color-stop(%s, %s)' % (to_str(s), c) for s, c in color_stops)
        ret = '-webkit-gradient(' + ', '.join(to_str(a) for a in args or [] if a is not None) + ')'
        return StringValue(ret)
    ret.to__owg = to__owg

    def to__svg():
        return _radial_svg_gradient(color_stops, position_and_angle or 'center')
    ret.to__svg = to__svg

    return ret


def _linear_gradient(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()

    position_and_angle = _get_gradient_position_and_angle(args)
    color_stops = _get_gradient_color_stops(args)
    color_stops = __color_stops(False, *color_stops)

    args = [
        _position(position_and_angle) if position_and_angle is not None else None,
    ]
    args.extend('%s %s' % (c, to_str(s)) for s, c in color_stops)

    to__s = 'linear-gradient(' + ', '.join(to_str(a) for a in args or [] if a is not None) + ')'
    ret = StringValue(to__s)

    def to__css2():
        return StringValue('')
    ret.to__css2 = to__css2

    def to__moz():
        return StringValue('-moz-' + to__s)
    ret.to__moz = to__moz

    def to__pie():
        return StringValue('-pie-' + to__s)
    ret.to__pie = to__pie

    def to__ms():
        return StringValue('-ms-' + to__s)
    ret.to__ms = to__ms

    def to__o():
        return StringValue('-o-' + to__s)
    ret.to__o = to__o

    def to__webkit():
        return StringValue('-webkit-' + to__s)
    ret.to__webkit = to__webkit

    def to__owg():
        args = [
            'linear',
            _position(position_and_angle or 'center top'),
            _opposite_position(position_and_angle or 'center top'),
        ]
        args.extend('color-stop(%s, %s)' % (to_str(s), c) for s, c in color_stops)
        ret = '-webkit-gradient(' + ', '.join(to_str(a) for a in args or [] if a is not None) + ')'
        return StringValue(ret)
    ret.to__owg = to__owg

    def to__svg():
        return _linear_svg_gradient(color_stops, position_and_angle or 'top')
    ret.to__svg = to__svg

    return ret


def _radial_svg_gradient(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    color_stops = args
    center = None
    if isinstance(args[-1], (StringValue, NumberValue, basestring)):
        center = args[-1]
        color_stops = args[:-1]
    color_stops = __color_stops(False, *color_stops)
    cx, cy = zip(*_grad_point(center).items())[1]
    r = __grad_end_position(True, color_stops)
    svg = __radial_svg(color_stops, cx, cy, r)
    url = 'data:' + 'image/svg+xml' + ';base64,' + base64.b64encode(svg)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


def _linear_svg_gradient(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    color_stops = args
    start = None
    if isinstance(args[-1], (StringValue, NumberValue, basestring)):
        start = args[-1]
        color_stops = args[:-1]
    color_stops = __color_stops(False, *color_stops)
    x1, y1 = zip(*_grad_point(start).items())[1]
    x2, y2 = zip(*_grad_point(_opposite_position(start)).items())[1]
    svg = __linear_svg(color_stops, x1, y1, x2, y2)
    url = 'data:' + 'image/svg+xml' + ';base64,' + base64.b64encode(svg)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


def __color_stops_svg(color_stops):
    ret = ''.join('<stop offset="%s" stop-color="%s"/>' % (to_str(s), c) for s, c in color_stops)
    return ret


def __svg_template(gradient):
    ret = '<?xml version="1.0" encoding="utf-8"?>\
<svg version="1.1" xmlns="http://www.w3.org/2000/svg">\
<defs>%s</defs>\
<rect x="0" y="0" width="100%%" height="100%%" fill="url(#grad)" />\
</svg>' % gradient
    return ret


def __linear_svg(color_stops, x1, y1, x2, y2):
    gradient = '<linearGradient id="grad" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>' % (
        to_str(NumberValue(x1)),
        to_str(NumberValue(y1)),
        to_str(NumberValue(x2)),
        to_str(NumberValue(y2)),
        __color_stops_svg(color_stops)
    )
    return __svg_template(gradient)


def __radial_svg(color_stops, cx, cy, r):
    gradient = '<radialGradient id="grad" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s">%s</radialGradient>' % (
        to_str(NumberValue(cx)),
        to_str(NumberValue(cy)),
        to_str(NumberValue(r)),
        __color_stops_svg(color_stops)
    )
    return __svg_template(gradient)


################################################################################
# Compass like functionality for sprites and images:
sprite_maps = {}
sprite_images = {}


def _sprite_map(g, **kwargs):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.
    """
    g = StringValue(g).value

    if not Image:
        raise Exception("Images manipulation require PIL")

    if g in sprite_maps:
        sprite_maps[glob]['*'] = datetime.datetime.now()
    elif '..' not in g:  # Protect against going to prohibited places...
        vertical = (kwargs.get('direction', 'vertical') == 'vertical')
        repeat = StringValue(kwargs.get('repeat', 'no-repeat'))
        position = NumberValue(kwargs.get('position', 0))
        collapse_x = NumberValue(kwargs.get('collapse_x', 0))
        collapse_y = NumberValue(kwargs.get('collapse_y', 0))
        if position and position > -1 and position < 1:
            position.units = {'%': _units_weights.get('%', 1), '_': '%'}

        dst_colors = kwargs.get('dst_color')
        if isinstance(dst_colors, ListValue):
            dst_colors = [list(ColorValue(v).value[:3]) for n, v in dst_colors.items() if v]
        else:
            dst_colors = [list(ColorValue(dst_colors).value[:3])] if dst_colors else []

        src_colors = kwargs.get('src_color')
        if isinstance(src_colors, ListValue):
            src_colors = [tuple(ColorValue(v).value[:3]) if v else (0, 0, 0) for n, v in src_colors.items()]
        else:
            src_colors = [tuple(ColorValue(src_colors).value[:3]) if src_colors else (0, 0, 0)]

        len_colors = max(len(dst_colors), len(src_colors))
        dst_colors = (dst_colors * len_colors)[:len_colors]
        src_colors = (src_colors * len_colors)[:len_colors]

        spacing = kwargs.get('spacing', 0)
        if isinstance(spacing, ListValue):
            spacing = [int(NumberValue(v).value) for n, v in spacing.items()]
        else:
            spacing = [int(NumberValue(spacing).value)]
        spacing = (spacing * 4)[:4]

        if callable(STATIC_ROOT):
            glob_path = g
            rfiles = files = sorted(STATIC_ROOT(g))
        else:
            glob_path = os.path.join(STATIC_ROOT, g)
            files = glob.glob(glob_path)
            files = sorted((f, None) for f in files)
            rfiles = [(f[len(STATIC_ROOT):], s) for f, s in files]

        if not files:
            log.error("Nothing found at '%s'", glob_path)
            return StringValue(None)

        times = []
        for file, storage in files:
            try:
                d_obj = storage.modified_time(file)
                times.append(int(time.mktime(d_obj.timetuple())))
            except:
                times.append(int(os.path.getmtime(file)))

        map_name = os.path.normpath(os.path.dirname(g)).replace('\\', '_').replace('/', '_')
        key = list(zip(*files)[0]) + times + [repr(kwargs), ASSETS_URL]
        key = map_name + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + '.png'
        asset_path = os.path.join(ASSETS_ROOT, asset_file)

        try:
            asset, map, sizes = pickle.load(open(asset_path + '.cache'))
            sprite_maps[asset] = map
        except Exception:
            images = tuple(Image.open(storage.open(file)) if storage is not None else Image.open(file) for file, storage in files)
            names = tuple(os.path.splitext(os.path.basename(file))[0] for file, storage in files)
            positions = []
            spacings = []
            tot_spacings = []
            for name in names:
                name = name.replace('-', '_')
                _position = kwargs.get(name + '_position')
                if _position is None:
                    _position = position
                else:
                    _position = NumberValue(_position)
                    if _position and _position > -1 and _position < 1:
                        _position.units = {'%': _units_weights.get('%', 1), '_': '%'}
                positions.append(_position)
                _spacing = kwargs.get(name + '_spacing')
                if _spacing is None:
                    _spacing = spacing
                else:
                    if isinstance(_spacing, ListValue):
                        _spacing = [int(NumberValue(v).value) for n, v in _spacing.items()]
                    else:
                        _spacing = [int(NumberValue(_spacing).value)]
                    _spacing = (_spacing * 4)[:4]
                spacings.append(_spacing)
                if _position and _position.unit != '%':
                    if vertical:
                        if _position > 0:
                            tot_spacings.append((_spacing[0], _spacing[1], _spacing[2], _spacing[3] + _position))
                    else:
                        if _position > 0:
                            tot_spacings.append((_spacing[0] + _position, _spacing[1], _spacing[2], _spacing[3]))
                else:
                    tot_spacings.append(_spacing)

            sizes = tuple((collapse_x or image.size[0], collapse_y or image.size[1]) for image in images)

            _spacings = zip(*tot_spacings)
            if vertical:
                width = max(zip(*sizes)[0]) + max(_spacings[1]) + max(_spacings[3])
                height = sum(zip(*sizes)[1]) + sum(_spacings[0]) + sum(_spacings[2])
            else:
                width = sum(zip(*sizes)[0]) + sum(_spacings[1]) + sum(_spacings[3])
                height = max(zip(*sizes)[1]) + max(_spacings[0]) + max(_spacings[2])

            new_image = Image.new(
                mode='RGBA',
                size=(width, height),
                color=(0, 0, 0, 0)
            )

            offsets_x = []
            offsets_y = []
            offset = 0
            for i, image in enumerate(images):
                spacing = spacings[i]
                position = positions[i]
                iwidth, iheight = image.size
                width, height = sizes[i]
                if vertical:
                    if position and position.unit == '%':
                        x = width * position.value - (spacing[3] + height + spacing[1])
                    elif position.value < 0:
                        x = width + position.value - (spacing[3] + height + spacing[1])
                    else:
                        x = position.value
                    offset += spacing[0]
                    for i, dst_color in enumerate(dst_colors):
                        src_color = src_colors[i]
                        pixdata = image.load()
                        for _y in xrange(image.size[1]):
                            for _x in xrange(image.size[0]):
                                pixel = pixdata[_x, _y]
                                if pixel[:3] == src_color:
                                    pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                    if iwidth != width or iheight != height:
                        cy = 0
                        while cy < iheight:
                            cx = 0
                            while cx < iwidth:
                                cropped_image = image.crop((cx, cy, cx + width, cy + height))
                                new_image.paste(cropped_image, (int(x + spacing[3]), offset), cropped_image)
                                cx += width
                            cy += height
                    else:
                        new_image.paste(image, (int(x + spacing[3]), offset))
                    offsets_x.append(x)
                    offsets_y.append(offset - spacing[0])
                    offset += height + spacing[2]
                else:
                    if position and position.unit == '%':
                        y = height * position.value - (spacing[0] + height + spacing[2])
                    elif position.value < 0:
                        y = height + position.value - (spacing[0] + height + spacing[2])
                    else:
                        y = position.value
                    offset += spacing[3]
                    for i, dst_color in enumerate(dst_colors):
                        src_color = src_colors[i]
                        pixdata = image.load()
                        for _y in xrange(image.size[1]):
                            for _x in xrange(image.size[0]):
                                pixel = pixdata[_x, _y]
                                if pixel[:3] == src_color:
                                    pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                    if iwidth != width or iheight != height:
                        cy = 0
                        while cy < iheight:
                            cx = 0
                            while cx < iwidth:
                                cropped_image = image.crop((cx, cy, cx + width, cy + height))
                                new_image.paste(cropped_image, (offset, int(y + spacing[0])), cropped_image)
                                cx += width
                            cy += height
                    else:
                        new_image.paste(image, (offset, int(y + spacing[0])))
                    offsets_x.append(offset - spacing[3])
                    offsets_y.append(y)
                    offset += width + spacing[1]

            try:
                new_image.save(asset_path)
            except IOError:
                log.exception("Error while saving image")
            filetime = int(time.mktime(datetime.datetime.now().timetuple()))

            url = '%s%s?_=%s' % (ASSETS_URL, asset_file, filetime)
            asset = 'url("%s") %s' % (escape(url), repeat)
            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(sprite_maps) > 1000:
                for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['*'], reverse=True)[500:]:
                    del sprite_maps[a]
            # Add the new object:
            map = dict(zip(names, zip(sizes, rfiles, offsets_x, offsets_y)))
            map['*'] = datetime.datetime.now()
            map['*f*'] = asset_file
            map['*k*'] = key
            map['*n*'] = map_name
            map['*t*'] = filetime

            tmp_dir = ASSETS_ROOT
            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=tmp_dir)
            pickle.dump((asset, map, zip(files, sizes)), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, asset_path + '.cache')

            sprite_maps[asset] = map
        for file, size in sizes:
            sprite_images[file] = size
    ret = StringValue(asset)
    return ret


def _grid_image(left_gutter, width, right_gutter, height, columns=1, grid_color=None, baseline_color=None, background_color=None, inline=False):
    if not Image:
        raise Exception("Images manipulation require PIL")
    if grid_color == None:
        grid_color = (120, 170, 250, 15)
    else:
        c = ColorValue(grid_color).value
        grid_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    if baseline_color == None:
        baseline_color = (120, 170, 250, 30)
    else:
        c = ColorValue(baseline_color).value
        baseline_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    if background_color == None:
        background_color = (0, 0, 0, 0)
    else:
        c = ColorValue(background_color).value
        background_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    _height = int(height) if height >= 1 else int(height * 1000.0)
    _width = int(width) if width >= 1 else int(width * 1000.0)
    _left_gutter = int(left_gutter) if left_gutter >= 1 else int(left_gutter * 1000.0)
    _right_gutter = int(right_gutter) if right_gutter >= 1 else int(right_gutter * 1000.0)
    if _height <= 0 or _width <= 0 or _left_gutter <= 0 or _right_gutter <= 0:
        raise ValueError
    _full_width = (_left_gutter + _width + _right_gutter)
    new_image = Image.new(
        mode='RGBA',
        size=(_full_width * int(columns), _height),
        color=background_color
    )
    draw = ImageDraw.Draw(new_image)
    for i in range(int(columns)):
        draw.rectangle((i * _full_width + _left_gutter, 0, i * _full_width + _left_gutter + _width - 1, _height - 1),  fill=grid_color)
    if _height > 1:
        draw.rectangle((0, _height - 1, _full_width * int(columns) - 1, _height - 1),  fill=baseline_color)
    if not inline:
        grid_name = 'grid_'
        if left_gutter:
            grid_name += str(int(left_gutter)) + '+'
        grid_name += str(int(width))
        if right_gutter:
            grid_name += '+' + str(int(right_gutter))
        if height and height > 1:
            grid_name += 'x' + str(int(height))
        key = (columns, grid_color, baseline_color, background_color)
        key = grid_name + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + '.png'
        asset_path = os.path.join(ASSETS_ROOT, asset_file)
        try:
            new_image.save(asset_path)
        except IOError:
            log.exception("Error while saving image")
            inline = True  # Retry inline version
        url = '%s%s' % (ASSETS_URL, asset_file)
    if inline:
        output = StringIO()
        new_image.save(output, format='PNG')
        contents = output.getvalue()
        output.close()
        url = 'data:image/png;base64,' + base64.b64encode(contents)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


def _image_color(color, width=1, height=1):
    if not Image:
        raise Exception("Images manipulation require PIL")
    c = ColorValue(color).value
    w = int(NumberValue(width).value)
    h = int(NumberValue(height).value)
    if w <= 0 or h <= 0:
        raise ValueError
    new_image = Image.new(
        mode='RGB' if c[3] == 1 else 'RGBA',
        size=(w, h),
        color=(c[0], c[1], c[2], int(c[3] * 255.0))
    )
    output = StringIO()
    new_image.save(output, format='PNG')
    contents = output.getvalue()
    output.close()
    mime_type = 'image/png'
    url = 'data:' + mime_type + ';base64,' + base64.b64encode(contents)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


def _sprite_map_name(map):
    """
    Returns the name of a sprite map The name is derived from the folder than
    contains the sprites.
    """
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        return StringValue(sprite_map['*n*'])
    return StringValue(None)


def _sprite_file(map, sprite):
    """
    Returns the relative path (from the images directory) to the original file
    used when construction the sprite. This is suitable for passing to the
    image_width and image_height helpers.
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        return QuotedStringValue(sprite[1][0])
    return StringValue(None)


def _sprites(map):
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map, {})
    return ListValue(sorted(s for s in sprite_map if not s.startswith('*')))


def _sprite(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the image and background position for use in a single shorthand
    property
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['*f*'], sprite_map['*t*'])
        x = NumberValue(offset_x or 0, 'px')
        y = NumberValue(offset_y or 0, 'px')
        if not x or (x <= -1 or x >= 1) and x.unit != '%':
            x -= sprite[2]
        if not y or (y <= -1 or y >= 1) and y.unit != '%':
            y -= sprite[3]
        pos = "url(%s) %s %s" % (escape(url), x, y)
        return StringValue(pos)
    return StringValue('0 0')


def _sprite_url(map):
    """
    Returns a url to the sprite image.
    """
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['*f*'], sprite_map['*t*'])
        url = "url(%s)" % escape(url)
        return StringValue(url)
    return StringValue(None)


def _sprite_position(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the position for the original image in the sprite.
    This is suitable for use as a value to background-position.
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        x = None
        if offset_x is not None and not isinstance(offset_x, NumberValue):
            x = str(offset_x)
        if x not in ('left', 'right', 'center'):
            if x:
                offset_x = None
            x = NumberValue(offset_x or 0, 'px')
            if not x or (x <= -1 or x >= 1) and x.unit != '%':
                x -= sprite[2]
        y = None
        if offset_y is not None and not isinstance(offset_y, NumberValue):
            y = str(offset_y)
        if y not in ('top', 'bottom', 'center'):
            if y:
                offset_y = None
            y = NumberValue(offset_y or 0, 'px')
            if not y or (y <= -1 or y >= 1) and y.unit != '%':
                y -= sprite[3]
        pos = '%s %s' % (x, y)
        return StringValue(pos)
    return StringValue('0 0')


def _background_noise(intensity=None, opacity=None, size=None, monochrome=False, inline=False):
    if not Image:
        raise Exception("Images manipulation require PIL")

    intensity = intensity and NumberValue(intensity).value
    if not intensity or intensity < 0 or intensity > 1:
        intensity = 0.5

    opacity = opacity and NumberValue(opacity).value
    if not opacity or opacity < 0 or opacity > 1:
        opacity = 0.08

    size = size and int(NumberValue(size).value)
    if not size or size < 1 or size > 512:
        size = 200

    monochrome = bool(monochrome)

    new_image = Image.new(
        mode='RGBA',
        size=(size, size)
    )

    pixdata = new_image.load()
    for i in range(0, int(round(intensity * size ** 2))):
        x = random.randint(1, size)
        y = random.randint(1, size)
        r = random.randint(0, 255)
        a = int(round(random.randint(0, 255) * opacity))
        color = (r, r, r, a) if monochrome else (r, random.randint(0, 255), random.randint(0, 255), a)
        pixdata[x - 1, y - 1] = color

    if not inline:
        key = (intensity, opacity, size, monochrome)
        asset_file = 'noise_%s%sx%s+%s+%s' % ('mono_' if monochrome else '', size, size, to_str(intensity).replace('.', '_'), to_str(opacity).replace('.', '_'))
        asset_file = asset_file + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = asset_file + '.png'
        asset_path = os.path.join(ASSETS_ROOT, asset_file)
        try:
            new_image.save(asset_path)
        except IOError:
            log.exception("Error while saving image")
            inline = True  # Retry inline version
        url = '%s%s' % (ASSETS_URL, asset_file)
    if inline:
        output = StringIO()
        new_image.save(output, format='PNG')
        contents = output.getvalue()
        output.close()
        url = 'data:image/png;base64,' + base64.b64encode(contents)

    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


def add_cache_buster(url, mtime):
    fragment = url.split('#')
    query = fragment[0].split('?')
    if len(query) > 1 and query[1] != '':
        cb = '&_=%s' % (mtime)
        url = '?'.join(query) + cb
    else:
        cb = '?_=%s' % (mtime)
        url = query[0] + cb
    if len(fragment) > 1:
        url += '#' + fragment[1]
    return url


def _stylesheet_url(path, only_path=False, cache_buster=True):
    """
    Generates a path to an asset found relative to the project's css directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    filepath = StringValue(path).value
    if callable(STATIC_ROOT):
        try:
            _file, _storage = list(STATIC_ROOT(filepath))[0]
            d_obj = _storage.modified_time(_file)
            filetime = int(time.mktime(d_obj.timetuple()))
        except:
            filetime = 'NA'
    else:
        _path = os.path.join(STATIC_ROOT, filepath.strip('/'))
        if os.path.exists(_path):
            filetime = int(os.path.getmtime(_path))
        else:
            filetime = 'NA'
    BASE_URL = STATIC_URL

    url = '%s%s' % (BASE_URL, filepath)
    if cache_buster:
        url = add_cache_buster(url, filetime)
    if not only_path:
        url = 'url("%s")' % (url)
    return StringValue(url)


def __font_url(path, only_path=False, cache_buster=True, inline=False):
    filepath = StringValue(path).value
    path = None
    if callable(STATIC_ROOT):
        try:
            _file, _storage = list(STATIC_ROOT(filepath))[0]
            d_obj = _storage.modified_time(_file)
            filetime = int(time.mktime(d_obj.timetuple()))
            if inline:
                path = _storage.open(_file)
        except:
            filetime = 'NA'
    else:
        _path = os.path.join(STATIC_ROOT, filepath.strip('/'))
        if os.path.exists(_path):
            filetime = int(os.path.getmtime(_path))
            if inline:
                path = open(_path, 'rb')
        else:
            filetime = 'NA'
    BASE_URL = STATIC_URL

    if path and inline:
        mime_type = mimetypes.guess_type(filepath)[0]
        url = 'data:' + mime_type + ';base64,' + base64.b64encode(path.read())
    else:
        url = '%s%s' % (BASE_URL, filepath)
        if cache_buster:
            url = add_cache_buster(url, filetime)

    if not only_path:
        url = 'url("%s")' % escape(url)
    return StringValue(url)


def __font_files(args, inline):
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    n = 0
    params = [[], []]
    for arg in args:
        if isinstance(arg, ListValue):
            if len(arg) == 2:
                if n % 2 == 1:
                    params[1].append(None)
                    n += 1
                params[0].append(arg[0])
                params[1].append(arg[1])
                n += 2
            else:
                for arg2 in arg:
                    params[n % 2].append(arg2)
                    n += 1
        else:
            params[n % 2].append(arg)
            n += 1
    len0 = len(params[0])
    len1 = len(params[1])
    if len1 < len0:
        params[1] += [None] * (len0 - len1)
    elif len0 < len1:
        params[0] += [None] * (len1 - len0)
    fonts = []
    for font, format in zip(params[0], params[1]):
        if format:
            fonts.append('%s format("%s")' % (__font_url(font, inline=inline), StringValue(format).value))
        else:
            fonts.append(__font_url(font, inline=inline))
    return ListValue(fonts)


def _font_url(path, only_path=False, cache_buster=True):
    """
    Generates a path to an asset found relative to the project's font directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    return __font_url(path, only_path, cache_buster, False)


def _font_files(*args):
    return __font_files(args, inline=False)


def _inline_font_files(*args):
    return __font_files(args, inline=True)


def __image_url(path, only_path=False, cache_buster=True, dst_color=None, src_color=None, inline=False, mime_type=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    src_color - a list of or a single color to be replaced by each corresponding dst_color colors
    spacing - spaces to be added to the image
    collapse_x, collapse_y - collapsable (layered) image of the given size (x, y)
    """
    if inline or dst_color or spacing:
        if not Image:
            raise Exception("Images manipulation require PIL")
    filepath = StringValue(path).value
    mime_type = inline and (StringValue(mime_type).value or mimetypes.guess_type(filepath)[0])
    path = None
    if callable(STATIC_ROOT):
        try:
            _file, _storage = list(STATIC_ROOT(filepath))[0]
            d_obj = _storage.modified_time(_file)
            filetime = int(time.mktime(d_obj.timetuple()))
            if inline or dst_color or spacing:
                path = _storage.open(_file)
        except:
            filetime = 'NA'
    else:
        _path = os.path.join(STATIC_ROOT, filepath.strip('/'))
        if os.path.exists(_path):
            filetime = int(os.path.getmtime(_path))
            if inline or dst_color or spacing:
                path = open(_path, 'rb')
        else:
            filetime = 'NA'
    BASE_URL = STATIC_URL
    if path:
        dst_colors = dst_color
        if isinstance(dst_colors, ListValue):
            dst_colors = [list(ColorValue(v).value[:3]) for n, v in dst_colors.items() if v]
        else:
            dst_colors = [list(ColorValue(dst_colors).value[:3])] if dst_colors else []

        src_colors = src_color
        if isinstance(src_colors, ListValue):
            src_colors = [tuple(ColorValue(v).value[:3]) if v else (0, 0, 0) for n, v in src_colors.items()]
        else:
            src_colors = [tuple(ColorValue(src_colors).value[:3]) if src_colors else (0, 0, 0)]

        len_colors = max(len(dst_colors), len(src_colors))
        dst_colors = (dst_colors * len_colors)[:len_colors]
        src_colors = (src_colors * len_colors)[:len_colors]

        if isinstance(spacing, ListValue):
            spacing = [int(NumberValue(v).value) for n, v in spacing.items()]
        else:
            spacing = [int(NumberValue(spacing).value)]
        spacing = (spacing * 4)[:4]

        file_name, file_ext = os.path.splitext(os.path.normpath(filepath).replace('\\', '_').replace('/', '_'))
        key = (filetime, src_color, dst_color, spacing)
        key = file_name + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + file_ext
        asset_path = os.path.join(ASSETS_ROOT, asset_file)

        if os.path.exists(asset_path):
            filepath = asset_file
            BASE_URL = ASSETS_URL
            if inline:
                path = open(asset_path, 'rb')
                url = 'data:' + mime_type + ';base64,' + base64.b64encode(path.read())
            else:
                url = '%s%s' % (BASE_URL, filepath)
                if cache_buster:
                    filetime = int(os.path.getmtime(asset_path))
                    url = add_cache_buster(url, filetime)
        else:
            image = Image.open(path)
            width, height = collapse_x or image.size[0], collapse_y or image.size[1]
            new_image = Image.new(
                mode='RGBA',
                size=(width + spacing[1] + spacing[3], height + spacing[0] + spacing[2]),
                color=(0, 0, 0, 0)
            )
            for i, dst_color in enumerate(dst_colors):
                src_color = src_colors[i]
                pixdata = image.load()
                for _y in xrange(image.size[1]):
                    for _x in xrange(image.size[0]):
                        pixel = pixdata[_x, _y]
                        if pixel[:3] == src_color:
                            pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
            iwidth, iheight = image.size
            if iwidth != width or iheight != height:
                cy = 0
                while cy < iheight:
                    cx = 0
                    while cx < iwidth:
                        cropped_image = image.crop((cx, cy, cx + width, cy + height))
                        new_image.paste(cropped_image, (int(spacing[3]), int(spacing[0])), cropped_image)
                        cx += width
                    cy += height
            else:
                new_image.paste(image, (int(spacing[3]), int(spacing[0])))

            if not inline:
                try:
                    new_image.save(asset_path)
                    filepath = asset_file
                    BASE_URL = ASSETS_URL
                    if cache_buster:
                        filetime = int(os.path.getmtime(asset_path))
                except IOError:
                    log.exception("Error while saving image")
                    inline = True  # Retry inline version
                url = '%s%s' % (ASSETS_URL, asset_file)
                if cache_buster:
                    url = add_cache_buster(url, filetime)
            if inline:
                output = StringIO()
                new_image.save(output, format='PNG')
                contents = output.getvalue()
                output.close()
                url = 'data:' + mime_type + ';base64,' + base64.b64encode(contents)
    else:
        url = '%s%s' % (BASE_URL, filepath)
        if cache_buster:
            url = add_cache_buster(url, filetime)

    if not only_path:
        url = 'url("%s")' % escape(url)
    return StringValue(url)


def _inline_image(image, mime_type=None, dst_color=None, src_color=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    Embeds the contents of a file directly inside your stylesheet, eliminating
    the need for another HTTP request. For small files such images or fonts,
    this can be a performance benefit at the cost of a larger generated CSS
    file.
    """
    return __image_url(image, False, False, dst_color, src_color, True, mime_type, spacing, collapse_x, collapse_y)


def _image_url(path, only_path=False, cache_buster=True, dst_color=None, src_color=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    Generates a path to an asset found relative to the project's images
    directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    return __image_url(path, only_path, cache_buster, dst_color, src_color, False, None, spacing, collapse_x, collapse_y)


def _image_width(image):
    """
    Returns the width of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    filepath = StringValue(image).value
    path = None
    try:
        width = sprite_images[filepath][0]
    except KeyError:
        width = 0
        if callable(STATIC_ROOT):
            try:
                _file, _storage = list(STATIC_ROOT(filepath))[0]
                path = _storage.open(_file)
            except:
                pass
        else:
            _path = os.path.join(STATIC_ROOT, filepath.strip('/'))
            if os.path.exists(_path):
                path = open(_path, 'rb')
        if path:
            image = Image.open(path)
            size = image.size
            width = size[0]
            sprite_images[filepath] = size
    return NumberValue(width, 'px')


def _image_height(image):
    """
    Returns the height of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    filepath = StringValue(image).value
    path = None
    try:
        height = sprite_images[filepath][1]
    except KeyError:
        height = 0
        if callable(STATIC_ROOT):
            try:
                _file, _storage = list(STATIC_ROOT(filepath))[0]
                path = _storage.open(_file)
            except:
                pass
        else:
            _path = os.path.join(STATIC_ROOT, filepath.strip('/'))
            if os.path.exists(_path):
                path = open(_path, 'rb')
        if path:
            image = Image.open(path)
            size = image.size
            height = size[1]
            sprite_images[filepath] = size
    return NumberValue(height, 'px')


################################################################################


def __position(opposite, p):
    pos = []
    hrz = vrt = None
    nums = [v for v in p if isinstance(v, NumberValue)]

    if 'left' in p:
        hrz = 'right' if opposite else 'left'
    elif 'right' in p:
        hrz = 'left' if opposite else 'right'
    elif 'center' in p:
        hrz = 'center'

    if 'top' in p:
        vrt = 'bottom' if opposite else 'top'
    elif 'bottom' in p:
        vrt = 'top' if opposite else 'bottom'
    elif 'center' in p:
        hrz = 'center'

    if hrz == vrt:
        vrt = None

    if hrz is not None:
        pos.append(hrz)
    elif len(nums):
        pos.append(nums.pop(0))
    if vrt is not None:
        pos.append(vrt)
    elif len(nums):
        pos.append(nums.pop(0))
    return ListValue(pos + nums)


def _position(p):
    return __position(False, p)


def _opposite_position(p):
    return __position(True, p)


def _grad_point(*p):
    pos = set()
    hrz = vrt = NumberValue(0.5, '%')
    for _p in p:
        pos.update(StringValue(_p).value.split())
    if 'left' in pos:
        hrz = NumberValue(0, '%')
    elif 'right' in pos:
        hrz = NumberValue(1, '%')
    if 'top' in pos:
        vrt = NumberValue(0, '%')
    elif 'bottom' in pos:
        vrt = NumberValue(1, '%')
    return ListValue(v for v in (hrz, vrt) if v is not None)


################################################################################


def __compass_list(*args):
    separator = None
    if len(args) == 1 and isinstance(args[0], (list, tuple, ListValue)):
        args = ListValue(args[0]).values()
    else:
        separator = ','
    ret = ListValue(args)
    if separator:
        ret['_'] = separator
    return ret


def __compass_space_list(*lst):
    """
    If the argument is a list, it will return a new list that is space delimited
    Otherwise it returns a new, single element, space-delimited list.
    """
    ret = __compass_list(*lst)
    ret.value.pop('_', None)
    return ret


def _blank(*objs):
    """Returns true when the object is false, an empty string, or an empty list"""
    for o in objs:
        if bool(o):
            return BooleanValue(False)
    return BooleanValue(True)


def _compact(*args):
    """Returns a new list after removing any non-true values"""
    ret = {}
    if len(args) == 1:
        args = args[0]
        if isinstance(args, ListValue):
            args = args.value
        if isinstance(args, dict):
            for i, item in args.items():
                if False if isinstance(item, basestring) and _undefined_re.match(item) else bool(item):
                    ret[i] = item
        elif False if isinstance(args, basestring) and _undefined_re.match(args) else bool(args):
            ret[0] = args
    else:
        ret['_'] = ','
        for i, item in enumerate(args):
            if False if isinstance(item, basestring) and _undefined_re.match(item) else bool(item):
                ret[i] = item
    if isinstance(args, ListValue):
        args = args.value
    if isinstance(args, dict):
        separator = args.get('_', None)
        if separator is not None:
            ret['_'] = separator
    return ListValue(ret)


def _reject(lst, *values):
    """Removes the given values from the list"""
    ret = {}
    if not isinstance(lst, ListValue):
        lst = ListValue(lst)
    lst = lst.value
    if len(values) == 1:
        values = values[0]
        if isinstance(values, ListValue):
            values = values.value.values()
    for i, item in lst.items():
        if item not in values:
            ret[i] = item
    separator = lst.get('_', None)
    if separator is not None:
        ret['_'] = separator
    return ListValue(ret)


def __compass_slice(lst, start_index, end_index=None):
    start_index = NumberValue(start_index).value
    end_index = NumberValue(end_index).value if end_index is not None else None
    ret = {}
    lst = ListValue(lst).value
    for i, item in lst.items():
        if not isinstance(i, int):
            if i == '_':
                ret[i] = item
        elif i > start_index and end_index is None or i <= end_index:
            ret[i] = item
    return ListValue(ret)


def _first_value_of(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0])
    ret = ListValue(lst).first()
    return ret.__class__(ret)


def _nth(lst, n=1):
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


def _join(lst1, lst2, separator=None):
    ret = ListValue(lst1)
    lst2 = ListValue(lst2).value
    lst_len = len(ret.value)
    ret.value.update((k + lst_len if isinstance(k, int) else k, v) for k, v in lst2.items())
    if separator is not None:
        separator = StringValue(separator).value
        if separator:
            ret.value['_'] = separator
    return ret


def _length(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst)
    return NumberValue(len(lst))


def _max(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst).value
    return max(lst.values())


def _min(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, ListValue)):
        lst = ListValue(lst[0]).values()
    lst = ListValue(lst).value
    return min(lst.values())


def _append(lst, val, separator=None):
    separator = separator and StringValue(separator).value
    ret = ListValue(lst, separator)
    val = ListValue(val)
    for v in val:
        ret.value[len(ret)] = v
    return ret


################################################################################


def _prefixed(prefix, *args):
    to_fnct_str = 'to_' + to_str(prefix).replace('-', '_')
    for arg in args:
        if isinstance(arg, ListValue):
            for k, iarg in arg.value.items():
                if hasattr(iarg, to_fnct_str):
                    return BooleanValue(True)
        else:
            if hasattr(arg, to_fnct_str):
                return BooleanValue(True)
    return BooleanValue(False)


def _prefix(prefix, *args):
    to_fnct_str = 'to_' + to_str(prefix).replace('-', '_')
    args = list(args)
    for i, arg in enumerate(args):
        if isinstance(arg, ListValue):
            _value = {}
            for k, iarg in arg.value.items():
                to_fnct = getattr(iarg, to_fnct_str, None)
                if to_fnct:
                    _value[k] = to_fnct()
                else:
                    _value[k] = iarg
            args[i] = ListValue(_value)
        else:
            to_fnct = getattr(arg, to_fnct_str, None)
            if to_fnct:
                args[i] = to_fnct()
    if len(args) == 1:
        return args[0]
    return ListValue(args, ',')


def __moz(*args):
    return _prefix('_moz', *args)


def __svg(*args):
    return _prefix('_svg', *args)


def __css2(*args):
    return _prefix('_css2', *args)


def __pie(*args):
    return _prefix('_pie', *args)


def __webkit(*args):
    return _prefix('_webkit', *args)


def __owg(*args):
    return _prefix('_owg', *args)


def __khtml(*args):
    return _prefix('_khtml', *args)


def __ms(*args):
    return _prefix('_ms', *args)


def __o(*args):
    return _prefix('_o', *args)

################################################################################


def _percentage(value):
    value = NumberValue(value)
    value.units = {'%': _units_weights.get('%', 1), '_': '%'}
    return value


def _unitless(value):
    value = NumberValue(value)
    return BooleanValue(not bool(value.unit))


def _unquote(*args):
    return StringValue(' '.join([StringValue(s).value for s in args]))


def _quote(*args):
    return QuotedStringValue(' '.join([StringValue(s).value for s in args]))


def _pi():
    return NumberValue(math.pi)


def _comparable(number1, number2):
    n1, n2 = NumberValue(number1), NumberValue(number2)
    type1 = _conv_type.get(n1.unit)
    type2 = _conv_type.get(n2.unit)
    return BooleanValue(type1 == type2)


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


def _if(condition, if_true, if_false=''):
    condition = bool(False if not condition or isinstance(condition, basestring) and (condition in ('0', 'false', 'undefined') or _variable_re.match(condition)) else condition)
    return if_true.__class__(if_true) if condition else if_true.__class__(if_false)


def _unit(number):  # -> px, em, cm, etc.
    unit = NumberValue(number).unit
    return StringValue(unit)

# Parser/functions map:
fnct = {
    'grid-image:4': _grid_image,
    'grid-image:5': _grid_image,
    'image-color:1': _image_color,
    'image-color:2': _image_color,
    'image-color:3': _image_color,
    'sprite-map:1': _sprite_map,
    'sprite-names:1': _sprites,
    'sprites:1': _sprites,
    'sprite:2': _sprite,
    'sprite:3': _sprite,
    'sprite:4': _sprite,
    'sprite-map-name:1': _sprite_map_name,
    'sprite-file:2': _sprite_file,
    'sprite-url:1': _sprite_url,
    'sprite-position:2': _sprite_position,
    'sprite-position:3': _sprite_position,
    'sprite-position:4': _sprite_position,
    'background-noise:0': _background_noise,
    'background-noise:1': _background_noise,
    'background-noise:2': _background_noise,
    'background-noise:3': _background_noise,
    'background-noise:4': _background_noise,

    'image-url:1': _image_url,
    'image-url:2': _image_url,
    'image-url:3': _image_url,
    'image-url:4': _image_url,
    'image-url:5': _image_url,
    'inline-image:1': _inline_image,
    'inline-image:2': _inline_image,
    'image-width:1': _image_width,
    'image-height:1': _image_height,

    'stylesheet-url:1': _stylesheet_url,
    'stylesheet-url:2': _stylesheet_url,

    'font-url:1': _font_url,
    'font-url:2': _font_url,

    'font-files:n': _font_files,
    'inline-font-files:n': _inline_font_files,

    'opposite-position:n': _opposite_position,
    'grad-point:n': _grad_point,
    'grad-end-position:n': _grad_end_position,
    'color-stops:n': _color_stops,
    'color-stops-in-percentages:n': _color_stops_in_percentages,
    'grad-color-stops:n': _grad_color_stops,
    'radial-gradient:n': _radial_gradient,
    'linear-gradient:n': _linear_gradient,
    'radial-svg-gradient:n': _radial_svg_gradient,
    'linear-svg-gradient:n': _linear_svg_gradient,

    'opacify:2': _opacify,
    'fadein:2': _opacify,
    'fade-in:2': _opacify,
    'transparentize:2': _transparentize,
    'fadeout:2': _transparentize,
    'fade-out:2': _transparentize,
    'lighten:2': _lighten,
    'darken:2': _darken,
    'saturate:2': _saturate,
    'desaturate:2': _desaturate,
    'grayscale:1': _grayscale,
    'greyscale:1': _grayscale,
    'adjust-hue:2': _adjust_hue,
    'adjust-lightness:2': _adjust_lightness,
    'adjust-saturation:2': _adjust_saturation,
    'scale-lightness:2': _scale_lightness,
    'scale-saturation:2': _scale_saturation,
    'adjust-color:n': _adjust_color,
    'scale-color:n': _scale_color,
    'change-color:n': _change_color,
    'spin:2': _adjust_hue,
    'complement:1': _complement,
    'invert:1': _invert,
    'mix:2': _mix,
    'mix:3': _mix,
    'hsl:3': _hsl,
    'hsl:1': _hsl2,
    'hsla:1': _hsla2,
    'hsla:2': _hsla2,
    'hsla:4': _hsla,
    'rgb:3': _rgb,
    'rgb:1': _rgb2,
    'rgba:1': _rgba2,
    'rgba:2': _rgba2,
    'rgba:4': _rgba,
    'ie-hex-str:1': _ie_hex_str,

    'red:1': _red,
    'green:1': _green,
    'blue:1': _blue,
    'alpha:1': _alpha,
    'opacity:1': _alpha,
    'hue:1': _hue,
    'saturation:1': _saturation,
    'lightness:1': _lightness,

    'prefixed:n': _prefixed,
    'prefix:n': _prefix,
    '-moz:n': __moz,
    '-svg:n': __svg,
    '-css2:n': __css2,
    '-pie:n': __pie,
    '-webkit:n': __webkit,
    '-owg:n': __owg,
    '-ms:n': __ms,
    '-o:n': __o,

    '-compass-list:n': __compass_list,
    '-compass-space-list:n': __compass_space_list,
    'blank:n': _blank,
    'compact:n': _compact,
    'reject:n': _reject,
    '-compass-slice:3': __compass_slice,
    'nth:2': _nth,
    'max:n': _max,
    'min:n': _min,
    '-compass-nth:2': _nth,
    'first-value-of:n': _first_value_of,
    'join:2': _join,
    'join:3': _join,
    'length:n': _length,
    '-compass-list-size:n': _length,
    'append:2': _append,
    'append:3': _append,

    'nest:n': _nest,
    'append-selector:2': _append_selector,
    'headers:0': _headers,
    'headers:1': _headers,
    'headers:2': _headers,
    'headings:0': _headers,
    'headings:1': _headers,
    'headings:2': _headers,
    'enumerate:3': _enumerate,
    'enumerate:4': _enumerate,
    'range:1': _range,
    'range:2': _range,

    'percentage:1': _percentage,
    'unitless:1': _unitless,
    'unit:1': _unit,
    'if:2': _if,
    'if:3': _if,
    'type-of:1': _type_of,
    'comparable:2': _comparable,
    'elements-of-type:1': _elements_of_type,
    'quote:n': _quote,
    'unquote:n': _unquote,
    'escape:1': _unquote,
    'e:1': _unquote,

    'sin:1': Value._wrap(math.sin),
    'cos:1': Value._wrap(math.cos),
    'tan:1': Value._wrap(math.tan),
    'abs:1': Value._wrap(abs),
    'round:1': Value._wrap(round),
    'ceil:1': Value._wrap(math.ceil),
    'floor:1': Value._wrap(math.floor),
    'pi:0': _pi,
}
for u in _units:
    fnct[u + ':2'] = _convert_to

for str_key, func in fnct.items():
    scss_builtins.legacy_register(str_key, func)
