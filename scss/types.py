from __future__ import absolute_import
from __future__ import print_function

import colorsys
import operator

import six

from scss.cssdefs import COLOR_LOOKUP, COLOR_NAMES, ZEROABLE_UNITS, convert_units_to_base_units
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
    def __bool__(self):
        return True

    def __nonzero__(self):
        # Py 2's name for __bool__
        return self.__bool__()

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

    def __truediv__(self, other):
        return self._do_op(self, other, operator.__truediv__)

    def __rtruediv__(self, other):
        return self._do_op(other, self, operator.__truediv__)

    def __div__(self, other):
        return self.__truediv__(other)

    def __rdiv__(self, other):
        return self.__rtruediv__(other)

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

    def render(self, compress=False, short_colors=False):
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

    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Null)

    def render(self, compress=False, short_colors=False):
        return 'null'


class BooleanValue(Value):
    sass_type_name = u'bool'

    def __init__(self, value):
        self.value = bool(value)

    def __str__(self):
        return 'true' if self.value else 'false'

    def __bool__(self):
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

    def render(self, compress=False, short_colors=False):
        if self.value:
            return 'true'
        else:
            return 'false'


class NumberValue(Value):
    sass_type_name = u'number'

    def __init__(self, amount, unit_numer=(), unit_denom=(), unit=None):
        if isinstance(amount, NumberValue):
            assert not unit and not unit_numer and not unit_denom
            self.value = amount.value
            self.unit_numer = amount.unit_numer
            self.unit_denom = amount.unit_denom
            return

        if not isinstance(amount, (int, float)):
            raise TypeError("Expected number, got %r" % (amount,))

        self.value = amount

        if unit is not None:
            unit_numer = unit_numer + (unit,)

        self.unit_numer = tuple(sorted(unit_numer))
        self.unit_denom = tuple(sorted(unit_denom))

    def __repr__(self):
        full_unit = ' * '.join(self.unit_numer)
        if self.unit_denom:
            full_unit += ' / '
            full_unit += ' * '.join(self.unit_denom)

            if full_unit:
                full_unit = ' ' + full_unit

        return '<%s: %r%s>' % (self.__class__.__name__, self.value, full_unit)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return self * NumberValue(-1)

    def __pos__(self):
        return self

    def __str__(self):
        return self.render()

    def __eq__(self, other):
        if not isinstance(other, NumberValue):
            return BooleanValue(False)

        return self._compare(other, operator.__eq__)

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

        left = self.to_base_units()
        right = other.to_base_units()

        if left.unit_numer != right.unit_numer or left.unit_denom != right.unit_denom:
            raise ValueError("Can't reconcile units: %r and %r" % (self, other))

        return op(left.value, right.value)

    def __mul__(self, other):
        if not isinstance(other, NumberValue):
            return NotImplemented

        amount = self.value * other.value
        # TODO cancel out units if appropriate
        numer = self.unit_numer + other.unit_numer
        denom = self.unit_denom + other.unit_denom

        return NumberValue(amount, unit_numer=numer, unit_denom=denom)

    def __truediv__(self, other):
        if not isinstance(other, NumberValue):
            return NotImplemented

        amount = self.value / other.value
        numer = list(self.unit_numer + other.unit_denom)
        denom = list(self.unit_denom + other.unit_numer)

        # Cancel out like units
        # TODO cancel out relatable units too
        numer2 = []
        for unit in numer:
            try:
                denom.remove(unit)
            except ValueError:
                numer2.append(unit)

        return NumberValue(amount, unit_numer=numer2, unit_denom=denom)

    def __add__(self, other):
        # Numbers auto-cast to strings when added to other strings
        if isinstance(other, String):
            return String(self.render(), quotes=None) + other

        return self._add_sub(other, operator.add)

    def __sub__(self, other):
        return self._add_sub(other, operator.sub)

    def _add_sub(self, other, op):
        """Implements both addition and subtraction."""
        if not isinstance(other, NumberValue):
            return NotImplemented

        # If either side is unitless, inherit the other side's units.  Skip all
        # the rest of the conversion math, too.
        if self.is_unitless or other.is_unitless:
            return NumberValue(
                op(self.value, other.value),
                self.unit_numer or other.unit_numer,
                self.unit_denom or other.unit_denom,
            )

        # Reduce both operands to the same units
        left = self.to_base_units()
        right = other.to_base_units()

        if left.unit_numer != right.unit_numer or left.unit_denom != right.unit_denom:
            raise ValueError("Can't reconcile units: %r and %r" % (self, other))

        new_amount = op(left.value, right.value)

        # Convert back to the left side's units
        if left.value != 0:
            new_amount = new_amount * self.value / left.value

        return NumberValue(new_amount, self.unit_numer, self.unit_denom)


    ### Helper methods, mostly used internally

    def to_base_units(self):
        """Convert to a fixed set of "base" units.  The particular units are
        arbitrary; what's important is that they're consistent.

        Used for addition and comparisons.
        """
        # Convert to "standard" units, as defined by the conversions dict above
        amount = self.value

        numer_factor, numer_units = convert_units_to_base_units(self.unit_numer)
        denom_factor, denom_units = convert_units_to_base_units(self.unit_denom)

        return NumberValue(
            amount * numer_factor / denom_factor,
            numer_units,
            denom_units,
        )


    ### Utilities for public consumption

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
            sass_ret = cls(python_ret, unit=sass_arg.unit)
            return sass_ret

        return wrapped

    @property
    def unit(self):
        if self.unit_denom:
            raise TypeError

        if not self.unit_numer:
            return ''

        if len(self.unit_numer) != 1:
            raise TypeError

        return self.unit_numer[0]

    @property
    def has_simple_unit(self):
        """Returns True iff the unit is expressible in CSS, i.e., has no
        denominator and at most one unit in the numerator.
        """
        return len(self.unit_numer) <= 1 and not self.unit_denom

    @property
    def is_unitless(self):
        return not self.unit_numer and not self.unit_denom

    def render(self, compress=False, short_colors=False):
        if not self.has_simple_unit:
            raise ValueError("Can't express compound units in CSS: %r" % (self,))

        unit = self.unit

        if compress and unit in ZEROABLE_UNITS and self.value == 0:
            return '0'

        val = "%0.05f" % round(self.value, 5)
        val = val.rstrip('0').rstrip('.')

        if compress and val.startswith('0.'):
            # Strip off leading zero when compressing
            val = val[1:]

        return val + unit


