from __future__ import absolute_import

import colorsys
import operator

from scss.cssdefs import _conv_factor, _conv_type, _units_weights
from scss.util import escape, to_float, to_str


################################################################################
# pyScss data types:

class ParserValue(object):
    def __init__(self, value):
        self.value = value


class Value(object):
    is_null = False
    sass_type_name = u'unknown'

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, repr(self.value))

    # Sass values are all true, except for booleans and nulls
    def __nonzero__(self):
        return True

    ### NOTE: From here on down, the operators are exposed to Sass code and
    ### thus should ONLY return Sass types

    # Reasonable default for equality
    def __eq__(self, other):
        return BooleanValue(
            type(self) == type(other) and self.value == other.value)

    def __ne__(self, other):
        return BooleanValue(not self.__eq__(other))

    # Only numbers support ordering
    def __lt__(self, other):
        raise TypeError("Can't compare %r with %r" % (self, other))

    def __le__(self, other):
        raise TypeError("Can't compare %r with %r" % (self, other))

    def __gt__(self, other):
        raise TypeError("Can't compare %r with %r" % (self, other))

    def __ge__(self, other):
        raise TypeError("Can't compare %r with %r" % (self, other))

    # Math ops
    def __add__(self, other):
        return self._do_op(self, other, operator.__add__)

    def __radd__(self, other):
        return self._do_op(other, self, operator.__add__)

    def __div__(self, other):
        return self._do_op(self, other, operator.__div__)

    def __rdiv__(self, other):
        return self._do_op(other, self, operator.__div__)

    def __sub__(self, other):
        return self._do_op(self, other, operator.__sub__)

    def __rsub__(self, other):
        return self._do_op(other, self, operator.__sub__)

    def __mul__(self, other):
        return self._do_op(self, other, operator.__mul__)

    def __rmul__(self, other):
        return self._do_op(other, self, operator.__mul__)

    def merge(self, obj):
        if isinstance(obj, Value):
            self.value = obj.value
        else:
            self.value = obj
        return self

    def render(self):
        return self.__str__()


class Null(Value):
    is_null = True
    sass_type_name = u'null'

    def __init__(self):
        pass

    def __str__(self):
        return 'null'

    def __repr__(self):
        return "<%s>" % (type(self).__name__,)

    def __nonzero__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Null)


class BooleanValue(Value):
    sass_type_name = u'bool'

    def __init__(self, value):
        self.value = bool(value)

    def __str__(self):
        return 'true' if self.value else 'false'

    def __nonzero__(self):
        return self.value

    @classmethod
    def _do_op(cls, first, second, op):
        if isinstance(first, ListValue) and isinstance(second, ListValue):
            ret = ListValue(first)
            for k, v in ret.items():
                try:
                    ret.value[k] = op(ret.value[k], second.value[k])
                except KeyError:
                    pass
            return ret
        if isinstance(first, ListValue):
            ret = ListValue(first)
            for k, v in ret.items():
                ret.value[k] = op(ret.value[k], second)
            return ret
        if isinstance(second, ListValue):
            ret = ListValue(second)
            for k, v in ret.items():
                ret.value[k] = op(first, ret.value[k])
            return ret

        first = BooleanValue(first)
        second = BooleanValue(second)
        val = op(first.value, second.value)
        return BooleanValue(val)


