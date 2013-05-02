from __future__ import absolute_import

import colorsys
import operator

from scss.cssdefs import _conv_factor, _conv_type, _undefined_re, _units_weights
from scss.util import dequote, escape, to_float, to_str


################################################################################
# pyScss data types:

class ParserValue(object):
    def __init__(self, value):
        self.value = value


class Value(object):
    @staticmethod
    def _merge_type(a, b):
        if a.__class__ == b.__class__:
            return a.__class__
        if isinstance(a, QuotedStringValue) or isinstance(b, QuotedStringValue):
            return QuotedStringValue
        return StringValue

    @staticmethod
    def _wrap(fn):
        """
        Wrapper function to allow calling any function
        using Value objects as parameters.
        """
        def _func(*args):
            merged = None
            _args = []
            for arg in args:
                if merged.__class__ != arg.__class__:
                    if merged is None:
                        merged = arg.__class__(None)
                    else:
                        merged = Value._merge_type(merged, arg)(None)
                merged.merge(arg)
                if isinstance(arg, Value):
                    arg = arg.value
                _args.append(arg)
            merged.value = fn(*_args)
            return merged
        return _func

    @classmethod
    def _do_bitops(cls, first, second, op):
        first = StringValue(first)
        second = StringValue(second)
        k = op(first.value, second.value)
        return first if first.value == k else second

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, repr(self.value))

    def __lt__(self, other):
        return self._do_cmps(self, other, operator.__lt__)

    def __le__(self, other):
        return self._do_cmps(self, other, operator.__le__)

    def __eq__(self, other):
        return self._do_cmps(self, other, operator.__eq__)

    def __ne__(self, other):
        return self._do_cmps(self, other, operator.__ne__)

    def __gt__(self, other):
        return self._do_cmps(self, other, operator.__gt__)

    def __ge__(self, other):
        return self._do_cmps(self, other, operator.__ge__)

    def __cmp__(self, other):
        return self._do_cmps(self, other, operator.__cmp__)

    def __rcmp__(self, other):
        return self._do_cmps(other, self, operator.__cmp__)

    def __and__(self, other):
        return self._do_bitops(self, other, operator.__and__)

    def __or__(self, other):
        return self._do_bitops(self, other, operator.__or__)

    def __xor__(self, other):
        return self._do_bitops(self, other, operator.__xor__)

    def __rand__(self, other):
        return self._do_bitops(other, self, operator.__rand__)

    def __ror__(self, other):
        return self._do_bitops(other, self, operator.__ror__)

    def __rxor__(self, other):
        return self._do_bitops(other, self, operator.__rxor__)

    def __nonzero__(self):
        return bool(self.value)

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

    def convert_to(self, type):
        return self.value.convert_to(type)

    def merge(self, obj):
        if isinstance(obj, Value):
            self.value = obj.value
        else:
            self.value = obj
        return self


class BooleanValue(Value):
    def __init__(self, tokens):
        self.tokens = tokens
        if tokens is None:
            self.value = False
        elif isinstance(tokens, ParserValue):
            self.value = (tokens.value.lower() == 'true')
        elif isinstance(tokens, BooleanValue):
            self.value = tokens.value
        elif isinstance(tokens, NumberValue):
            self.value = bool(tokens.value)
        elif isinstance(tokens, (float, int)):
            self.value = bool(tokens)
        else:
            self.value = to_str(tokens).lower() in ('true', '1', 'on', 'yes', 't', 'y') or bool(tokens)

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return 'true' if self.value else 'false'

    @classmethod
    def _do_cmps(cls, first, second, op):
        first = first.value if isinstance(first, Value) else first
        second = second.value if isinstance(second, Value) else second
        if first in ('true', '1', 'on', 'yes', 't', 'y'):
            first = True
        elif first in ('false', '0', 'off', 'no', 'f', 'n', 'undefined'):
            first = False
        if second in ('true', '1', 'on', 'yes', 't', 'y'):
            second = True
        elif second in ('false', '0', 'off', 'no', 'f', 'n', 'undefined'):
            second = False
        return op(first, second)

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
        ret = BooleanValue(None).merge(first).merge(second)
        ret.value = val
        return ret

    def merge(self, obj):
        obj = BooleanValue(obj)
        self.value = obj.value
        return self


