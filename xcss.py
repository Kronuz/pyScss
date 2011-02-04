#!/usr/bin/python
#-*- coding: utf-8 -*-
"""
xCSS Framework for Python

@author    German M. Bravo (Kronuz)
           Based on some code from the original xCSS project by Anton Pawlik
@version   0.2
@see       http://xcss.antpaw.org/docs/
           http://sass-lang.com/
           http://oocss.org/spec/css-object-model.html
@copyright (c) 2011 German M. Bravo (Kronuz)
           (c) 2010 Anton Pawlik
@license   MIT License
           http://www.opensource.org/licenses/mit-license.php

xCSS for Python is a superset of CSS that is more powerful, elegant and easier
to maintain than plain-vanilla CSS. The framework works as a CSS source code
preprocesor which allows you to use variables, nested rules, mixins, and extend
classes, all with a CSS-compatible syntax which the preprocessor then compiles
to standard CSS.

xCSS, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten and many bugs have been fixed.

"""

import re
import sys
from math import *

FILEID = 0
POSITION = 1
CODESTR = 2
DEPS = 3
CONTEXT = 4
OPTIONS = 5
SELECTORS = 6
PROPERTIES = 7

def safe_eval(str, context=None):
    # Safe eval:

    #make a list of safe functions
    safe_locals = ['math','acos', 'asin', 'atan', 'atan2', 'ceil', 'cos',
                   'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod',
                   'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi',
                   'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']
    safe_builtins = ['abs', 'max', 'min', 'int', 'pow']

    safe_dict = {}

    # use the list to filter the local namespace
    safe_dict.update(dict([ (k, globals().get(k, None)) for k in safe_locals ]))

    # add any needed builtins back in
    safe_dict.update(dict([ (k, getattr(__builtins__, k, None)) for k in safe_builtins ]))

    # add user context
    safe_dict.update(context or {})

    return eval(str, {"__builtins__": None}, safe_dict)


# this does not increase asymptotical complexity
# but can still waste more time than it saves. TODO: profile
# from http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python
def long_substr(strings):
    substr = ""
    if not strings:
        return substr
    reference = min(strings, key=len) #strings[0]
    length = len(reference)
    #find a suitable slice i:j
    for i in xrange(length):
        #only consider strings long at least len(substr) + 1
        for j in xrange(i + len(substr) + 1, length + 1):
            candidate = reference[i:j]  # is the slice recalculated every time?
            if all(candidate in text for text in strings):
                substr = candidate
    return substr