class NumberValue(Value):
    sass_type_name = u'number'

    def __init__(self, tokens, type=None):
        self.tokens = tokens
        self.units = {}
        if tokens is None:
            self.value = 0.0
        elif isinstance(tokens, NumberValue):
            self.value = tokens.value
            self.units = tokens.units.copy()
            if tokens.units:
                type = None
        elif isinstance(tokens, (StringValue, basestring)):
            tokens = getattr(tokens, 'value', tokens)
            try:
                if tokens and tokens[-1] == '%':
                    self.value = to_float(tokens[:-1]) / 100.0
                    self.units = {'%': _units_weights.get('%', 1), '_': '%'}
                else:
                    self.value = to_float(tokens)
            except ValueError:
                raise ValueError("Value is not a Number! (%s)" % tokens)
        elif isinstance(tokens, (int, float)):
            # TODO i don't like this; should store the original and only divide
            # when converting.  requires fixing __str__ though
            self.value = float(tokens) * _conv_factor.get(type, 1.0)
        else:
            raise ValueError("Can't convert to CSS number: %s" % repr(tokens))
        if type is not None:
            self.units = {type: _units_weights.get(type, 1), '_': type}

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, repr(self.value), repr(self.units))

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return self * NumberValue(-1)

    def __pos__(self):
        return self

    def __str__(self):
        unit = self.unit
        val = self.value / _conv_factor.get(unit, 1.0)
        val = to_str(val) + unit
        return val

    def __eq__(self, other):
        if not isinstance(other, NumberValue):
            return BooleanValue(False)

        return BooleanValue(self.value == other.value and self.unit == other.unit)

    def __lt__(self, other):
        return self._compare(other, operator.__lt__)

    def __le__(self, other):
        return self._compare(other, operator.__le__)

    def __gt__(self, other):
        return self._compare(other, operator.__gt__)

    def __ge__(self, other):
        return self._compare(other, operator.__ge__)

    def _compare(self, other, op):
        if not isinstance(other, NumberValue):
            raise TypeError("Can't compare %r and %r" % (self, other))

        # TODO this will need to get more complicated for full unit support
        first = NumberValue(self)
        second = NumberValue(other)
        first_type = _conv_type.get(first.unit)
        second_type = _conv_type.get(second.unit)
        if first_type == second_type or first_type is None or second_type is None:
            return op(first.value, second.value)
        else:
            return op(first_type, second_type)

    @classmethod
    def _do_op(cls, first, second, op):
        if op == operator.__add__ and isinstance(second, String):
            return String(first.render(), quotes=None) + second

        first_unit = first.unit
        second_unit = second.unit
        if op == operator.__add__ or op == operator.__sub__:
            if first_unit == '%' and not second_unit:
                second.units = {'%': _units_weights.get('%', 1), '_': '%'}
                second.value /= 100.0
            elif first_unit == '%' and second_unit != '%':
                first = NumberValue(second) * first.value
            elif second_unit == '%' and not first_unit:
                first.units = {'%': _units_weights.get('%', 1), '_': '%'}
                first.value /= 100.0
            elif second_unit == '%' and first_unit != '%':
                second = NumberValue(first) * second.value
        elif op == operator.__div__:
            if first_unit and first_unit == second_unit:
                first.units = {}
                second.units = {}

        val = op(first.value, second.value)

        ret = NumberValue(None).merge(first)
        ret = ret.merge(second)
        ret.value = val
        return ret

    @classmethod
    def wrap_python_function(cls, fn):
        """Wraps an unary Python math function, translating the argument from
        Sass to Python on the way in, and vice versa for the return value.

        Used to wrap simple Python functions like `ceil`, `floor`, etc.
        """
        def wrapped(sass_arg):
            # TODO enforce no units for trig?
            python_arg = sass_arg.value
            python_ret = fn(python_arg)
            sass_ret = cls(python_ret, type=sass_arg.unit)
            return sass_ret

        return wrapped

    def merge(self, obj):
        obj = NumberValue(obj)
        self.value = obj.value
        for unit, val in obj.units.items():
            if unit != '_':
                self.units.setdefault(unit, 0)
                self.units[unit] += val
        unit = obj.unit
        if _units_weights.get(self.units.get('_'), 1) <= _units_weights.get(unit, 1):
            self.units['_'] = unit
        return self

    @property
    def unit(self):
        unit = ''
        if self.units:
            if '_'in self.units:
                units = self.units.copy()
                _unit = units.pop('_')
                units.setdefault(_unit, 0)
                units[_unit] += _units_weights.get(_unit, 1)  # Give more weight to the first unit ever set
            else:
                units = self.units
            units = sorted(units, key=units.get)
            while len(units):
                unit = units.pop()
                if unit:
                    break
        return unit


class ListValue(Value):
    sass_type_name = u'list'

    def __init__(self, tokens, separator=None):
        self.tokens = tokens
        if tokens is None:
            self.value = {}
        elif isinstance(tokens, ListValue):
            self.value = tokens.value.copy()
        elif isinstance(tokens, Value):
            self.value = {0: tokens}
        elif isinstance(tokens, dict):
            self.value = self._reorder_list(tokens)
        elif isinstance(tokens, (list, tuple)):
            self.value = dict(enumerate(tokens))
        else:
            if isinstance(tokens, StringValue):
                tokens = tokens.value
            tokens = to_str(tokens)
            lst = [i for i in tokens.split() if i]
            if len(lst) == 1:
                lst = [i.strip() for i in lst[0].split(',') if i.strip()]
                if len(lst) > 1:
                    separator = ',' if separator is None else separator
                else:
                    lst = [tokens]
            self.value = dict(enumerate(lst))
        if separator is None:
            separator = self.value.pop('_', None)
        if separator:
            self.value['_'] = separator

    @classmethod
    def _do_op(cls, first, second, op):
        if isinstance(first, ListValue) and isinstance(second, ListValue):
            ret = ListValue(first)
            for k, v in ret.items():
                try:
                    ret.value[k] = op(ret.value[k], second.value[k])
                except KeyError:
                    pass
            return ret
        if isinstance(first, ListValue):
            ret = ListValue(first)
            for k, v in ret.items():
                ret.value[k] = op(ret.value[k], second)
            return ret
        if isinstance(second, ListValue):
            ret = ListValue(second)

            for k, v in ret.items():
                ret.value[k] = op(first, ret.value[k])
            return ret

    def _reorder_list(self, lst):
        return dict((i if isinstance(k, int) else k, v) for i, (k, v) in enumerate(sorted(lst.items())))

    def __nonzero__(self):
        return len(self)

    def __len__(self):
        return len(self.value) - (1 if '_' in self.value else 0)

    def __str__(self):
        return to_str(self.value)

    def __iter__(self):
        return iter(self.values())

    def values(self):
        return zip(*self.items())[1]

    def keys(self):
        return zip(*self.items())[0]

    def items(self):
        return sorted((k, v) for k, v in self.value.items() if k != '_')

    def __getitem__(self, key):
        return self.value[key]