class NumberValue(Value):
    def __init__(self, tokens, type=None):
        self.tokens = tokens
        self.units = {}
        if tokens is None:
            self.value = 0.0
        elif isinstance(tokens, ParserValue):
            self.value = float(tokens.value)
        elif isinstance(tokens, NumberValue):
            self.value = tokens.value
            self.units = tokens.units.copy()
            if tokens.units:
                type = None
        elif isinstance(tokens, (StringValue,)):
            tokens = getattr(tokens, 'value', tokens)
            if _undefined_re.match(tokens):
                raise ValueError("Value is not a Number! (%s)" % tokens)
            try:
                if tokens and tokens[-1] == '%':
                    self.value = to_float(tokens[:-1]) / 100.0
                    self.units = {'%': _units_weights.get('%', 1), '_': '%'}
                else:
                    self.value = to_float(tokens)
            except ValueError:
                raise ValueError("Value is not a Number! (%s)" % tokens)
        elif isinstance(tokens, (int, float)):
            self.value = float(tokens)
        else:
            raise ValueError("Can't convert to CSS number: %r" % tokens)
        if type is not None:
            self.units = {type: _units_weights.get(type, 1), '_': type}

    def __hash__(self):
        return hash((self.value, frozenset(self.units.items())))

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, repr(self.value), repr(self.units))

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        unit = self.unit
        val = self.value / _conv_factor.get(unit, 1.0)
        val = to_str(val) + unit
        return val

    @classmethod
    def _do_cmps(cls, first, second, op):
        try:
            first = NumberValue(first)
            second = NumberValue(second)
        except ValueError:
            return op(getattr(first, 'value', first), getattr(second, 'value', second))
        first_type = _conv_type.get(first.unit)
        second_type = _conv_type.get(second.unit)
        if first_type == second_type or first_type is None or second_type is None:
            return op(first.value, second.value)
        else:
            return op(first_type, second_type)

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

        if isinstance(first, (int, float)):
            first = NumberValue(first)
        if isinstance(second, (int, float)):
            second = NumberValue(second)

        if op in (operator.__div__, operator.__sub__):
            if isinstance(first, QuotedStringValue):
                first = NumberValue(first)
            if isinstance(second, QuotedStringValue):
                second = NumberValue(second)
        elif op == operator.__mul__:
            if isinstance(first, NumberValue) and isinstance(second, QuotedStringValue):
                first.value = int(first.value)
                val = op(second.value, first.value)
                return second.__class__(val)
            if isinstance(first, QuotedStringValue) and isinstance(second, NumberValue):
                second.value = int(second.value)
                val = op(first.value, second.value)
                return first.__class__(val)

        if not isinstance(first, NumberValue) or not isinstance(second, NumberValue):
            return op(first.value if isinstance(first, NumberValue) else first, second.value if isinstance(second, NumberValue) else second)

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

        val = op(first.value, second.value)

        ret = NumberValue(None).merge(first)
        ret = ret.merge(second)
        ret.value = val
        return ret

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

    def convert_to(self, type):
        val = self.value
        if not self.unit:
            val *= _conv_factor.get(type, 1.0)
        ret = NumberValue(val)
        if type == 'deg' and ret.value > 360:
            ret.value = ret.value % 360.0
        ret.units = {type: _units_weights.get(type, 1), '_': type}
        return ret

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
    def __init__(self, tokens, separator=None):
        self.tokens = tokens
        if tokens is None:
            self.value = {}
        elif isinstance(tokens, ParserValue):
            self.value = self._reorder_list(tokens.value)
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

    def __hash__(self):
        return hash((frozenset(self.value.items())))

    @classmethod
    def _do_cmps(cls, first, second, op):
        try:
            first = ListValue(first)
            second = ListValue(second)
        except ValueError:
            return op(getattr(first, 'value', first), getattr(second, 'value', second))
        return op(first.value, second.value)

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

    def __tuple__(self):
        return tuple(sorted((k, v) for k, v in self.value.items() if k != '_'))

    def __iter__(self):
        return iter(self.values())

    def values(self):
        return zip(*self.items())[1]

    def keys(self):
        return zip(*self.items())[1]

    def items(self):
        return sorted((k, v) for k, v in self.value.items() if k != '_')

    def first(self):
        for v in self.values():
            if isinstance(v, basestring) and _undefined_re.match(v):
                continue
            if bool(v):
                return v
        return v