class xCSS(object):
    # configuration:
    construct = 'self'
    short_colors = True
    reverse_colors = True

    #optinos
    verbosity = 0

    # units and conversions
    _units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
              'grad', 'ms', 's', 'hz', 'khz', '%']
    _conv = {
        'size': {
            'em': 13.0,
            'px': 1.0
        },
        'length': {
            'mm':  1.0,
            'cm':  10.0,
            'in':  25.4,
            'pt':  25.4 / 72,
            'pc':  25.4 / 6
        },
        'time': {
            'ms':  1.0,
            's':   1000.0
        },
        'freq': {
            'hz':  1.0,
            'khz': 1000.0
        }
    }
    _conv_mapping = {}
    for t, m in _conv.items():
        for k in m:
            _conv_mapping[k] = t
    del t, m, k

    # color literals
    _colors = {
        'aliceblue': '#f0f8ff',
        'antiquewhite': '#faebd7',
        'aqua': '#00ffff',
        'aquamarine': '#7fffd4',
        'azure': '#f0ffff',
        'beige': '#f5f5dc',
        'bisque': '#ffe4c4',
        'black': '#000000',
        'blanchedalmond': '#ffebcd',
        'blue': '#0000ff',
        'blueviolet': '#8a2be2',
        'brown': '#a52a2a',
        'burlywood': '#deb887',
        'cadetblue': '#5f9ea0',
        'chartreuse': '#7fff00',
        'chocolate': '#d2691e',
        'coral': '#ff7f50',
        'cornflowerblue': '#6495ed',
        'cornsilk': '#fff8dc',
        'crimson': '#dc143c',
        'cyan': '#00ffff',
        'darkblue': '#00008b',
        'darkcyan': '#008b8b',
        'darkgoldenrod': '#b8860b',
        'darkgray': '#a9a9a9',
        'darkgreen': '#006400',
        'darkkhaki': '#bdb76b',
        'darkmagenta': '#8b008b',
        'darkolivegreen': '#556b2f',
        'darkorange': '#ff8c00',
        'darkorchid': '#9932cc',
        'darkred': '#8b0000',
        'darksalmon': '#e9967a',
        'darkseagreen': '#8fbc8f',
        'darkslateblue': '#483d8b',
        'darkslategray': '#2f4f4f',
        'darkturquoise': '#00ced1',
        'darkviolet': '#9400d3',
        'deeppink': '#ff1493',
        'deepskyblue': '#00bfff',
        'dimgray': '#696969',
        'dodgerblue': '#1e90ff',
        'firebrick': '#b22222',
        'floralwhite': '#fffaf0',
        'forestgreen': '#228b22',
        'fuchsia': '#ff00ff',
        'gainsboro': '#dcdcdc',
        'ghostwhite': '#f8f8ff',
        'gold': '#ffd700',
        'goldenrod': '#daa520',
        'gray': '#808080',
        'green': '#008000',
        'greenyellow': '#adff2f',
        'honeydew': '#f0fff0',
        'hotpink': '#ff69b4',
        'indianred': '#cd5c5c',
        'indigo': '#4b0082',
        'ivory': '#fffff0',
        'khaki': '#f0e68c',
        'lavender': '#e6e6fa',
        'lavenderblush': '#fff0f5',
        'lawngreen': '#7cfc00',
        'lemonchiffon': '#fffacd',
        'lightblue': '#add8e6',
        'lightcoral': '#f08080',
        'lightcyan': '#e0ffff',
        'lightgoldenrodyellow': '#fafad2',
        'lightgreen': '#90ee90',
        'lightgrey': '#d3d3d3',
        'lightpink': '#ffb6c1',
        'lightsalmon': '#ffa07a',
        'lightseagreen': '#20b2aa',
        'lightskyblue': '#87cefa',
        'lightslategray': '#778899',
        'lightsteelblue': '#b0c4de',
        'lightyellow': '#ffffe0',
        'lime': '#00ff00',
        'limegreen': '#32cd32',
        'linen': '#faf0e6',
        'magenta': '#ff00ff',
        'maroon': '#800000',
        'mediumaquamarine': '#66cdaa',
        'mediumblue': '#0000cd',
        'mediumorchid': '#ba55d3',
        'mediumpurple': '#9370db',
        'mediumseagreen': '#3cb371',
        'mediumslateblue': '#7b68ee',
        'mediumspringgreen': '#00fa9a',
        'mediumturquoise': '#48d1cc',
        'mediumvioletred': '#c71585',
        'midnightblue': '#191970',
        'mintcream': '#f5fffa',
        'mistyrose': '#ffe4e1',
        'moccasin': '#ffe4b5',
        'navajowhite': '#ffdead',
        'navy': '#000080',
        'oldlace': '#fdf5e6',
        'olive': '#808000',
        'olivedrab': '#6b8e23',
        'orange': '#ffa500',
        'orangered': '#ff4500',
        'orchid': '#da70d6',
        'palegoldenrod': '#eee8aa',
        'palegreen': '#98fb98',
        'paleturquoise': '#afeeee',
        'palevioletred': '#db7093',
        'papayawhip': '#ffefd5',
        'peachpuff': '#ffdab9',
        'peru': '#cd853f',
        'pink': '#ffc0cb',
        'plum': '#dda0dd',
        'powderblue': '#b0e0e6',
        'purple': '#800080',
        'red': '#ff0000',
        'rosybrown': '#bc8f8f',
        'royalblue': '#4169e1',
        'saddlebrown': '#8b4513',
        'salmon': '#fa8072',
        'sandybrown': '#f4a460',
        'seagreen': '#2e8b57',
        'seashell': '#fff5ee',
        'sienna': '#a0522d',
        'silver': '#c0c0c0',
        'skyblue': '#87ceeb',
        'slateblue': '#6a5acd',
        'slategray': '#708090',
        'snow': '#fffafa',
        'springgreen': '#00ff7f',
        'steelblue': '#4682b4',
        'tan': '#d2b48c',
        'teal': '#008080',
        'thistle': '#d8bfd8',
        'tomato': '#ff6347',
        'turquoise': '#40e0d0',
        'violet': '#ee82ee',
        'wheat': '#f5deb3',
        'white': '#ffffff',
        'whitesmoke': '#f5f5f5',
        'yellow': '#ffff00',
        'yellowgreen': '#9acd32'
    }

    _default_xcss_vars = {
        # unsafe chars will be hidden as vars
        '$__doubleslash': '//',
        '$__bigcopen': '/*',
        '$__bigcclose': '*/',
        '$__doubledot': ':',
        '$__semicolon': ';',
        '$__curlybracketopen': '{',
        '$__curlybracketclosed': '}',

        # shortcuts (it's "a hidden feature" for now)
        'bg:': 'background:',
        'bgc:': 'background-color:',
    }

    _default_xcss_opts = {
        'verbosity': 1,
    }

    _short_color_re = re.compile(r'(?<!\w)#([a-f0-9])\1([a-f0-9])\2([a-f0-9])\3\b', re.IGNORECASE)
    _long_color_re = re.compile(r'(?<!\w)#([a-f0-9]){2}([a-f0-9]){2}([a-f0-9]){2}\b', re.IGNORECASE)
    _reverse_colors = dict((v, k) for k, v in _colors.items())
    for long_k, v in _colors.items():
        # Calculate the different possible representations of a color:
        short_k = _short_color_re.sub(r'#\1\2\3', v).lower()
        rgb_k = _long_color_re.sub(lambda m: 'rgb(%d, %d, %d)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
        rgba_k = _long_color_re.sub(lambda m: 'rgba(%d, %d, %d, 255)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
        # get the shortest of all to use it:
        k = min([short_k, long_k, rgb_k, rgba_k], key=len)
        _reverse_colors[short_k] = k
        _reverse_colors[rgb_k] = k
        _reverse_colors[rgba_k] = k
    _reverse_colors_re = re.compile(r'(?<!\w)(' + '|'.join(map(re.escape, _reverse_colors.keys()))+r')\b', re.IGNORECASE)
    _colors_re = re.compile(r'\b(' + '|'.join(map(re.escape, _colors.keys()))+r')\b', re.IGNORECASE)

    _color_re = re.compile(r'''
        (# RGB in the hex form (#RRGGBB):
            (?<!\w)
            \#
                (?P<short_R>[a-f0-9])
                (?P<short_G>[a-f0-9])
                (?P<short_B>[a-f0-9])
            \b
        | # RGB in the hex form (#RRGGBB):
            (?<!\w)
            \#
                (?P<long_R>[a-f0-9]{2})
                (?P<long_G>[a-f0-9]{2})
                (?P<long_B>[a-f0-9]{2})
            \b
        | # RGB using the rgb():
            \b
            rgb\(
                \s*(?P<rgb_R>\d+)(?P<rgbX>%?)\s*,
                \s*(?P<rgb_G>\d+)(?P=rgbX)\s*,
                \s*(?P<rgb_B>\d+)(?P=rgbX)\s*
            \)
        | # RGBA using the rgba():
            \b
            rgba\(
                \s*(?P<rgba_R>\d+)(?P<rgbaX>%?)\s*,
                \s*(?P<rgba_G>\d+)(?P=rgbaX)\s*,
                \s*(?P<rgba_B>\d+)(?P=rgbaX)\s*,
                \s*(?P<rgba_A>\d+)(?P=rgbaX)\s*
            \)
        )
    ''', re.IGNORECASE | re.VERBOSE)
    _expr_re = re.compile(r'''
        (?P<expr>
            \#\{.*?\}
        |
            (?:
                [[(][\][()\s]*
            )?
            [#%.\w]+                # Accept a variable or constant or number (preceded by spaces or parenthesis)
            (?:
                (?:
                    \(              # Accept either the start of a function call... ("function_call(")
                |
                    [\][()\s]*      # ...or an operation ("+-*/")
                    (?:\s-\s|[+*/]) # (dash needs a surrounding space always)
                )
                [\][()\s]*          
                [#%.\w]+            # Accept a variable or constant or number (preceded by spaces or parenthesis)
            )*                      # ...take n arguments,
            (?:
                [\][()\s]*[\])]     # but then finish accepting any missing parenthesis and spaces
            )?
            (?!.*:)
            (?=.*;)
        )
        (?P<unit>
            \s*[;}]
        |
            \s*$
        |
            [^;}\s]+
        |
            \s
        )
    ''', re.VERBOSE)
    #_expr_re = re.compile(r'(\[.*?\])([\s;}]|$|.+?\S)') # <- This is the old method, required parenthesis around the expression
    _ml_comment_re = re.compile(r'\/\*(.*?)\*\/', re.DOTALL)
    _sl_comment_re = re.compile(r'(?<!\w{2}:)\/\/.*')
    _unit_re = re.compile(r'(?<=(\s|\d))' + '|'.join(map(re.escape, _units)) + r'(?!\w)', re.IGNORECASE)
    _full_unit_re = re.compile(r'([\d.]+)(' + '|'.join(map(re.escape, _units)) + r')?(?!\w)', re.IGNORECASE)
    _zero_units_re = re.compile(r'\b0(' + '|'.join(map(re.escape, _units)) + r')(?!\w)', re.IGNORECASE)

    _includes_re = re.compile(r'@include\s+(.*?)\s*(\((.+?,)*(.+?)\))?\s*([;}]|$)', re.DOTALL)
    _remove_decls_re = re.compile(r'(@option\b.*?([;}]|$))', re.DOTALL | re.IGNORECASE)
    _fix_extends_re = re.compile(r'\s+extends\s+', re.IGNORECASE)
    _collapse_properties_space_re = re.compile(r'([:#])\s*{')
    _expand_rules_space_re = re.compile(r'\s*{')

    _reverse_default_xcss_vars = dict((v, k) for k, v in _default_xcss_vars.items())
    _reverse_default_xcss_vars_re = re.compile(r'(content.*:.*(\'|").*)(' + '|'.join(map(re.escape, _reverse_default_xcss_vars.keys())) + ')(.*\2)')

    def __init__(self):
        pass

    def locate_blocks(self, str, open='{', close='}', joiner=','):
        """
        Returns all code blocks between `open` and `close` and a proper key
        that can be multilined as long as it's joined by `joiner`.
        Returns the lose code that's not part of the code as a third item.
        """
        depth = 0
        losing = 0
        skip = False
        i = init = lose = 0
        start = end = None
        str_len = len(str)
        open_len = len(open)
        close_len = len(close)
        joiner_len = len(joiner)
        while i < str_len:
            if i > 0 and str[i-1] == '#' and str[i:i+open_len] == open:
                skip = True
            if not skip and str[i:i+open_len] == open:
                depth += 1
                if depth == 1:
                    start = i
                    if lose < init:
                        losestr = str[lose:init]
                        yield None, None, losestr
                        lose = init
                        losing = 0
                i += open_len
            elif not skip and str[i:i+close_len] == close:
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        end = i
                        selectors = str[init:start].strip()
                        codestr = str[start+open_len:end].strip()
                        if selectors:
                            yield selectors, codestr, None
                        init = lose = end + close_len
                        losing = 0
                else:
                    init = lose = i + close_len
                i += close_len
            else:
                if skip and str[i:i+close_len] == close:
                    skip = False
                if depth == 0:
                    if str[i] == '\n':
                        if losing:
                            losing = 2 # If last thing we saw was a real character, we're now walking on ice...
                    elif str[i:i+joiner_len] == joiner:
                        losing = 0 # We're safe not (for the moment)
                        i += joiner_len - 1
                    elif str[i] not in ('\t', ' '):
                        if losing == 2:
                            init = i # We were walking on ice, now it's broken!
                            losing = 0
                        else:
                            losing = 1 # We saw a real character!
                    i += 1
                else:
                    i += 1
        losestr = str[lose:]
        yield None, None, losestr

    def compile(self, input_xcss=None):
        # Initialize
        self.rules = []
        self._rules = {}
        self.parts = {}
        self.css_files = []
        self.xcss_vars = self._default_xcss_vars.copy()
        self.xcss_opts = self._default_xcss_opts.copy()

        self._contexts = {}
        self._replaces = {}

        if input_xcss is not None:
            self.xcss_files = {}
            self.xcss_files['string'] = input_xcss + '\n'
        self.xcss_files = self.xcss_files or {}

        # Compile
        for fileid, str in self.xcss_files.items():
            self.parse_xcss_string(fileid, str)

        if self.parts:
            # this will manage xCSS rule: child objects inside of a node
            self.parse_children()

            # this will manage xCSS rule: ' extends '
            self.parse_extends()

            # this will manage properties in rules
            self.parse_properties()

            # this will manage the order of the rules
            self.manage_order()

        final_cont = ''
        for fileid in self.css_files:
            if fileid != 'string':
                final_cont += '/* Generated frm: ' + fileid + ' */\n'
            fcont = self.create_css(fileid)
            fcont = self.do_math(fcont)
            fcont = self.post_process(fcont)
            final_cont += fcont

        return final_cont

    def post_process(self, cont):
        # short colors:
        if self.short_colors:
            cont = self._short_color_re.sub(r'#\1\2\3', cont)

        # color names:
        if self.reverse_colors:
            cont = self._reverse_colors_re.sub(lambda m: self._reverse_colors[m.group(0).lower()], cont)

        # zero units out (i.e. 0px or 0em -> 0):
        cont = self._zero_units_re.sub('0', cont)
        return cont

    def use_vars(self, cont, context=None, options=None):
        xcss_vars = self.xcss_vars.copy()
        xcss_vars.update(context or {})
        vars = xcss_vars.keys()
        try:
            remove_vars_re, interpolate_re = self._contexts[tuple(vars)]
        except KeyError:
            vars1 = []
            vars2 = []
            for var in vars:
                if var[0] == '$':
                    vars1.append(re.escape(var))
                else:
                    vars2.append(re.escape(var))
            remove_vars_re = re.compile(r'(?<![-\w])(((' + '|'.join(vars1) + r')\s*[:=]|(' + '|'.join(vars2) + r')\s*=).*?([;}]|$))')
            interpolate_re = re.compile(r'(?<![-\w])(' + '|'.join(map(re.escape, vars)) + r')(?![-\w])')
            self._contexts[tuple(vars)] = remove_vars_re, interpolate_re

        # remove variables declarations from the rules
        cont = self._remove_decls_re.sub('', cont)
        cont = remove_vars_re.sub('', cont)

        cnt = 0
        old_cont = None
        while cont != old_cont and cnt < 5:
            cnt += 1
            old_cont = cont

            # interpolate variables:
            cont = interpolate_re.sub(lambda m: xcss_vars[m.group(0)], cont)

        return cont

    def do_math(self, content):
        def calculate(result):
            _base_str = result.group(0)
            _expr_str = result.group('expr')
            _unit_str = result.group('unit')
            if _expr_str.startswith('url(') or _expr_str.startswith('expression('):
                return _base_str
            try:
                better_expr_str = self._replaces[_base_str]
            except KeyError:
                if _expr_str[:2] == '#{' and _expr_str[-1] == '}':
                    _expr_str = _expr_str[2:-1].strip('[]')

                better_expr_str = self._colors_re.sub(lambda m: self._colors.get(m.group(0), m.group(0)), _expr_str).replace('[', '(').replace(']', ')')

                rgba = None
                for color in self._color_re.finditer(better_expr_str):
                    c = color.groupdict()
                    if c.get('short_R'):
                        r = int(c.get('short_R')*2, 16)
                        g = int(c.get('short_G')*2, 16)
                        b = int(c.get('short_B')*2, 16)
                        a = 0
                    elif c.get('long_R'):
                        r = int(c.get('long_R'), 16)
                        g = int(c.get('long_G'), 16)
                        b = int(c.get('long_B'), 16)
                        a = 0
                    elif c.get('rgb_R') is not None:
                        r = int(c.get('rgb_R'))
                        g = int(c.get('rgb_G'))
                        b = int(c.get('rgb_B'))
                        a = 0
                    else:
                        r = int(c.get('rgba_R'))
                        g = int(c.get('rgba_G'))
                        b = int(c.get('rgba_B'))
                        a = 255 - int(c.get('rgba_A'))
                    if c.get('rgb_X') or c.get('rgba_X'):
                        r = '%02x' % (r * 255 / 100)
                        g = '%02x' % (g * 255 / 100)
                        b = '%02x' % (b * 255 / 100)
                        a = '%02x' % (a * 255 / 100)
                    else:
                        r = '%02x' % r
                        g = '%02x' % g
                        b = '%02x' % b
                        a = '%02x' % a
                    _base_color_str = color.group(0)
                    if not rgba:
                        rgba = [
                            better_expr_str.replace(_base_color_str, '0x'+r),
                            better_expr_str.replace(_base_color_str, '0x'+g),
                            better_expr_str.replace(_base_color_str, '0x'+b),
                            better_expr_str.replace(_base_color_str, '0x'+a),
                        ]
                    else:
                        rgba = [
                            rgba[0].replace(_base_color_str, '0x'+r),
                            rgba[1].replace(_base_color_str, '0x'+g),
                            rgba[2].replace(_base_color_str, '0x'+b),
                            rgba[3].replace(_base_color_str, '0x'+a),
                        ]

                if rgba:
                    try:
                        r = int(safe_eval(rgba[0])); r = 0 if r < 0 else 255 if r > 255 else r
                        g = int(safe_eval(rgba[1])); g = 0 if g < 0 else 255 if g > 255 else g
                        b = int(safe_eval(rgba[2])); b = 0 if b < 0 else 255 if b > 255 else b
                        a = int(safe_eval(rgba[3])); a = 0 if a < 0 else 255 if a > 255 else a
                        
                        if a == 0:
                            _better_expr_str = '#%02x%02x%02x' % (r, g, b)
                        else:
                            _better_expr_str = 'rgba(%d, %d, %d, %d)' % (r, g, b, 255-a)
                    except NameError:
                        pass
                    except ValueError:
                        pass
                    except SyntaxError, e:
                        if self.xcss_opts.get('verbosity', self.verbosity) > 2:
                            better_expr_str += ' /* ERROR: %s! */' % e
                    except:
                        better_expr_str += ' /* ERROR: %s! */' % e
                    else:
                        better_expr_str = _better_expr_str
                else:
                    try:
                        global_factor = 1.0
                        if _unit_str == '%':
                            global_factor = 100.0
                        else:
                            for m in self._full_unit_re.finditer(better_expr_str):
                                unit = m.group(2)
                                if unit == '%':
                                    global_factor = 100.0
                                    break
                        
                        unit_types = set()
                        my_units = {}
                        def reunit(m):
                            value = m.group(1)
                            unit = m.group(2)
                            unit = unit and unit.lower()
                            my_units.setdefault(unit, 0)
                            my_units[unit] += 1
                            my_units.setdefault('count', 0)
                            if my_units['count'] < my_units[unit]:
                                my_units['count'] = my_units[unit]
                            if unit == '%' or not unit:
                                unit_type = None
                                factor = 1.0
                            else:
                                unit_type = self._conv_mapping.get(unit, 'unknown')
                                factor = self._conv.get(unit_type, {}).get(unit, 1.0)
                            unit_types.add(unit_type)
                            return str(float(value) * factor / global_factor)
                        better_expr_str = self._full_unit_re.sub(reunit, better_expr_str)

                        new_unit = ''
                        final_unit = _unit_str.lower()
                        if final_unit in (';', '\t', ' '):
                            for unit, count in my_units.items():
                                if unit != 'count' and count == my_units['count']:
                                    new_unit = unit
                                    break
                            final_unit = new_unit = new_unit or ''
                        if final_unit == '%' or not final_unit:
                            final_unit_type = None
                            final_factor = 1.0
                        elif final_unit:
                            final_unit_type = self._conv_mapping.get(final_unit, 'unknown')
                            final_factor = self._conv.get(final_unit_type, {}).get(final_unit, 1.0)
                        unit_types.add(final_unit_type)
                        unit_types.discard(None)
                        _better_expr_str = self._unit_re.sub('', better_expr_str)
                        num = str('%0.04f' % round(safe_eval(_better_expr_str) * global_factor / final_factor)).rstrip('0').rstrip('.')
                        _better_expr_str = '%s%s' % (num, new_unit)
                        if len(unit_types) > 1:
                            _better_expr_str += ' /* ERROR: units mismatch: %s! */' % ' vs. '.join(unit_types)
                    except NameError:
                        pass
                    except ValueError:
                        pass
                    except SyntaxError, e:
                        if self.xcss_opts.get('verbosity', self.verbosity) > 2:
                            better_expr_str += ' /* ERROR: %s! */' % e
                    except Exception, e:
                        better_expr_str += ' /* ERROR: %s! */' % e
                    else:
                        better_expr_str = _better_expr_str
                self._replaces[_base_str] = better_expr_str
            return better_expr_str + _unit_str
        #print >>sys.stderr, self._expr_re.findall(content)
        content = self._expr_re.sub(calculate, content)
        return content

    def parse_xcss_string(self, fileid, str):
        # protects content: "..." strings
        str = self._reverse_default_xcss_vars_re.sub(lambda m: m.group(0) + self._reverse_default_xcss_vars.get(m.group(2)) + m.group(3), str)

        # removes multiple line comments
        str = self._ml_comment_re.sub('', str)

        # removes inline comments, but not :// (protocol)
        str = self._sl_comment_re.sub('', str)

        # expand the space in rules
        str = self._expand_rules_space_re.sub(' {', str)
        # collapse the space in properties blocks
        str = self._collapse_properties_space_re.sub(r'\1{', str)
        # Fixe tabs and spaces in ' extends '
        str = self._fix_extends_re.sub(' extends ', str)

        my_rules = []
        context = {}
        options = {}
        for _selectors, codestr, lose in self.locate_blocks(str):
            if lose is not None:
                self.process_properties(lose, context, options)
            elif _selectors[-1] == ':':
                self.process_properties(_selectors + '{' + codestr + '}', context, options)
            else:
                rule, name = (_selectors.split(None, 1)+[''])[:2]
                rule = rule.strip()
                name = name.strip()
                if rule == '@variables' or rule == 'vars': # vars for backwards xCSS compatibility
                    if name:
                        name =  name + '.'
                    self.process_properties(codestr, self.xcss_vars, self.xcss_opts, self.xcss_vars, name)
                    _selectors = None
                elif rule == '@mixin':
                    if name:
                        funct, _, params = name.partition('(')
                        funct = funct.strip()
                        params = params.strip('()').split(',')
                        q = 0
                        vars = {}
                        defaults = {}
                        new_params = []
                        for param in params:
                            id = chr(97+q)
                            param, _, default = param.partition(':')
                            param = param.strip()
                            default = default.strip()
                            if param:
                                if default:
                                    defaults['$__'+id+'__'] = default.strip()
                                vars[param] = '[$__'+id+'__]'
                                new_params.append(id)
                                q += 1
                        if vars:
                            rename_vars_re = re.compile(r'(?<!\w)(' + '|'.join(map(re.escape, vars.keys())) + r')(?!\w)')
                            codestr = rename_vars_re.sub(lambda m: vars[m.group(0)], codestr)
                        mixin = [ defaults, codestr ]
                        if not new_params:
                            self.xcss_opts['@mixin ' + funct] = mixin
                        while len(new_params):
                            self.xcss_opts['@mixin ' + funct + '('+','.join(new_params)+')'] = mixin
                            param = '$__'+new_params.pop()+'__'
                            if param not in defaults:
                                break
                    _selectors = None
                elif rule == '@prototype':
                    _selectors = name # prototype keyword simply ignored (all selectors are prototypes)
                if _selectors:
                    # normalizing selectors by stripping them and joining them using a single ','
                    _selectors = self.normalize_selectors(_selectors)
                    rule = [ fileid, len(self.rules), codestr, set(), None, None, None, None ]
                    my_rules.append(rule)
                    self.rules.append(rule)
                    self.parts.setdefault(_selectors, [])
                    self.parts[_selectors].append(rule)

        def expand_includes(m):
            funct = m.group(1)
            funct = funct.strip()
            params = m.group(2)
            params = params and params.strip('()').split(',') or []
            q = 0
            _vars = {}
            new_params = []
            for param in params:
                id = chr(97+q)
                param = param.strip()
                _vars['$__'+id+'__'] = param
                new_params.append(id)
                q += 1
            new_params = new_params and '('+','.join(new_params)+')' or ''
            mixin = self.xcss_opts.get('@mixin ' + funct + new_params)
            if mixin:
                codestr = mixin[1]
                vars = mixin[0].copy()
                vars.update(_vars)
                if vars:
                    rename_vars_re = re.compile(r'(?<!\w)(' + '|'.join(map(re.escape, vars.keys())) + r')(?!\w)')
                    codestr = rename_vars_re.sub(lambda m: vars[m.group(0)], codestr)
                return codestr.replace('[', '(').replace(']', ')')
            return m.group(0)

        for rule in my_rules:
            # give each rule a new copy of the context and its options
            rule[CONTEXT] = context.copy()
            rule[OPTIONS] = options.copy()
            rule[CODESTR] = self._includes_re.sub(expand_includes, rule[CODESTR])

    def process_properties(self, codestr, context, options, properties=None, scope=''):
        for p_selectors, p_codestr, lose in self.locate_blocks(codestr):
            if lose is not None:
                codestr = lose
                codes = [ s.strip() for s in codestr.split(';') if s.strip() ]
                for code in codes:
                    prop, value = (re.split(r'[:=]', code, 1) + [''])[:2]
                    try:
                        is_var = (code[len(prop)] == '=')
                    except IndexError:
                        is_var = False

                    prop = prop.strip()
                    if prop:
                        value = value.strip()
                        _prop = scope + prop
                        if prop[0] == '@':
                            prop, name = (prop.split(None, 1)+[''])[:2]
                            prop = prop.strip()
                            name = name.strip()
                            options[prop + ' ' + name] = value
                        elif is_var or prop[0] == '$':
                            if value:
                                context[_prop] = value
                        else:
                            if properties is not None and value:
                                properties[_prop] = value
            elif p_selectors[-1] == ':':
                self.process_properties(p_codestr, context, options, properties, scope + p_selectors[:-1] + '-')

    def parse_properties(self):
        # build final properties:
        for _selectors, rules in self.parts.items():
            for rule in rules:
                fileid, position, codestr, deps, context, options, selectors, properties = rule
                if position is not None and codestr and properties is None:
                    assert selectors is None, "Rule body is repeated for different selectors!"
                    rule[SELECTORS] = _selectors
                    rule[PROPERTIES] = properties = rule[PROPERTIES] or {}
                    rule[CONTEXT] = context = rule[CONTEXT] or {}
                    rule[OPTIONS] = context = rule[OPTIONS] or {}
                    self.process_properties(codestr, context, options, properties)

    def manage_order(self):
        # order rules according with their dependencies
        for rule in self.rules:
            if rule[POSITION] is not None:
                rule[DEPS].add(rule[POSITION]+1)
                # This moves the rules just above the topmost dependency during the sorted() below:
                rule[POSITION] = min(rule[DEPS])
        self.rules = sorted(self.rules, key=lambda o: o[POSITION])

        self.css_files = []
        self._rules = {}
        css_files = set()
        old_fileid = None
        for rule in self.rules:
            fileid, position, codestr, deps, context, options, selectors, properties = rule
            self._rules.setdefault(fileid, [])
            self._rules[fileid].append(rule)
            if position is not None and properties:
                if old_fileid != fileid:
                    old_fileid = fileid
                    if fileid not in css_files:
                        css_files.add(fileid)
                        self.css_files.append(fileid)

    def create_css(self, fileid=None):
        # generate the final CSS string
        result = ''
        if fileid:
            rules = self._rules.get(fileid) or []
        else:
            rules = self.rules

        for rule in rules:
            fileid, position, codestr, deps, context, options, selectors, properties = rule
            #print >>sys.stderr, fileid, position, context, options, selectors, properties
            if position is not None and properties:
                # feel free to modifie the indentations the way you like it
                result += ',\n'.join(selectors.split(',')) + ' {\n'
                if options.get('verbosity', self.verbosity) > 0:
                    result += '\t/* file: ' + fileid + ' */\n'
                    if context:
                        result += '\t/* vars:\n'
                        for k, v in context.items():
                            result += '\t\t' + k + ' = ' + v + ';\n'
                        result += '\t*/\n'
                for prop, value in properties.items():
                    result += '\t' + prop + ': ' + value + ';\n'
                result += '}\n'
        return result

    def search_for_parent(self, parent, c_selectors, c_rules):
        parent_found = None
        for p_selectors, p_rules in self.parts.items():
            _p_selectors, _, _ = p_selectors.partition(' extends ')
            _p_selectors = _p_selectors.split(',')
            new_selectors = set()
            # finds all the parent selectors and parent selectors with another
            # bind selectors behind. For example, if `.specialClass extends .baseClass`,
            # and there is a `.baseClass` selector, the extension should create
            # `.specialClass` for that rule, but if there's also a `.baseClass a`
            # it also should create `.specialClass a`
            for p_selector in _p_selectors:
                if parent in p_selector:
                    # get the new child selector to add (same as the parent selector but with the child name)
                    # since selectors can be together, separated with # or . (i.e. something.parent) check that too:
                    for c_selector in c_selectors.split(','):
                        new_selectors.add(re.sub(parent[0] not in ('#', '.') and r'(?<!\w|-)' or '' + parent + r'(?!\w|-)', c_selector, p_selector))
            if new_selectors:
                new_selectors = self.normalize_selectors(p_selectors, new_selectors)
                # rename node:
                if new_selectors != p_selectors:
                    self.parts.setdefault(new_selectors, [])
                    self.parts[new_selectors].extend(p_rules)
                    del self.parts[p_selectors]

                # save child dependencies:
                for c_rule in c_rules or []:
                    for p_rule in p_rules:
                        p_rule[DEPS].add(c_rule[POSITION]) # position is the "index" of the object

                # add parent:
                parent_found = parent_found or []
                parent_found.extend(p_rules)

        return parent_found

    def manage_multiple_extends(self, parts):
        # To be able to manage multiple extends, you need to
        # destroy the actual node and create many nodes that have
        # mono extend. The first one gets all the css rules
        for _selectors, rules in parts.items():
            if ' extends ' in _selectors:
                selectors, _, parent = _selectors.partition(' extends ')
                parents = parent.split('&')
                del parts[_selectors]
                for parent in parents:
                    new_selectors = selectors + ' extends ' + parent
                    parts.setdefault(new_selectors, [])
                    parts[new_selectors].extend(rules)
                    rules = [] # further rules extending other parents will be empty

    def parse_extends(self):
        self.manage_multiple_extends(self.parts)
        for _selectors, rules in self.parts.items():
            selectors, _, parent = _selectors.partition(' extends ')
            if parent:
                self.parts.setdefault(selectors, [])
                self.parts[selectors].extend(rules)
                if _selectors in self.parts:
                    # It might be that search_for_parent or previous iterations
                    # already have removed the selectors...
                    del self.parts[_selectors]
                parents = self.search_for_parent(parent, selectors, rules)

                assert parents is not None, "Parent not found: %s (%s)" % (parent, selectors)

                # from the parent, copy the context and the options:
                new_context = {}
                new_options = {}
                for parent in parents:
                    new_context.update(parent[CONTEXT])
                    new_options.update(parent[OPTIONS])
                for rule in rules:
                    _new_context = new_context.copy()
                    _new_context.update(rule[CONTEXT])
                    rule[CONTEXT] = _new_context
                    _new_options = new_options.copy()
                    _new_options.update(rule[OPTIONS])
                    rule[OPTIONS] = _new_options

    def normalize_selectors(self, _selectors, selector=None):
        if isinstance(selector, basestring):
            selector = set([selector])
        if ' extends ' in _selectors:
            parents = set()
            selectors = set()
            for key in _selectors.split(','):
                child, _, parent = key.partition(' extends ')
                child = child.strip()
                parent = parent.strip()
                selectors.add(child)
                parents.update(s.strip() for s in parent.split('&') if s.strip())
            if selector:
                selectors.update(selector)
            selectors.discard('')
            if not selectors:
                return None
            parents.discard('')
            if parents:
                return ','.join(sorted(selectors)) + ' extends ' + '&'.join(sorted(parents))
            return ','.join(sorted(selectors))
        else:
            selectors = set(s.strip() for s in _selectors.split(',') if s.strip())
            if selector:
                selectors.update(selector)
            selectors.discard('')
            if not selectors:
                return None
            return ','.join(sorted(selectors))

    def parse_children(self):
        cnt = 0
        children_left = True
        while children_left and cnt < 5:
            cnt += 1
            children_left = False
            for _selectors, rules in self.parts.items():
                nested = False
                interpolated = False
                new_selectors = _selectors
                for rule in rules:
                    fileid, position, codestr, deps, context, options, selectors, properties = rule
                    if not interpolated:
                        # First time only, interpolate the final selectors with whatever variables were inherited:
                        interpolated = True
                        new_selectors = self.use_vars(_selectors, context, options)
                        new_selectors = self.do_math(new_selectors)
                        new_selectors = self.normalize_selectors(new_selectors)
                    if ' {' in codestr:
                        nested = True
                if nested:
                    # remove old selector:
                    del self.parts[_selectors]
                    # manage children or expand children:
                    self.manage_children(new_selectors, rules)
                    # maybe there are some children still left...
                    children_left = True
                else:
                    # No more children, interpolate the plain CSS rule:
                    for rule in rules:
                        fileid, position, codestr, deps, context, options, selectors, properties = rule
                        options = dict(filter(lambda x: not x[0].startswith('@extend '), options.items())) # clean options
                        self.process_properties(codestr, context, options)
                        rule[CODESTR] = self.use_vars(codestr, context, options)
                        for o in options:
                            if o.startswith('@extend '):
                                parents = o[8:].replace(',', '&')
                                if ' extends ' in new_selectors:
                                    new_selectors += '&'+parents
                                else:
                                    new_selectors += ' extends ' + parents
                                new_selectors = self.normalize_selectors(new_selectors)
                    # rename selectors (if interpolated)
                    if new_selectors != _selectors:
                        del self.parts[_selectors]
                        self.parts.setdefault(new_selectors, [])
                        self.parts[new_selectors].extend(rules)

    def manage_children(self, _selectors, rules):
        _selectors, _, _parents = _selectors.partition(' extends ')
        p_selectors = _selectors.split(',')
        construct = self.construct
        if _parents:
            construct += ' extends ' + _parents

        for rule in rules:
            fileid, position, codestr, deps, context, options, selectors, properties = rule

            # Check if the block has nested blocks and work it out:
            if ' {' not in codestr:
                self.process_properties(codestr, context, options)
                c_codestr = self.use_vars(codestr, context, options)
                codestr = construct + ' {' + codestr + '}\n'
            else:
                codestr = construct + ' {}\n' + codestr

            my_rules = []
            def _create_children(c_selectors, c_codestr):
                better_selectors = set()
                c_selectors, _, c_parents = c_selectors.partition(' extends ')
                c_selectors = c_selectors.split(',')
                for c_selector in c_selectors:
                    for p_selector in p_selectors:
                        if c_selector == self.construct:
                            better_selectors.add(p_selector)
                        elif c_selector[0] == '&': # Parent References (SASS)
                            better_selectors.add(p_selector + c_selector[1:])
                        else:
                            better_selectors.add(p_selector + ' ' + c_selector)
                better_selectors = ','.join(sorted(better_selectors))
                if c_parents:
                    better_selectors += ' extends ' + c_parents

                rule[POSITION] = None # Disable old rule
                _rule = [ fileid, position, c_codestr, deps, None, None, None, None ]
                my_rules.append(_rule)
                self.rules.append(_rule)
                self.parts.setdefault(better_selectors, [])
                self.parts[better_selectors].append(_rule)

            for c_selectors, c_codestr, lose in self.locate_blocks(codestr):
                if lose is not None or c_selectors[-1] == ':':
                    # This is either a raw rule or a nested property...
                    if lose is None:
                        # ...it was a nested property or varialble, treat as raw
                        lose = c_selectors + '{' + c_codestr + '}'
                    c_selectors = construct
                    c_codestr = lose.strip()
                    if c_codestr:
                        self.process_properties(c_codestr, context, options)
                        c_codestr = self.use_vars(c_codestr, context, options)
                        _create_children(c_selectors, c_codestr)
                else:
                    _create_children(c_selectors, c_codestr)

            for rule in my_rules:
                rule[CONTEXT] = context.copy()
                rule[OPTIONS] = options.copy()


__doc__ += """
>>> css = xCSS()

VARIABLES
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/variables

>>> print css.compile('''
... vars {
...     $path = ../img/tmpl1/png;
...     $color1 = #FF00FF;
...     $border = border-top: 1px solid $color1;
... }
... .selector {
...     background-image: url($path/head_bg.png);
...     background-color: $color1;
...     $border;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
    background-image: url(../img/tmpl1/png/head_bg.png);
    background-color: #f0f;
    border-top: 1px solid #f0f;
}


NESTING CHILD OBJECTS
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/children

>>> print css.compile('''
... .selector {
...     a {
...         display: block;
...     }
...     strong {
...         color: blue;
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector a {
    display: block;
}
.selector strong {
    color: #00f;
}


>>> print css.compile('''
... .selector {
...     self {
...         margin: 20px;
...     }
...     a {
...         display: block;
...     }
...     strong {
...         color: blue;
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
    margin: 20px;
}
.selector a {
    display: block;
}
.selector strong {
    color: #00f;
}


>>> print css.compile('''
... .selector {
...     self {
...         margin: 20px;
...     }
...     a {
...         display: block;
...     }
...     dl {
...         dt {
...             color: red;
...         }
...         dd {
...             self {
...                 color: gray;
...             }
...             span {
...                 text-decoration: underline;
...             }
...         }
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
    margin: 20px;
}
.selector a {
    display: block;
}
.selector dl dt {
    color: red;
}
.selector dl dd {
    color: gray;
}
.selector dl dd span {
    text-decoration: underline;
}


EXTENDING OBJECTS
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/extends

>>> print css.compile('''
...
... .basicClass {
...     padding: 20px;
...     background-color: #FF0000;
... }
... .specialClass extends .basicClass {}
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}


>>> print css.compile('''
... .basicClass {
...     padding: 20px;
...     background-color: #FF0000;
... }
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}
.specialClass {
    padding: 10px;
    font-size: 14px;
}

>>> print css.compile('''
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... .specialLink extends .basicClass a {}
... .basicClass {
...     self {
...         padding: 20px;
...         background-color: #FF0000;
...     }
...     a {
...         text-decoration: none;
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}
.basicClass a,
.specialClass a,
.specialLink {
    text-decoration: none;
}
.specialClass {
    padding: 10px;
    font-size: 14px;
}

>>> print css.compile('''
... .basicList {
...     li {
...         padding: 5px 10px;
...         border-bottom: 1px solid #000000;
...     }
...     dd {
...         margin: 4px;
...     }
...     span {
...         display: inline-block;
...     }
... }
... .roundBox {
...     some: props;
... }
... .specialClass extends .basicList & .roundBox {}
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicList li,
.specialClass li {
	padding: 5px 10px;
	border-bottom: 1px solid #000;
}
.basicList dd,
.specialClass dd {
	margin: 4px;
}
.basicList span,
.specialClass span {
	display: inline-block;
}
.roundBox,
.specialClass {
	some: props;
}

>>> print css.compile('''.basicList {
...     li {
...         padding: 5px 10px;
...         border-bottom: 1px solid #000000;
...     }
...     dd {
...         margin: 4px;
...     }
...     span {
...         display: inline-block;
...     }
... }
... .specialClass {
...     dt extends .basicList li {}
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicList li,
.specialClass dt {
    padding: 5px 10px;
    border-bottom: 1px solid #000;
}
.basicList dd {
    margin: 4px;
}
.basicList span {
    display: inline-block;
}

MATH OPERATIONS
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/math

>>> print css.compile('''
... vars {
...     $color = #FFF555;
... }
... .selector {
...     padding: [5px * 2];
...     color: [#ccc * 2];
...     // lets assume $color is '#FFF555'
...     background-color: [$color - #222 + #101010];
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
	padding: 10px;
	color: #fff;
	background-color: #ede343;
}


>>> print css.compile('''
... .selector {
...     padding: [(5px - 3) * (5px - 3)];
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
	padding: 4px;
}


>>> print css.compile('''
... .selector {
...     padding: [5em - 3em + 5px]px;
...     margin: [20 - 10] [30% - 10];
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
	padding: 31px;
	margin: 10 20%;
}


SASS NESTING COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/tutorial.html

>>> print css.compile('''
... /* style.scss */
... #navbar {
...   width: 80%;
...   height: 23px;
...
...   ul { list-style-type: none; }
...   li {
...     float: left;
...     a { font-weight: bold; }
...   }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
#navbar {
	width: 80%;
	height: 23px;
}
#navbar ul {
	list-style-type: none;
}
#navbar li {
	float: left;
}
#navbar li a {
	font-weight: bold;
}


>>> print css.compile('''
... /* style.scss */
... .fakeshadow {
...   border: {
...     style: solid;
...     left: {
...       width: 4px;
...       color: #888;
...     }
...     right: {
...       width: 2px;
...       color: #ccc;
...     }
...   }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.fakeshadow {
	border-style: solid;
	border-left-width: 4px;
	border-left-color: #888;
	border-right-width: 2px;
	border-right-color: #ccc;
}


>>> print css.compile('''
... /* style.scss */
... a {
...   color: #ce4dd6;
...   &:hover { color: #ffb3ff; }
...   &:visited { color: #c458cb; }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
a {
	color: #ce4dd6;
}
a:hover {
	color: #ffb3ff;
}
a:visited {
	color: #c458cb;
}


SASS VARIABLES COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/tutorial.html

>>> print css.compile('''
... /* style.scss */
... $main-color: #ce4dd6;
... $style: solid;
...
... #navbar {
...   border-bottom: {
...     color: $main-color;
...     style: $style;
...   }
... }
...
... a {
...   color: $main-color;
...   &:hover { border-bottom: $style 1px; }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
#navbar {
	border-bottom-color: #ce4dd6;
	border-bottom-style: solid;
}
a {
	color: #ce4dd6;
}
a:hover {
	border-bottom: solid 1px;
}


SASS INTERPOLATION COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/tutorial.html

>>> print css.compile('''
... /* style.scss */
... $side: top;
... $radius: 10px;
... 
... .rounded-#{$side} {
...   border-#{$side}-radius: $radius;
...   -moz-border-radius-#{$side}: $radius;
...   -webkit-border-#{$side}-radius: $radius;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.rounded-top {
	border-top-radius: 10px;
	-moz-border-radius-top: 10px;
	-webkit-border-top-radius: 10px;
}


SASS MIXINS COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/tutorial.html

>>> print css.compile('''
... /* style.scss */
... 
... @mixin rounded-top {
...   $side: top;
...   $radius: 10px;
... 
...   border-#{$side}-radius: $radius;
...   -moz-border-radius-#{$side}: $radius;
...   -webkit-border-#{$side}-radius: $radius;
... }
... 
... #navbar li { @include rounded-top; }
... #footer { @include rounded-top; }
... ''') #doctest: +NORMALIZE_WHITESPACE
#navbar li {
	border-top-radius: 10px;
	-moz-border-radius-top: 10px;
	-webkit-border-top-radius: 10px;
}
#footer {
	border-top-radius: 10px;
	-moz-border-radius-top: 10px;
	-webkit-border-top-radius: 10px;
}


>>> print css.compile('''
... /* style.scss */
... 
... @mixin rounded($side, $radius: 10px) {
...   border-#{$side}-radius: $radius;
...   -moz-border-radius-#{$side}: $radius;
...   -webkit-border-#{$side}-radius: $radius;
... }
... 
... #navbar li { @include rounded(top); }
... #footer { @include rounded(top, 5px); }
... #sidebar { @include rounded(left, 8px); }
... ''') #doctest: +NORMALIZE_WHITESPACE
#navbar li {
	border-(top)-radius: 10px;
	-moz-border-radius-(top): 10px;
	-webkit-border-(top)-radius: 10px;
}
#footer {
	border-(top)-radius: 5px;
	-moz-border-radius-(top): 5px;
	-webkit-border-(top)-radius: 5px;
}
#sidebar {
	border-(left)-radius: 8px;
	-moz-border-radius-(left): 8px;
	-webkit-border-(left)-radius: 8px;
}


SASS EXTEND COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html#extend

>>> from xcss import *
>>> css = xCSS()
>>> 
>>> 
>>> print css.compile('''
... .error {
...   border: 1px #f00;
...   background-color: #fdd;
... }
... .error.intrusion {
...   background-image: url("/image/hacked.png");
... }
... .seriousError {
...   @extend .error;
...   border-width: 3px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.error,
.seriousError {
	border: 1px red;
	background-color: #fdd;
}
.error.intrusion,
.seriousError.intrusion {
	background-image: url("/image/hacked.png");
}
.seriousError {
	border-width: 3px;
}


Multiple Extends
>>> print css.compile('''
... .error {
...   border: 1px #f00;
...   background-color: #fdd;
... }
... .attention {
...   font-size: 3em;
...   background-color: #ff0;
... }
... .seriousError {
...   @extend .error;
...   @extend .attention;
...   border-width: 3px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.error,
.seriousError {
	border: 1px red;
	background-color: #fdd;
}
.attention,
.seriousError {
	font-size: 3em;
	background-color: #ff0;
}
.seriousError {
	border-width: 3px;
}




FROM THE FORUM
--------------------------------------------------------------------------------

http://groups.google.com/group/xcss/browse_thread/thread/6989243973938362#
>>> print css.compile('''
... body {
...     _width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
body {
	_width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
}


http://groups.google.com/group/xcss/browse_thread/thread/2d27ddec3c15c385#
>>> print css.compile('''
... vars {
...     $ie6 = *html;
...     $ie7 = *:first-child+html;
... }
... $ie6 {
...     .a  { color:white; }
...     .b  { color:black; }
... }
... $ie7 {
...     .a  { color:white; }
...     .b  { color:black; }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
*html .a {
	color: #fff;
}
*html .b {
	color: #000;
}
*:first-child+html .a {
	color: #fff;
}
*:first-child+html .b {
	color: #000;
}


http://groups.google.com/group/xcss/browse_thread/thread/04faafb4ef178984#
>>> print css.compile('''
... .basicClass {
...     padding: 20px;
...     background-color: #FF0000;
... }
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}
.specialClass {
    padding: 10px;
    font-size: 14px;
}


TESTS
--------------------------------------------------------------------------------

>>> print css.compile('''
... .coloredClass {
...     $mycolor: green;
...     padding: 20px;
...     background-color: $mycolor;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
    .coloredClass {
    	padding: 20px;
    	background-color: green;
    }


>>> css.xcss_files = {}
>>> css.xcss_files['first.css'] = '''
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... '''
>>> css.xcss_files['second.css'] = '''
... .basicClass {
...     padding: 20px;
...     background-color: #FF0000;
... }
... '''
>>> print css.compile() #doctest: +NORMALIZE_WHITESPACE
/* Generated frm: second.css */
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}
/* Generated frm: first.css */
.specialClass {
    padding: 10px;
    font-size: 14px;
}


>>> print css.compile('''
... .mod {
... 	margin: 10px;
... }
... .mod h1 {
... 	font-size: 40px;
... }
... .cleanBox h1 extends .mod {
... 	font-size: 60px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.cleanBox h1,
.mod {
	margin: 10px;
}
.cleanBox h1,
.mod h1 {
	font-size: 40px;
}
.cleanBox h1 {
	font-size: 60px;
}


ERRORS
--------------------------------------------------------------------------------

http://groups.google.com/group/xcss/browse_thread/thread/5f4f3af046883c3b#
>>> print css.compile('''
... .some-selector { some:prop; }
... .some-selector-more { some:proop; }
... .parent {
...     self extends .some-selector {
...         height: auto
...     }
...     .children {
...         self extends .some-selector-more {
...             height: autoo
...         }
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.parent,
.some-selector {
	some: prop;
}
.parent .children,
.some-selector-more {
	some: proop;
}
.parent {
	height: auto;
}
.parent .children {
	height: autoo;
}


http://groups.google.com/group/xcss/browse_thread/thread/540f8ad0771c053b#
>>> print css.compile('''
... .noticeBox {
...     self {
...         background-color:red;
...     }
...     span, p {
...         some: props
...     }
... }
... .errorBox extends .noticeBox {}
... ''') #doctest: +NORMALIZE_WHITESPACE
.errorBox,
.noticeBox {
	background-color: red;
}
.errorBox p,
.errorBox span,
.noticeBox p,
.noticeBox span {
	some: props;
}


http://groups.google.com/group/xcss/browse_thread/thread/b5757c24586c1519#
>>> print css.compile('''
... .mod {
...     self {
...         margin: 10px;
...     }
...     h1 {
...         font-size:40px;
...     }
... }
... .cleanBox extends .mod {
...     h1 {
...         font-size:60px;
...     }
... }
... .cleanBoxExtended extends .cleanBox {}
... .articleBox extends .cleanBox {}
... ''') #doctest: +NORMALIZE_WHITESPACE
.articleBox,
.cleanBox,
.cleanBoxExtended,
.mod {
	margin: 10px;
}
.articleBox h1,
.cleanBox h1,
.cleanBoxExtended h1,
.mod h1 {
	font-size: 40px;
}
.articleBox h1,
.cleanBox h1,
.cleanBoxExtended h1 {
	font-size: 60px;
}

"""
"""


>>> print css.compile('''
... .hoverlink {@extend a:hover}
... a:hover {text-decoration: underline}
... ''') #doctest: +NORMALIZE_WHITESPACE
.hoverlink,
a:hover {
	text-decoration: underline;
}

>>> print css.compile('''
... .hoverlink {@extend a:hover}
... .comment a.user:hover {font-weight: bold}
... ''') #doctest: +NORMALIZE_WHITESPACE
.comment a.user:hover,
.comment .hoverlink.user {
	font-weight: bold;
}


>>> print css.compile('''
... #fake-links .link {@extend a}
... 
... a {
...   color: blue;
...   &:hover {text-decoration: underline}
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
#fake-links .linka,
a {
	color: #00f;
}
#fake-links .link:hover ,
a:hover {
	text-decoration: underline;
}


>>> print css.compile('''
... #admin .tabbar a {font-weight: bold}
... #demo .overview .fakelink {@extend a}
... ''') #doctest: +NORMALIZE_WHITESPACE
#admin .tabbar a,
#admin .tabbar #demo .overview .fakelink,
#demo .overview #admin .tabbar .fakelink {
	font-weight: bold;
}

--------------------------------------------------------------------------------
"""

if __name__ == "__main__":
    import getopt
    # parse options for module imports
    opts, args = getopt.getopt(sys.argv[1:], 't')
    opts = dict(opts)
    if '-t' in opts:
        import doctest
        doctest.testmod()
    else:
        css = xCSS()
        sys.stdout.write(css.compile(sys.stdin.read()))