class ColorValue(Value):
    sass_type_name = u'color'

    HEX2RGBA = {
        9: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), int(c[7:9], 16)),
        7: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 1.0),
        5: lambda c: (int(c[1] * 2, 16), int(c[2] * 2, 16), int(c[3] * 2, 16), int(c[4] * 2, 16)),
        4: lambda c: (int(c[1] * 2, 16), int(c[2] * 2, 16), int(c[3] * 2, 16), 1.0),
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.value = (0, 0, 0, 1)
        self.types = {}
        if tokens is None:
            self.value = (0, 0, 0, 1)
        elif isinstance(tokens, ParserValue):
            hex = tokens.value
            self.value = self.HEX2RGBA[len(hex)](hex)
            self.types = {'rgba': 1}
        elif isinstance(tokens, ColorValue):
            self.value = tokens.value
            self.types = tokens.types.copy()
        elif isinstance(tokens, NumberValue):
            val = tokens.value
            self.value = (val, val, val, 1)
        elif isinstance(tokens, (list, tuple)):
            c = tokens[:4]
            r = 255.0, 255.0, 255.0, 1.0
            c = [0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4)]
            self.value = tuple(c)
            type = tokens[-1]
            if type in ('rgb', 'rgba', 'hsl', 'hsla'):
                self.types = {type: 1}
        elif isinstance(tokens, (int, float)):
            val = float(tokens)
            self.value = (val, val, val, 1)
        else:
            if isinstance(tokens, StringValue):
                tokens = tokens.value
            tokens = to_str(tokens)
            tokens.replace(' ', '').lower()
            try:
                self.value = self.HEX2RGBA[len(tokens)](tokens)
            except:
                try:
                    val = to_float(tokens)
                    self.value = (val, val, val, 1)
                except ValueError:
                    try:
                        type, _, colors = tokens.partition('(')
                        colors = colors.rstrip(')')
                        if type in ('rgb', 'rgba'):
                            c = tuple(colors.split(','))
                            try:
                                c = [to_float(c[i]) for i in range(4)]
                                col = [0.0 if c[i] < 0 else 255.0 if c[i] > 255 else c[i] for i in range(3)]
                                col += [0.0 if c[3] < 0 else 1.0 if c[3] > 1 else c[3]]
                                self.value = tuple(col)
                                self.types = {type: 1}
                            except:
                                raise ValueError("Value is not a Color! (%s)" % tokens)
                        elif type in ('hsl', 'hsla'):
                            c = colors.split(',')
                            try:
                                c = [to_float(c[i]) for i in range(4)]
                                col = [c[0] % 360.0] / 360.0
                                col += [0.0 if c[i] < 0 else 1.0 if c[i] > 1 else c[i] for i in range(1, 4)]
                                self.value = tuple([c * 255.0 for c in colorsys.hls_to_rgb(col[0], 0.999999 if col[2] == 1 else col[2], 0.999999 if col[1] == 1 else col[1])] + [col[3]])
                                self.types = {type: 1}
                            except:
                                raise ValueError("Value is not a Color! (%s)" % tokens)
                        else:
                            raise ValueError("Value is not a Color! (%s)" % tokens)
                    except:
                        raise ValueError("Value is not a Color! (%s)" % tokens)

    @classmethod
    def from_rgb(cls, red, green, blue, alpha=1.0):
        self = cls.__new__(cls)  # TODO
        self.tokens = None
        # TODO really should store these things internally as 0-1
        self.value = (red * 255.0, green * 255.0, blue * 255.0, alpha)
        if alpha == 1.0:
            self.types = {'rgb': 1}
        else:
            self.types = {'rgba': 1}

        return self

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, repr(self.value), repr(self.types))

    def __str__(self):
        # TODO bit of a hack?
        if self.tokens is not None and isinstance(self.tokens, ParserValue):
            return self.tokens.value

        type = self.type
        c = self.value
        if type == 'hsl' or type == 'hsla' and c[3] == 1:
            h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
            return 'hsl(%s, %s%%, %s%%)' % (to_str(h * 360.0), to_str(s * 100.0), to_str(l * 100.0))
        if type == 'hsla':
            h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
            return 'hsla(%s, %s%%, %s%%, %s)' % (to_str(h * 360.0), to_str(s * 100.0), to_str(l * 100.0), to_str(c[3]))
        r, g, b = to_str(c[0]), to_str(c[1]), to_str(c[2])
        are_integral = True
        for n in c[:3]:
            # replicating old logic; perhaps needs rethinking
            n2 = round(n * 100, 1)
            if n2 != int(n2):
                are_integral = False
                break
        if c[3] == 1:
            if not are_integral:
                return 'rgb(%s%%, %s%%, %s%%)' % (to_str(c[0] * 100.0 / 255.0), to_str(c[1] * 100.0 / 255.0), to_str(c[2] * 100.0 / 255.0))
            return '#%02x%02x%02x' % (round(c[0]), round(c[1]), round(c[2]))
        if not are_integral:
            return 'rgba(%s%%, %s%%, %s%%, %s)' % (to_str(c[0] * 100.0 / 255.0), to_str(c[1] * 100.0 / 255.0), to_str(c[2] * 100.0 / 255.0), to_str(c[3]))
        return 'rgba(%d, %d, %d, %s)' % (round(c[0]), round(c[1]), round(c[2]), to_str(c[3]))

    def __eq__(self, other):
        if not isinstance(other, ColorValue):
            return BooleanValue(False)

        # Round to the nearest 5 digits for comparisons; corresponds roughly to
        # 16 bits per channel, the most that generally matters.  Otherwise
        # float errors make equality fail for HSL colors.
        left = tuple(round(n, 5) for n in self.value)
        right = tuple(round(n, 5) for n in other.value)
        return left == right

    @classmethod
    def _do_op(cls, first, second, op):
        first = ColorValue(first)
        second = ColorValue(second)
        val = [op(first.value[i], second.value[i]) for i in range(4)]
        val[3] = (first.value[3] + second.value[3]) / 2
        c = val
        r = 255.0, 255.0, 255.0, 1.0
        c = [0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4)]
        ret = ColorValue(None).merge(first).merge(second)
        ret.value = tuple(c)
        return ret

    def merge(self, obj):
        obj = ColorValue(obj)
        self.value = obj.value
        for type, val in obj.types.items():
            self.types.setdefault(type, 0)
            self.types[type] += val
        return self

    @property
    def type(self):
        type = ''
        if self.types:
            types = sorted(self.types, key=self.types.get)
            while len(types):
                type = types.pop()
                if type:
                    break
        return type