class List(Value):
    """A list of other values.  May be delimited by commas or spaces.

    Lists of one item don't make much sense in CSS, but can exist in Sass.  Use ......

    Lists may also contain zero items, but these are forbidden from appearing
    in CSS output.
    """

    sass_type_name = u'list'

    def __init__(self, tokens, separator=None, use_comma=True):
        if isinstance(tokens, ListValue):
            tokens = tokens.value

        if not isinstance(tokens, (list, tuple)):
            raise TypeError("Expected list, got %r" % (tokens,))

        self.value = list(tokens)
        # TODO...
        self.use_comma = separator == ","

    @classmethod
    def maybe_new(cls, values, use_comma=True):
        """If `values` contains only one item, return that item.  Otherwise,
        return a List as normal.
        """
        if len(values) == 1:
            return values[0]
        else:
            return cls(values, use_comma=use_comma)

    def maybe(self):
        """If this List contains only one item, return it.  Otherwise, return
        the List.
        """
        if len(self.value) == 1:
            return self.value[0]
        else:
            return self

    @classmethod
    def from_maybe(cls, values, use_comma=True):
        """If `values` appears to not be a list, return a list containing it.
        Otherwise, return a List as normal.
        """
        if not isinstance(values, (list, tuple, List)):
            values = [values]

        return cls(values, use_comma=use_comma)

    @classmethod
    def from_maybe_starargs(cls, args):
        """If `args` has one element which appears to be a list, return it.
        Otherwise, return a list as normal.

        Mainly used by Sass function implementations that predate `...`
        support, so they can accept both a list of arguments and a single list
        stored in a variable.
        """
        if len(args) == 1:
            if isinstance(args[0], cls):
                return args[0]
            elif isinstance(args[0], (list, tuple)):
                return cls(args[0])

        return cls(args)

    @property
    def separator(self):
        return self.value.get('_', '')

    def delimiter(self, compress=False):
        if self.use_comma:
            if compress:
                return ','
            else:
                return ', '
        else:
            return ' '

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

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return self.render()

    def __iter__(self):
        return iter(self.value)

    def values(self):
        return self.value

    def keys(self):
        return range(len(self.value))

    def items(self):
        return enumerate(self.value)

    def __getitem__(self, key):
        return self.value[key]

    def render(self, compress=False, short_colors=False):
        delim = self.delimiter(compress)

        return delim.join(
            item.render(compress=compress, short_colors=short_colors)
            for item in self.value
        )


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

    @classmethod
    def from_name(cls, name):
        """Build a Color from a CSS color name."""
        self = cls.__new__(cls)  # TODO
        self.tokens = ParserValue(name)

        r, g, b, a = COLOR_NAMES[name]

        self.value = r, g, b, a
        if a == 1.0:
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

    def render(self, compress=False, short_colors=False):
        if not compress and not short_colors:
            return self.__str__()

        candidates = []

        # TODO this assumes CSS resolution is 8-bit per channel, but so does
        # Ruby.
        r, g, b, a = self.value
        r, g, b = int(round(r)), int(round(g)), int(round(b))

        # Try color name
        key = r, g, b, a
        if key in COLOR_LOOKUP:
            candidates.append(COLOR_LOOKUP[key])

        if a == 1:
            # Hex is always shorter than function notation
            if all(ch % 17 == 0 for ch in (r, g, b)):
                candidates.append("#%1x%1x%1x" % (r // 17, g // 17, b // 17))
            else:
                candidates.append("#%02x%02x%02x" % (r, g, b))
        else:
            # Can't use hex notation for RGBA
            if compress:
                sp = ''
            else:
                sp = ' '
            candidates.append("rgba(%d,%s%d,%s%d,%s%.2g)" % (r, sp, g, sp, b, sp, a))

        return min(candidates, key=len)


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

        if isinstance(value, six.binary_type):
            # TODO this blows!  need to be unicode-clean so this never happens.
            value = value.decode('ascii')

        if not isinstance(value, six.text_type):
            raise TypeError("Expected string, got {0!r}".format(value))

        # TODO probably disallow creating an unquoted string outside a
        # set of chars like [-a-zA-Z0-9]+

        if six.PY3:
            self.value = value
        else:
            # TODO not unicode clean on 2 yet...
            self.value = value.encode('ascii')
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

    def render(self, compress=False, short_colors=False):
        return self.__str__()


# Backwards-compatibility.
ListValue = List
QuotedStringValue = String
StringValue = String
