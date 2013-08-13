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
        # Default behavior is to treat both sides like strings
        if isinstance(other, String):
            return String(self.render() + other.value, quotes=other.quotes)
        return String(self.render() + other.render())

    def __sub__(self, other):
        # Default behavior is to treat the whole expression like one string
        return String(self.render() + "-" + other.render())

    def __div__(self, other):
        return String(self.render() + "/" + other.render())

    # Sass types have no notion of floor vs true division
    def __truediv__(self, other):
        return self.__div__(other)

    def __floordiv__(self, other):
        return self.__div__(other)

    def __mul__(self, other):
        raise NotImplementedError

    def __pos__(self):
        return String("+" + self.render())

    def __neg__(self):
        return String("-" + self.render())

    def render(self, compress=False):
        return self.__str__()


class Null(Value):
    is_null = True
    sass_type_name = u'null'

    def __init__(self):
        pass

    def __str__(self):
        return self.sass_type_name

    def __repr__(self):
        return "<%s>" % (type(self).__name__,)

    def __hash__(self):
        return hash(None)

    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Null)

    def render(self, compress=False):
        return self.sass_type_name


class Undefined(Null):
    sass_type_name = u'undefined'


class BooleanValue(Value):
    sass_type_name = u'bool'

    def __init__(self, value):
        self.value = bool(value)

    def __str__(self):
        return 'true' if self.value else 'false'

    def __hash__(self):
        return hash(self.value)

    def __bool__(self):
        return self.value

    def render(self, compress=False):
        if self.value:
            return 'true'
        else:
            return 'false'


class Number(Value):
    sass_type_name = u'number'

    def __init__(self, amount, unit=None, unit_numer=(), unit_denom=()):
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

    def __hash__(self):
        return hash((self.value, self.unit_numer, self.unit_denom))

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

        return op(round(left.value, 5), round(right.value, 5))

    def __mul__(self, other):
        if not isinstance(other, NumberValue):
            return NotImplemented

        amount = self.value * other.value
        # TODO cancel out units if appropriate
        numer = self.unit_numer + other.unit_numer
        denom = self.unit_denom + other.unit_denom

        return NumberValue(amount, unit_numer=numer, unit_denom=denom)

    def __div__(self, other):
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
                unit_numer=self.unit_numer or other.unit_numer,
                unit_denom=self.unit_denom or other.unit_denom,
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

        return NumberValue(new_amount, unit_numer=self.unit_numer, unit_denom=self.unit_denom)


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
            unit_numer=numer_units,
            unit_denom=denom_units,
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

    def render(self, compress=False):
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
    def from_maybe_starargs(cls, args, use_comma=True):
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
                return cls(args[0], use_comma=use_comma)

        return cls(args, use_comma=use_comma)

    def __hash__(self):
        return hash((self.value, self.use_comma))

    def delimiter(self, compress=False):
        if self.use_comma:
            if compress:
                return ','
            else:
                return ', '
        else:
            return ' '

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return self.render()

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, key):
        return self.value[key]

    def render(self, compress=False):
        delim = self.delimiter(compress)

        return delim.join(
            item.render(compress=compress)
            for item in self.value
        )