class String(Value):
    sass_type_name = u'string'

    """Represents both CSS quoted string values and CSS identifiers (such as
    `left`).

    Makes no distinction between single and double quotes, except that the same
    quotes are preserved on string literals that pass through unmodified.
    Otherwise, double quotes are used.
    """

    def __init__(self, value, quotes='"'):
        if isinstance(value, String):
            # TODO unclear if this should be here, but many functions rely on
            # it
            value = value.value
        elif isinstance(value, NumberValue):
            # TODO this may only be necessary in the case of __radd__ and
            # number values
            value = str(value)

        if isinstance(value, str):
            # TODO this blows!  need to be unicode-clean so this never happens.
            value = value.decode('ascii')

        if not isinstance(value, unicode):
            raise TypeError("Expected unicode, got {0!r}".format(value))

        # TODO probably disallow creating an unquoted string outside a
        # set of chars like [-a-zA-Z0-9]+

        self.value = value
        self.quotes = quotes

    def __str__(self):
        if self.quotes:
            return self.quotes + escape(self.value) + self.quotes
        else:
            return self.value

    def __eq__(self, other):
        return BooleanValue(isinstance(other, String) and self.value == other.value)

    def __add__(self, other):
        if isinstance(other, String):
            other_value = other.value
        else:
            other_value = other.render()

        return String(
            self.value + other_value,
            quotes='"' if self.quotes else None)


QuotedStringValue = String
StringValue = String
