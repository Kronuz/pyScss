from __future__ import absolute_import

from scss.cssdefs import __elements_of_type
from scss.types import BooleanValue, ListValue, NumberValue, StringValue

def _enumerate(prefix, frm, through, separator='-'):
    prefix = StringValue(prefix).value
    separator = StringValue(separator).value
    try:
        frm = int(getattr(frm, 'value', frm))
    except ValueError:
        frm = 1
    try:
        through = int(getattr(through, 'value', through))
    except ValueError:
        through = frm
    if frm > through:
        frm, through = through, frm
        rev = reversed
    else:
        rev = lambda x: x
    if prefix:
        ret = [prefix + separator + str(i) for i in rev(range(frm, through + 1))]
    else:
        ret = [NumberValue(i) for i in rev(range(frm, through + 1))]
    ret = dict(enumerate(ret))
    ret['_'] = ','
    return ret


def _range(frm, through=None):
    if through is None:
        through = frm
        frm = 1
    return _enumerate(None, frm, through)

def _headers(frm=None, to=None):
    if frm and to is None:
        if isinstance(frm, StringValue) and frm.value.lower() == 'all':
            frm = 1
            to = 6
        else:
            frm = 1
            try:
                to = int(getattr(frm, 'value', frm))
            except ValueError:
                to = 6
    else:
        try:
            frm = 1 if frm is None else int(getattr(frm, 'value', frm))
        except ValueError:
            frm = 1
        try:
            to = 6 if to is None else int(getattr(to, 'value', to))
        except ValueError:
            to = 6
    ret = ['h' + str(i) for i in range(frm, to + 1)]
    ret = dict(enumerate(ret))
    ret['_'] = ','
    return ret

def _convert_to(value, type):
    return value.convert_to(type)



################################################################################
# Specific to pyScss parser functions:


def _elements_of_type(display):
    d = StringValue(display)
    ret = __elements_of_type.get(d.value, None)
    if ret is None:
        raise Exception("Elements of type '%s' not found!" % d.value)
    ret['_'] = ','
    return ListValue(ret)


def _nest(*arguments):
    if isinstance(arguments[0], ListValue):
        lst = arguments[0].values()
    else:
        lst = StringValue(arguments[0]).value.split(',')
    ret = [unicode(s).strip() for s in lst if unicode(s).strip()]
    for arg in arguments[1:]:
        if isinstance(arg, ListValue):
            lst = arg.values()
        else:
            lst = StringValue(arg).value.split(',')
        new_ret = []
        for s in lst:
            s = unicode(s).strip()
            if s:
                for r in ret:
                    if '&' in s:
                        new_ret.append(s.replace('&', r))
                    else:
                        if r[-1] in ('.', ':', '#'):
                            new_ret.append(r + s)
                        else:
                            new_ret.append(r + ' ' + s)
        ret = new_ret
    ret = sorted(set(ret))
    ret = dict(enumerate(ret))
    ret['_'] = ','
    return ret


def _append_selector(selector, to_append):
    if isinstance(selector, ListValue):
        lst = selector.values()
    else:
        lst = StringValue(selector).value.split(',')
    to_append = StringValue(to_append).value.strip()
    ret = sorted(set(s.strip() + to_append for s in lst if s.strip()))
    ret = dict(enumerate(ret))
    ret['_'] = ','
    return ret




def _inv(sign, value):
    if isinstance(value, NumberValue):
        return value * -1
    elif isinstance(value, BooleanValue):
        return not value
    val = StringValue(value)
    val.value = sign + val.value
    return val