class Color(Value):
    sass_type_name = u'color'

    HEX2RGBA = {
        9: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), int(c[7:9], 16)),
        7: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 1.0),
        5: lambda c: (int(c[1] * 2, 16), int(c[2] * 2, 16), int(c[3] * 2, 16), int(c[4] * 2, 16)),
        4: lambda c: (int(c[1] * 2, 16), int(c[2] * 2, 16), int(c[3] * 2, 16), 1.0),
    }

    original_literal = None

    def __init__(self, tokens):
        self.tokens = tokens
        self.value = (0, 0, 0, 1)
        if tokens is None:
            self.value = (0, 0, 0, 1)
        elif isinstance(tokens, ParserValue):
            hex = tokens.value
            self.original_literal = hex
            self.value = self.HEX2RGBA[len(hex)](hex)
        elif isinstance(tokens, ColorValue):
            self.value = tokens.value
        elif isinstance(tokens, (list, tuple)):
            c = tokens[:4]
            r = 255.0, 255.0, 255.0, 1.0
            c = [0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4)]
            self.value = tuple(c)
        else:
            raise TypeError("Can't make Color from %r" % (tokens,))

    ### Alternate constructors

    @classmethod
    def from_rgb(cls, red, green, blue, alpha=1.0):
        self = cls.__new__(cls)  # TODO
        self.tokens = None
        # TODO really should store these things internally as 0-1, but can't
        # until stuff stops examining .value directly
        self.value = (red * 255.0, green * 255.0, blue * 255.0, alpha)
        return self

    @classmethod
    def from_hex(cls, hex_string):
        if not hex_string.startswith('#'):
            raise ValueError("Expected #abcdef, got %r" % (hex_string,))

        hex_string = hex_string[1:]

        # Always include the alpha channel
        if len(hex_string) == 3:
            hex_string += 'f'
        elif len(hex_string) == 6:
            hex_string += 'ff'

        # Now there should be only two possibilities.  Normalize to a list of
        # two hex digits
        if len(hex_string) == 4:
            chunks = [ch * 2 for ch in hex_string]
        elif len(hex_string) == 8:
            chunks = [
                hex_string[0:2], hex_string[2:4], hex_string[4:6], hex_string[6:8]
            ]

        rgba = [int(ch, 16) / 255. for ch in chunks]
        return cls.from_rgb(*rgba)

    @classmethod
    def from_name(cls, name):
        """Build a Color from a CSS color name."""
        self = cls.__new__(cls)  # TODO
        self.original_literal = name

        r, g, b, a = COLOR_NAMES[name]

        self.value = r, g, b, a
        return self

    ### Accessors

    @property
    def rgb(self):
        return tuple(self.value[:3])

    @property
    def alpha(self):
        return self.value[3]

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, repr(self.value))

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if not isinstance(other, ColorValue):
            return BooleanValue(False)

        # Round to the nearest 5 digits for comparisons; corresponds roughly to
        # 16 bits per channel, the most that generally matters.  Otherwise
        # float errors make equality fail for HSL colors.
        left = tuple(round(n, 5) for n in self.value)
        right = tuple(round(n, 5) for n in other.value)
        return BooleanValue(left == right)

    def __add__(self, other):
        if isinstance(other, (Color, Number)):
            return self._operate(other, operator.add)
        else:
            return super(Color, self).__add__(other)

    def __sub__(self, other):
        if isinstance(other, (Color, Number)):
            return self._operate(other, operator.sub)
        else:
            return super(Color, self).__sub__(other)

    def __mul__(self, other):
        if isinstance(other, (Color, Number)):
            return self._operate(other, operator.mul)
        else:
            return super(Color, self).__mul__(other)

    def __div__(self, other):
        if isinstance(other, (Color, Number)):
            return self._operate(other, operator.div)
        else:
            return super(Color, self).__div__(other)

    def _operate(self, other, op):
        if isinstance(other, Number):
            if not other.is_unitless:
                raise ValueError("Expected unitless Number, got %r" % (other,))

            other_rgb = (other.value,) * 3
        elif isinstance(other, Color):
            if self.alpha != other.alpha:
                raise ValueError("Alpha channels must match between %r and %r"
                    % (self, other))

            other_rgb = other.rgb
        else:
            raise TypeError("Expected Color or Number, got %r" % (other,))

        new_rgb = [
            min(255., max(0., op(left, right)))
            # for from_rgb
                / 255.
            for (left, right) in zip(self.rgb, other_rgb)
        ]

        return Color.from_rgb(*new_rgb, alpha=self.alpha)

    def render(self, compress=False):
        """Return a rendered representation of the color.  If `compress` is
        true, the shortest possible representation is used; otherwise, named
        colors are rendered as names and all others are rendered as hex (or
        with the rgba function).
        """

        if not compress and self.original_literal:
            return self.original_literal

        candidates = []

        # TODO this assumes CSS resolution is 8-bit per channel, but so does
        # Ruby.
        r, g, b, a = self.value
        r, g, b = int(round(r)), int(round(g)), int(round(b))

        # Build a candidate list in order of preference.  If `compress` is
        # True, the shortest candidate is used; otherwise, the first candidate
        # is used.

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

        if compress:
            return min(candidates, key=len)
        else:
            return candidates[0]


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

    def __hash__(self):
        return hash(self.value)

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

    def __mul__(self, other):
        # DEVIATION: Ruby Sass doesn't do this, because Ruby doesn't.  But
        # Python does, and in Ruby Sass it's just fatal anyway.
        if not isinstance(other, Number):
            return super(String, self).__mul__(other)

        if not other.is_unitless:
            raise TypeError("Can only multiply strings by unitless numbers")

        return String(self.value * other.value, quotes=self.quotes)

    def render(self, compress=False):
        return self.__str__()


# Backwards-compatibility.
ColorValue = Color
ListValue = List
NumberValue = Number
QuotedStringValue = String
StringValue = String