class ColorValue(Value):
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
            if _undefined_re.match(tokens):
                raise ValueError("Value is not a Color! (%s)" % tokens)
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

    def __hash__(self):
        return hash((tuple(self.value), frozenset(self.types.items())))

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, repr(self.value), repr(self.types))

    def __str__(self):
        type = self.type
        c = self.value
        if type == 'hsl' or type == 'hsla' and c[3] == 1:
            h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
            return 'hsl(%s, %s%%, %s%%)' % (to_str(h * 360.0), to_str(s * 100.0), to_str(l * 100.0))
        if type == 'hsla':
            h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
            return 'hsla(%s, %s%%, %s%%, %s)' % (to_str(h * 360.0), to_str(s * 100.0), to_str(l * 100.0), to_str(c[3]))
        r, g, b = to_str(c[0]), to_str(c[1]), to_str(c[2])
        _, _, r = r.partition('.')
        _, _, g = g.partition('.')
        _, _, b = b.partition('.')
        if c[3] == 1:
            if len(r) > 2 or len(g) > 2 or len(b) > 2:
                return 'rgb(%s%%, %s%%, %s%%)' % (to_str(c[0] * 100.0 / 255.0), to_str(c[1] * 100.0 / 255.0), to_str(c[2] * 100.0 / 255.0))
            return '#%02x%02x%02x' % (round(c[0]), round(c[1]), round(c[2]))
        if len(r) > 2 or len(g) > 2 or len(b) > 2:
            return 'rgba(%s%%, %s%%, %s%%, %s)' % (to_str(c[0] * 100.0 / 255.0), to_str(c[1] * 100.0 / 255.0), to_str(c[2] * 100.0 / 255.0), to_str(c[3]))
        return 'rgba(%d, %d, %d, %s)' % (round(c[0]), round(c[1]), round(c[2]), to_str(c[3]))

    @classmethod
    def _do_cmps(cls, first, second, op):
        try:
            first = ColorValue(first)
            second = ColorValue(second)
        except ValueError:
            return op(getattr(first, 'value', first), getattr(second, 'value', second))
        return op(first.value, second.value)

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

    def convert_to(self, type):
        val = self.value
        ret = ColorValue(val)
        ret.types[type] = 1
        return ret

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


class QuotedStringValue(Value):
    def __init__(self, tokens):
        self.tokens = tokens
        if tokens is None:
            self.value = ''
        elif isinstance(tokens, ParserValue):
            self.value = dequote(tokens.value)
        elif isinstance(tokens, QuotedStringValue):
            self.value = tokens.value
        else:
            self.value = to_str(tokens)

    def __hash__(self):
        return hash((True, self.value))

    def convert_to(self, type):
        return QuotedStringValue(self.value + type)

    def __str__(self):
        return str(self.__unicode__())

    def __unicode__(self):
        return '"%s"' % escape(self.value)

    @classmethod
    def _do_cmps(cls, first, second, op):
        first = QuotedStringValue(first)
        second = QuotedStringValue(second)
        return op(first.value, second.value)

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

        first = QuotedStringValue(first)
        first_value = first.value
        if op == operator.__mul__:
            second = NumberValue(second)
            second_value = int(second.value)
        else:
            second = QuotedStringValue(second)
            second_value = second.value
        val = op(first_value, second_value)
        ret = QuotedStringValue(None).merge(first).merge(second)
        ret.value = val
        return ret

    def merge(self, obj):
        obj = QuotedStringValue(obj)
        self.value = obj.value
        return self


class StringValue(QuotedStringValue):
    def __hash__(self):
        return hash((False, self.value))

    def __str__(self):
        return str(self.__unicode__())

    def __unicode__(self):
        return self.value

    def __add__(self, other):
        if isinstance(other, ListValue):
            return self._do_op(self, other, operator.__add__)
        string_class = StringValue
        if self.__class__ == QuotedStringValue or other.__class__ == QuotedStringValue:
            string_class = QuotedStringValue
        other = string_class(other)
        if not isinstance(other, QuotedStringValue):
            return string_class(self.value + '+' + other.value)
        return string_class(self.value + other.value)

    def __radd__(self, other):
        if isinstance(other, ListValue):
            return self._do_op(other, self, operator.__add__)
        string_class = StringValue
        if self.__class__ == QuotedStringValue or other.__class__ == QuotedStringValue:
            string_class = QuotedStringValue
        other = string_class(other)
        if not isinstance(other, (QuotedStringValue, basestring)):
            return string_class(other.value + '+' + self.value)
        return string_class(other.value + self.value)
