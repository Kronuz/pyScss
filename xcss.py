#!/usr/bin/python
#-*- coding: utf-8 -*-
"""
xCSS Framework for Python

@author    German M. Bravo (Kronuz)
           Based on some code from the original xCSS project by Anton Pawlik
@version   0.3
@see       http://xcss.antpaw.org/docs/
           http://sass-lang.com/
           http://oocss.org/spec/css-object-model.html
@copyright (c) 2011 German M. Bravo (Kronuz)
           (c) 2010 Anton Pawlik
@license   MIT License
           http://www.opensource.org/licenses/mit-license.php

xCSS for Python is a superset of CSS that is more powerful, elegant and easier
to maintain than plain-vanilla CSS. The library works as a CSS source code
preprocesor which allows you to use variables, nested rules, mixins, and have
inheritance of rules, all with a CSS-compatible syntax which the preprocessor
then compiles to standard CSS.

xCSS, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten and many bugs have been fixed.

"""

import re
import sys

MEDIA_ROOT = '/usr/local/www/mdubalu/media/'
ASSETS_ROOT = MEDIA_ROOT + 'assets/'
MEDIA_URL = '/media/'
ASSETS_URL = MEDIA_URL + 'assets/'

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
    },
    'any': {
        '%': 1.0 / 100
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
    'verbosity': 0,
    'compress': 1,
    'short_colors': 0,
    'reverse_colors': 0,
}

_short_color_re = re.compile(r'(?<!\w)#([a-f0-9])\1([a-f0-9])\2([a-f0-9])\3\b', re.IGNORECASE)
_long_color_re = re.compile(r'(?<!\w)#([a-f0-9]){2}([a-f0-9]){2}([a-f0-9]){2}\b', re.IGNORECASE)
_reverse_colors = dict((v, k) for k, v in _colors.items())
for long_k, v in _colors.items():
    # Calculate the different possible representations of a color:
    short_k = _short_color_re.sub(r'#\1\2\3', v).lower()
    rgb_k = _long_color_re.sub(lambda m: 'rgb(%d, %d, %d)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
    rgba_k = _long_color_re.sub(lambda m: 'rgba(%d, %d, %d, 1)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
    # get the shortest of all to use it:
    k = min([short_k, long_k, rgb_k, rgba_k], key=len)
    _reverse_colors[long_k] = k
    _reverse_colors[short_k] = k
    _reverse_colors[rgb_k] = k
    _reverse_colors[rgba_k] = k
_reverse_colors_re = re.compile(r'(?<!\w)(' + '|'.join(map(re.escape, _reverse_colors.keys()))+r')\b', re.IGNORECASE)
_colors_re = re.compile(r'\b(' + '|'.join(map(re.escape, _colors.keys()))+r')\b', re.IGNORECASE)

_expr_simple_re = re.compile(r'''
    \#\{.*?\}                 # Global Interpolation only
''', re.VERBOSE)

_expr_re = re.compile(r'''
    \#\{.*?\}                  # Global Interpolation
|
    (?<=\s)                    # Expression should have an space before it
    (?:[\[\(\\-][\[\(\s\-]*)?  # ...then any number of opening parenthesis or spaces
    (?:
        (['"]).*?\1            # If a string, consume the whole thing...
    |
        [#\w.%]+               # ...otherwise get the word, variable or number
        (?:
            [\[\(]             # optionally, then start with a parenthesis
            .*?                # followed by anything...
            [\]\)][\w%]*       # until it closes, then try to get any units
            [\]\)\s\,]*?       # ...and keep closing other parenthesis and parameters
        )?
    )
    (?:                        # Here comes the other expressions (0..n)
        [\]\)\s\,]*?
        (?:\s-\s|[+*/^,])      # Get the operator (minus needs spaces)
        [\[\(\s\-]*
        (?:
            (['"]).*?\2        # If a string, consume the whole thing...
        |
            [#\w.%]+           # ...otherwise get the word, variable or number
            (?:
                [\[\(]         # optionally, then  start with a parenthesis
                .*?            # followed by anything...
                [\]\)][\w%]*   # until it closes, then try to get any units
                [\]\)\s\,]*?   # ...and keep closing other parenthesis and parameters
            )?
        )
    )*
    [\]\)\s\,]*?               # ...keep closing parenthesis
    (?:[\]\)\,]+[\w%]*)?       # and then try to get any units afterwards
''', re.VERBOSE)

#_expr_re = re.compile(r'(\[.*?\])([\s;}]|$|.+?\S)') # <- This is the old method, required parenthesis around the expression
_ml_comment_re = re.compile(r'\/\*(.*?)\*\/', re.DOTALL)
_sl_comment_re = re.compile(r'(?<!\w{2}:)\/\/.*')
_zero_units_re = re.compile(r'\b0(' + '|'.join(map(re.escape, _units)) + r')(?!\w)', re.IGNORECASE)

_includes_re = re.compile(r'@include\s+(.*?)\s*(\((.+?,)*(.+?)\))?\s*([;}]|$)', re.DOTALL)
_remove_decls_re = re.compile(r'(@option\b.*?([;}]|$))', re.DOTALL | re.IGNORECASE)
_spaces_re = re.compile(r'\s+')
_expand_rules_space_re = re.compile(r'\s*{')
_collapse_properties_space_re = re.compile(r'([:#])\s*{')

_reverse_default_xcss_vars = dict((v, k) for k, v in _default_xcss_vars.items())
_reverse_default_xcss_vars_re = re.compile(r'(content.*:.*(\'|").*)(' + '|'.join(map(re.escape, _reverse_default_xcss_vars.keys())) + ')(.*\2)')

_blocks_re = re.compile(r'[{},;]|\n+')

FILEID = 0
POSITION = 1
CODESTR = 2
DEPS = 3
CONTEXT = 4
OPTIONS = 5
SELECTORS = 6
PROPERTIES = 7

class xCSS(object):
    # configuration:
    construct = 'self'
    short_colors = True
    reverse_colors = True

    def __init__(self):
        pass

    def longest_common_prefix(self, seq1, seq2):
        start = 0
        common = 0
        while start < min(len(seq1), len(seq2)):
            if seq1[start] != seq2[start]:
                break
            if seq1[start] == ' ':
                common = start + 1
            elif seq1[start] in ('#', ':', '.'):
                common = start
            start += 1
        return common

    def longest_common_suffix(self, seq1, seq2):
        return self.longest_common_prefix(seq1[::-1], seq2[::-1])

    def locate_blocks(self, str):
        """
        Returns all code blocks between `open` and `close` and a proper key
        that can be multilined as long as it's joined by `joiner`.
        Returns the lose code that's not part of the code as a third item.
        """
        depth = 0
        skip = False
        thin = None
        i = init = safe = lose = 0
        start = end = None
        str_len = len(str)
        for m in _blocks_re.finditer(str):
            i = m.end(0) - 1
            if str[i] == '{':
                if depth == 0:
                    if i > 0 and str[i-1] == '#':
                        skip = True
                    else:
                        start = i
                        if thin is not None and str[thin:i-1].strip():
                            init = thin
                        if lose < init:
                            losestr = str[lose:init].strip()
                            if losestr:
                                yield None, None, str[lose:init]
                            lose = init
                        thin = None
                depth += 1
            elif str[i] == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        if not skip:
                            end = i
                            selectors = str[init:start].strip()
                            codestr = str[start+1:end].strip()
                            if selectors:
                                yield selectors, codestr, None
                            init = safe = lose = end + 1
                            thin = None
                        skip = False
            elif depth == 0:
                if str[i] == ';':
                    init = safe = i + 1
                    thin = None
                elif str[i] == ',':
                    if thin is not None and str[thin:i-1].strip():
                        init = thin
                    thin = None
                    safe = i + 1
                elif str[i] == '\n':
                    if thin is None and str[safe:i-1].strip():
                        thin = i + 1
                    elif thin is not None and str[thin:i-1].strip():
                        init = i + 1
                        thin = None
        yield None, None, str[lose:]

    def normalize_selectors(self, _selectors, extra_selectors=None, extra_parents=None):
        """
        Normalizes or extends selectors in a string.
        An optional extra parameter that can be a list of extra selectors to be
        added to the final normalized selectors string.
        """
        # Fixe tabs and spaces in selectors
        _selectors = _spaces_re.sub(' ', _selectors)

        if isinstance(extra_selectors, basestring):
            extra_selectors = extra_selectors.split(',')

        if isinstance(extra_parents, basestring):
            extra_parents = extra_parents.split('&')

        parents = set()
        if ' extends ' in _selectors:
            selectors = set()
            for key in _selectors.split(','):
                child, _, parent = key.partition(' extends ')
                child = child.strip()
                parent = parent.strip()
                selectors.add(child)
                parents.update(s.strip() for s in parent.split('&') if s.strip())
        else:
            selectors = set(s.strip() for s in _selectors.split(',') if s.strip())
        if extra_selectors:
            selectors.update(s.strip() for s in extra_selectors if s.strip())
        selectors.discard('')
        if not selectors:
            return None
        if extra_parents:
            parents.update(s.strip() for s in extra_parents if s.strip())
        parents.discard('')
        if parents:
            return ','.join(sorted(selectors)) + ' extends ' + '&'.join(sorted(parents))
        return ','.join(sorted(selectors))


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
        cont = _remove_decls_re.sub('', cont)
        cont = remove_vars_re.sub('', cont)

        cnt = 0
        old_cont = None
        while cont != old_cont and cnt < 5:
            cnt += 1
            old_cont = cont

            # interpolate variables:
            cont = interpolate_re.sub(lambda m: xcss_vars[m.group(0)], cont)

        return cont


    def process_properties(self, codestr, context, options, properties=None, scope=''):
        for p_selectors, p_codestr, lose in self.locate_blocks(codestr):
            if lose is not None:
                codestr = lose
                codes = [ s.strip() for s in codestr.split(';') if s.strip() ]
                for code in codes:
                    if code[0] == '@':
                        code, name = (code.split(None, 1)+[''])[:2]
                        if code == '@options':
                            for option in name.split(','):
                                option, value = (option.split(':', 1)+[''])[:2]
                                option = option.strip().lower()
                                value = value.strip()
                                if option:
                                    if value.lower() in ('1', 'true', 't', 'yes', 'y'):
                                        value = 1
                                    elif value.lower() in ('0', 'false', 'f', 'no', 'n'):
                                        value = 0
                                    options[option] = value
                        else:
                            options[code] = name
                    else:
                        prop, value = (re.split(r'[:=]', code, 1) + [''])[:2]
                        try:
                            is_var = (code[len(prop)] == '=')
                        except IndexError:
                            is_var = False
                        prop = prop.strip()
                        if prop:
                            default = False
                            if '!default' in value:
                                default = True
                                value.replace('!default', '')
                            value = value.strip()
                            _prop = scope + prop
                            if is_var or prop[0] == '$':
                                if value and (not default or _prop not in context):
                                    context[_prop] = value
                            else:
                                if properties is not None and value:
                                    properties.append((_prop, value))
            elif p_selectors[-1] == ':':
                self.process_properties(p_codestr, context, options, properties, scope + p_selectors[:-1] + '-')


    def compile(self, input_xcss=None):
        # Initialize
        self.rules = []
        self._rules = {}
        self.parts = {}
        self.css_files = []
        self.xcss_vars = _default_xcss_vars.copy()
        self.xcss_opts = _default_xcss_opts.copy()

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

            # this will manage the order of the rules
            self.manage_order()

        final_cont = ''
        for fileid in self.css_files:
            if fileid != 'string':
                final_cont += '/* Generated from: ' + fileid + ' */\n'
            fcont = self.create_css(fileid)
            final_cont += fcont

        final_cont = self.do_math(final_cont)
        final_cont = self.post_process(final_cont)

        return final_cont

    def parse_xcss_string(self, fileid, str):
        # protects content: "..." strings
        str = _reverse_default_xcss_vars_re.sub(lambda m: m.group(0) + _reverse_default_xcss_vars.get(m.group(2)) + m.group(3), str)

        # removes multiple line comments
        str = _ml_comment_re.sub('', str)

        # removes inline comments, but not :// (protocol)
        str = _sl_comment_re.sub('', str)

        # expand the space in rules
        str = _expand_rules_space_re.sub(' {', str)
        # collapse the space in properties blocks
        str = _collapse_properties_space_re.sub(r'\1{', str)

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

        for _selectors, codestr, lose in self.locate_blocks(str):
            if lose is not None:
                self.process_properties(lose, self.xcss_vars, self.xcss_opts)
            elif _selectors[-1] == ':':
                self.process_properties(_selectors + '{' + codestr + '}', self.xcss_vars, self.xcss_opts)
            else:
                if _selectors[0] == '@':
                    code, name = (_selectors.split(None, 1)+[''])[:2]
                    if code in ('@variables', '@vars'):
                        if name:
                            name =  name + '.'
                        self.process_properties(codestr, self.xcss_vars, self.xcss_opts, self.xcss_vars, name)
                        _selectors = None
                    elif code == '@mixin':
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
                    elif code == '@prototype':
                        _selectors = name # prototype keyword simply ignored (all selectors are prototypes)
                if _selectors:
                    # normalizing selectors by stripping them and joining them using a single ','
                    _selectors = self.normalize_selectors(_selectors)

                    if '@include' in codestr:
                        codestr = _includes_re.sub(expand_includes, codestr)

                    # give each rule a new copy of the context and its options
                    rule = [ fileid, len(self.rules), codestr, set(), self.xcss_vars.copy(), self.xcss_opts.copy(), None, None ]
                    self.rules.append(rule)
                    self.parts.setdefault(_selectors, [])
                    self.parts[_selectors].append(rule)


    def parse_children(self):
        cnt = 0
        children_left = True
        while children_left and cnt < 5:
            cnt += 1
            children_left = False
            for _selectors, rules in self.parts.items():
                new_selectors = _selectors
                interpolated = False
                nested = False
                for rule in rules:
                    if not interpolated:
                        # First time only, interpolate the final selectors with whatever variables were inherited:
                        # (FIXME: Perhaps rules with the same selectors but different contexts would produce different final selectors??)
                        interpolated = True
                        if '#{' in new_selectors or '$' in _selectors:
                            new_selectors = self.use_vars(_selectors, rule[CONTEXT], rule[OPTIONS])
                            new_selectors = self.do_math(new_selectors, _expr_simple_re)
                            new_selectors = self.normalize_selectors(new_selectors)
                    if rule[PROPERTIES] is None:
                        properties = []
                        options = dict(filter(lambda x: not x[0].startswith('@extend '), rule[OPTIONS].items())) # clean options
                        self.process_properties(rule[CODESTR], rule[CONTEXT], rule[OPTIONS], properties)
                        parents = rule[OPTIONS].get('@extend')
                        if parents:
                            parents = parents.replace(',', '&') # @extend can come with comma separated selectors...
                            new_selectors = self.normalize_selectors(new_selectors, extra_parents=parents)
                        rule[SELECTORS] = new_selectors
                        rule[PROPERTIES] = properties
                    if ' {' in rule[CODESTR]:
                        nested = True
                        break
                if nested:
                    # remove old selector:
                    del self.parts[_selectors]
                    # manage children or expand children:
                    self.manage_children(new_selectors, rules)
                    # maybe there are some children still left...
                    children_left = True
                else:
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
                continue
            else:
                codestr = construct + ' {}' + codestr

            def _create_children(c_selectors, c_codestr):
                better_selectors = set()
                c_selectors, _, c_parents = c_selectors.partition(' extends ')
                c_selectors = c_selectors.split(',')
                for c_selector in c_selectors:
                    for p_selector in p_selectors:
                        if c_selector == self.construct:
                            better_selectors.add(p_selector)
                        elif '&' in c_selector: # Parent References
                            better_selectors.add(c_selector.replace('&', p_selector))
                        else:
                            better_selectors.add(p_selector + ' ' + c_selector)
                better_selectors = ','.join(sorted(better_selectors))
                if c_parents:
                    better_selectors += ' extends ' + c_parents

                rule[POSITION] = None # Disable this old rule (perhaps it could simply be removed instead??)
                _rule = [ fileid, position, c_codestr, deps, context.copy(), options.copy(), None, None ]
                self.rules.append(_rule)
                self.parts.setdefault(better_selectors, [])
                self.parts[better_selectors].append(_rule)

            for c_selectors, c_codestr, lose in self.locate_blocks(codestr):
                if lose is not None:
                    # This is either a raw lose rule...
                    _create_children(construct, lose)
                elif c_selectors[-1] == ':':
                    # ...it was a nested property or varialble, treat as raw
                    _create_children(construct, c_selectors + '{' + c_codestr + '}')
                else:
                    _create_children(c_selectors, c_codestr)

    def link_with_parents(self, parent, c_selectors, c_rules):
        """
        Link with a parent for the current child rule.
        If parents found, returns a list of parent rules to the child
        """
        parent_found = None
        for p_selectors, p_rules in self.parts.items():
            _p_selectors, _, _ = p_selectors.partition(' extends ')
            _p_selectors = _p_selectors.split(',')

            new_selectors = set()
            found = False

            # Finds all the parent selectors and parent selectors with another
            # bind selectors behind. For example, if `.specialClass extends .baseClass`,
            # and there is a `.baseClass` selector, the extension should create
            # `.specialClass` for that rule, but if there's also a `.baseClass a`
            # it also should create `.specialClass a`
            for p_selector in _p_selectors:
                if parent in p_selector:
                    # get the new child selector to add (same as the parent selector but with the child name)
                    # since selectors can be together, separated with # or . (i.e. something.parent) check that too:
                    for c_selector in c_selectors.split(','):
                        # Get whatever is different between the two selectors:
                        lcp = self.longest_common_prefix(c_selector, p_selector)
                        if lcp: c_selector = c_selector[lcp:]
                        lcs = self.longest_common_suffix(c_selector, p_selector)
                        if lcs: c_selector = c_selector[:-lcs]
                        # Get the new selectors:
                        prev_symbol = r'(?<![-\w])' if parent[0] not in ('#', '.', ':') else ''
                        post_symbol = r'(?![-\w])'
                        new_parent = re.sub(prev_symbol + parent + post_symbol, c_selector, p_selector)
                        new_selectors.add(new_parent)
                        found = True

            if found:
                # add parent:
                parent_found = parent_found or []
                parent_found.extend(p_rules)

            if new_selectors:
                new_selectors = self.normalize_selectors(p_selectors, new_selectors)
                # rename node:
                if new_selectors != p_selectors:
                    del self.parts[p_selectors]
                    self.parts.setdefault(new_selectors, [])
                    self.parts[new_selectors].extend(p_rules)

                deps = set()
                # save child dependencies:
                for c_rule in c_rules or []:
                    c_rule[SELECTORS] = c_selectors # re-set the SELECTORS for the rules
                    deps.add(c_rule[POSITION])

                for p_rule in p_rules:
                    p_rule[SELECTORS] = new_selectors # re-set the SELECTORS for the rules
                    p_rule[DEPS].update(deps) # position is the "index" of the object

        return parent_found

    def parse_extends(self):
        """
        For each part, create the inheritance parts from the ' extends '
        """
        # To be able to manage multiple extends, you need to
        # destroy the actual node and create many nodes that have
        # mono extend. The first one gets all the css rules
        for _selectors, rules in self.parts.items():
            if ' extends ' in _selectors:
                selectors, _, parent = _selectors.partition(' extends ')
                parents = parent.split('&')
                del self.parts[_selectors]
                for parent in parents:
                    new_selectors = selectors + ' extends ' + parent
                    self.parts.setdefault(new_selectors, [])
                    self.parts[new_selectors].extend(rules)
                    rules = [] # further rules extending other parents will be empty

        for _selectors, rules in self.parts.items():
            selectors, _, parent = _selectors.partition(' extends ')
            if parent:
                if _selectors in self.parts:
                    # It might be that link_with_parents or previous iterations
                    # already have removed the selectors... !!??
                    del self.parts[_selectors] #FIXME: why is this "if" really needed??
                self.parts.setdefault(selectors, [])
                self.parts[selectors].extend(rules)

                parents = self.link_with_parents(parent, selectors, rules)

                assert parents is not None, "Parent not found: %s (%s)" % (parent, selectors)

                # from the parent, inherit the context and the options:
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
        """
        Generate the final CSS string
        """
        result = ''
        if fileid:
            rules = self._rules.get(fileid) or []
        else:
            rules = self.rules

        compress = self.xcss_opts.get('compress', 1)
        if compress:
            sc = False
            sp = ''
            tb = ''
            nl = ''
        else:
            sc = True
            sp = ' '
            tb = '\t'
            nl = '\n'

        for rule in rules:
            fileid, position, codestr, deps, context, options, selectors, properties = rule
            #print >>sys.stderr, fileid, position, context, options, selectors, properties
            if position is not None and properties:
                if '#{' in codestr or '$' in codestr:
                    properties = []
                    codestr = self.use_vars(codestr, context, options)
                    self.process_properties(codestr, context, options, properties)
                # feel free to modifie the indentations the way you like it
                selector = (',' + nl).join(selectors.split(',')) + sp + '{' + nl
                result += selector
                if not compress and options.get('verbosity', 0) > 0:
                    result += tb + '/* file: ' + fileid + ' */' + nl
                    if context:
                        result += tb + '/* vars:' + nl
                        for k, v in context.items():
                            result += tb + tb + k + ' = ' + v + ';' + nl
                        result += tb + '*/' + nl
                for prop, value in properties:
                    property = tb + prop + ':' + sp + value + ';' + nl
                    result += property
                if not sc:
                    if result[-1] == ';':
                        result = result [:-1]
                result += '}' + nl
        return result + '\n'


    def do_math(self, content, _expr_re=_expr_re):
        def calculate(result):
            _base_str = result.group(0)

            if _base_str.isalnum():
                return _base_str

            try:
                better_expr_str = self._replaces[_base_str]
            except KeyError:
                better_expr_str = _base_str

                # If we are in a global variable, we remove
                if better_expr_str[:2] == '#{' and better_expr_str[-1] == '}':
                    better_expr_str = better_expr_str[2:-1]

                # To do math operations, we need to get the color's hex values (for color names)
                # ...also we change brackets to parenthesis:
                better_expr_str = _colors_re.sub(lambda m: _colors.get(m.group(0), m.group(0)), better_expr_str).replace('[', '(').replace(']', ')')

                try:
                    better_expr_str = eval_expr(better_expr_str)
                except:
                    better_expr_str = _base_str # leave untouched otherwise

                self._replaces[_base_str] = better_expr_str
            return better_expr_str

        #print >>sys.stderr, _expr_re.findall(content)
        content = _expr_re.sub(calculate, content)
        return content

    def post_process(self, cont):
        # short colors:
        if self.xcss_opts.get('short_colors', 0):
            cont = _short_color_re.sub(r'#\1\2\3', cont)
        # color names:
        if self.xcss_opts.get('reverse_colors', 0):
            cont = _reverse_colors_re.sub(lambda m: _reverse_colors[m.group(0).lower()], cont)
        # zero units out (i.e. 0px or 0em -> 0):
        cont = _zero_units_re.sub('0', cont)
        return cont

import os
import hashlib
import base64
import time
import datetime
import mimetypes
import glob
import math
import operator
import colorsys
from pyparsing import *
try:
    from PIL import Image
except ImportError:
    Image = None

exprStack = []

def escape(str):
    return re.sub(r'(["\'\\])', '\\\\\g<1>', str)

def unescape(str):
    return re.sub(re.escape('\\')+'(.)', "\g<1>", str)

def pushFirst( strg, loc, toks ):
    exprStack.append( toks[0] )

def pushFunct( strg, loc, toks ):
    toks = toks[0].split(',')
    args = len(toks)
    if strg.endswith('()'):
        args = 0
    exprStack.append( 'funct ' + toks[0] + ':' + str(args))

def pushQuoted( strg, loc, toks ):
    exprStack.append( u'"%s"' % escape(toks[0]))

def pushString( strg, loc, toks ):
    exprStack.append( u"'%s'" % escape(toks[0]) )

def pushUnifier( strg, loc, toks ):
    if toks and toks[0] in _units:
        exprStack.append( 'unary ' + toks[0] )

def pushUMinus( strg, loc, toks ):
    if toks and toks[0]=='-':
        exprStack.append( 'unary -' )

bnf = None
def BNF():
    global bnf
    if not bnf:
        expr = Forward()

        point  = Literal( '.' )
        plus   = Literal( '+' )
        minus  = Literal( '-' )
        mult   = Literal( '*' )
        div    = Literal( '/' )
        expop  = Literal( '^' )
        color  = Literal( '#' )
        lpar   = Literal( '(' ).suppress()
        rpar   = Literal( ')' ).suppress()
        comma  = Literal( ',' )

        __units = None
        for u in _units:
            if not __units:
                __units = Literal( u )
            else:
                __units |= Literal( u )
        units = Combine( __units )

        addop  = plus | minus
        multop = mult | div
        ident  = Word(alphas, '_$' + alphas + nums)
        string = QuotedString('"', escChar='\\', multiline=True) | QuotedString("'", escChar='\\', multiline=True)
        color  = Combine(color + Word(hexnums, exact=8) | # #RRGGBBAA
                         color + Word(hexnums, exact=6) | # #RRGGBB
                         color + Word(hexnums, exact=4) | # #RGBA
                         color + Word(hexnums, exact=3)   # #RGB
        )
        fnumber = Combine(
            Word( nums ) + Optional( point + Optional( Word( nums ) ) ) + Optional( units ) |
            point + Word( nums ) + Optional( units )
        )
        funct  = Combine(ident + lpar + Optional(expr.suppress() + ZeroOrMore(comma + expr.suppress())) + rpar)

        atom = (
            Optional('-') + ( fnumber | color ).setParseAction( pushFirst ) |
            Optional('-') + ( funct ).setParseAction( pushFunct ) |
            Optional('-') + ( string ).setParseAction( pushQuoted ) |
            Optional('-') + ( ident ).setParseAction( pushString ) |
            Optional('-') + ( lpar + expr.suppress() + rpar + Optional( units.setParseAction(pushUnifier) ) )
        ).setParseAction(pushUMinus)

        # by defining exponentiation as 'atom [ ^ factor ]...' instead of 'atom [ ^ atom ]...', we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )

        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )
        bnf = expr
    return bnf

################################################################################
# Compass like functionality for sprites and images:
sprite_maps = {}
def _sprite_map(_glob, *args):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")

    if _glob[0] in sprite_maps:
        sprite_maps[_glob[0]]['_'] = datetime.datetime.now()
    else:

        gutter = 0
        offset_x = 0
        offset_y = 0
        repeat = 'no-repeat'

        files = sorted(glob.glob(MEDIA_ROOT + dequote(_glob[0])))

        times = [ int(os.path.getmtime(file)) for file in files ]

        key = files + times + [ gutter, offset_x, offset_y, repeat ]
        key = base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + '.png'
        asset_path = ASSETS_ROOT + asset_file

        images = tuple( Image.open(file) for file in files )
        names = tuple( os.path.splitext(os.path.basename(file))[0] for file in files )
        files = tuple( file[len(MEDIA_ROOT):] for file in files )
        sizes = tuple( image.size for image in images )
        offsets = []
        if os.path.exists(asset_path):
            filetime = int(os.path.getmtime(asset_path))
            offset = gutter
            for i, image in enumerate(images):
                offsets.append(offset - gutter)
                offset += sizes[i][0] + gutter * 2
        else:
            width = sum(zip(*sizes)[0]) + gutter * len(files) * 2
            height = max(zip(*sizes)[1]) + gutter * 2

            new_image = Image.new(
                mode = 'RGBA',
                size = (width, height),
                color = (0, 0, 0, 0)
            )

            offset = gutter
            for i, image in enumerate(images):
                new_image.paste(image, (offset, gutter))
                offsets.append(offset - gutter)
                offset += sizes[i][0] + gutter * 2

            new_image.save(asset_path)
            filetime = int(time.mktime(datetime.datetime.now().timetuple()))

        url = '%s%s?_=%s' % (MEDIA_URL, asset_file, filetime)
        asset = "url('%s') %dpx %dpx %s" % (escape(url), int(offset_x), int(offset_y), repeat)
        sprite_maps[asset] = dict(zip(names, zip(sizes, files, offsets)))
        sprite_maps[asset]['_'] = datetime.datetime.now()
        sprite_maps[asset]['_f_'] = asset_file
        sprite_maps[asset]['_k_'] = key
        sprite_maps[asset]['_t_'] = filetime
        # Use the sorted list to remove older elements (keep only 500 objects):
        if len(sprite_maps) > 1000:
            for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['_'], reverse=True)[500:]:
                del sprite_maps[a]

    return (asset, None, None, {})

def _sprite_map_name(_map):
    """
    Returns the name of a sprite map The name is derived from the folder than
    contains the sprites.
    """
    sprite_map = sprite_maps.get(_map[0], {})
    if sprite_map:
        return (sprite_map['_k_'], None, None, {})
    return ('', None, None, {})

def _sprite_file(_map, _sprite):
    """
    Returns the relative path (from the images directory) to the original file
    used when construction the sprite. This is suitable for passing to the
    image_width and image_height helpers.
    """
    sprite = sprite_maps.get(_map[0], {}).get(dequote(_sprite[0]))
    if sprite:
        return (sprite[1], None, None, {})
    return ('', None, None, {})

def _sprite(_map, _sprite, _offset_x=None, _offset_y=None):
    """
    Returns the image and background position for use in a single shorthand
    property
    """
    sprite_map = sprite_maps.get(_map[0], {})
    sprite = sprite_map.get(dequote(_sprite[0]))
    if sprite:
        print sprite
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['_f_'], sprite_map['_t_'])
        _offset_x = _offset_x and _offset_x[1] or 0
        _offset_y = _offset_y and _offset_y[1] or 0
        pos = "url('%s') %dpx %dpx" % (escape(url), int(_offset_x - sprite[2]), int(_offset_y))
        return (pos, None, None, {})
    return ('0 0', None, None, {})

def _sprite_url(_map):
    """
    Returns a url to the sprite image.
    """
    if _map[0] in sprite_maps:
        sprite_map = sprite_maps[_map[0]]
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['_f_'], sprite_map['_t_'])
        return (url, None, None, {})
    return ('', None, None, {})

def _sprite_position(_map, _sprite, _offset_x=None, _offset_y=None):
    """
    Returns the position for the original image in the sprite.
    This is suitable for use as a value to background-position.
    """
    sprite = sprite_maps.get(_map[0], {}).get(dequote(_sprite[0]))
    if sprite:
        _offset_x = _offset_x and _offset_x[1] or 0
        _offset_y = _offset_y and _offset_y[1] or 0
        pos = '%dpx %dpx' % (int(_offset_x - sprite[2]), int(_offset_y))
        return (pos, None, None, {})
    return ('0 0', None, None, {})

def _inline_image(_image, _mime_type=None):
    """
    Embeds the contents of a file directly inside your stylesheet, eliminating
    the need for another HTTP request. For small files such images or fonts,
    this can be a performance benefit at the cost of a larger generated CSS
    file.
    """
    file = MEDIA_ROOT+dequote(_image[0])
    print file
    if os.path.exists(file):
        _mime_type = _mime_type and dequote(_mime_type[0]) or mimetypes.guess_type(file)[0]
        file = open(file, 'rb')
        url = 'data:'+_mime_type+';base64,'+base64.b64encode(file.read())
        inline = "url('%s')" % (escape(url),)
        return (inline, None, None, {})
    return ('', None, None, {})

def _image_url(_image):
    """
    Generates a path to an asset found relative to the project's images
    directory.
    """
    file = dequote(_image[0])
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        filetime = int(os.path.getmtime(path))
        url = '%s%s?_=%s' % (MEDIA_URL, file, filetime)
        return (url, None, None, {})
    return ('', None, None, {})

def _image_width(_image):
    """
    Returns the width of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    file = dequote(_image[0])
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        image = Image.open(path)
        width = image.size[0]
        return _float(('', width, None, { 'px': 1 }))
    return _float('', 0.0, None, { 'px': 1 })

def _image_height(_image):
    """
    Returns the height of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    file = dequote(_image[0])
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        image = Image.open(path)
        height = image.size[1]
        return _float(('', height, None, { 'px': 1 }))
    return _float('', 0.0, None, { 'px': 1 })

################################################################################
# Sass functionality:
def float2str(num):
    if isinstance(num, float):
        return ('%0.03f' % num).rstrip('0').rstrip('.')
    return str(num)

# map operator symbols to corresponding arithmetic operations
hex2rgba = {
    9: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), int(c[7:9], 16)),
    7: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 1.0),
    5: lambda c: (int(c[1]*2, 16), int(c[2]*2, 16), int(c[3]*2, 16), int(c[4]*2, 16)),
    4: lambda c: (int(c[1]*2, 16), int(c[2]*2, 16), int(c[3]*2, 16), 1.0),
}

def _rgbhex(hex, d=None):
    _r, _g, _b, _a = hex2rgba[len(hex)](hex)
    _r = ('', _r, None, {})
    _g = ('', _g, None, {})
    _b = ('', _b, None, {})
    _a = ('', _a, None, {})
    return _rgba(_r, _g, _b, _a, d)

def _rgb(_r, _g, _b, d=None):
    return _rgba(_r, _g, _b, ('', 1.0, None, {}), d)

def _rgba(_r, _g, _b, _a, d=None):
    r = _r[1]
    g = _g[1]
    b = _b[1]
    a = _a[1]
    rp = 1 if '%' in _r[3] else 0
    gp = 1 if '%' in _g[3] else 0
    bp = 1 if '%' in _b[3] else 0
    r = r * 255.0 if rp else 0.0 if r < 0 else 255.0 if r > 255 else r
    g = g * 255.0 if gp else 0.0 if g < 0 else 255.0 if g > 255 else g
    b = b * 255.0 if bp else 0.0 if b < 0 else 255.0 if b > 255 else b
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    if a == 1:
        d = d or {}
        d.setdefault('rgb', 0)
        d['rgb'] += 1
        d = { 'rgb': 1 }
        p = rp + gp + bp
        if p:
            d.setdefault('%', 0)
            d['%'] = p
        return ('#%02x%02x%02x' % (r,g,b), None, (r, g, b, 1.0), d)
    else:
        d = d or {}
        d.setdefault('rgba', 0)
        d['rgba'] += 1
        p = rp + gp + bp
        if p:
            d.setdefault('%', 0)
            d['%'] = p
        return ('rgba(%d, %d, %d, %s)' % (int(round(r)), int(round(g)), int(round(b)), float2str(a)), None, (r, g, b, a), d)

def _hsl(_h, _s, _l, d=None):
    return _hsla(_h, _s, _l, ('', 1.0, None, {}), d)

def _hsla(_h, _s, _l, _a, d=None):
    h = _h[1]
    s = _s[1]
    l = _l[1]
    a = _a[1]
    hp = 1 if '%' in _h[3] else 0
    sp = 1 if '%' in _s[3] else 0
    lp = 1 if '%' in _l[3] else 0
    h = h * 360.0 if hp else h % 360.0
    s = 0.0 if s < 0 else 1.0 if s > 1 else s
    l = 0.0 if l < 0 else 1.0 if l > 1 else l
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    r, g, b = colorsys.hls_to_rgb(h/360.0, l, s)
    if a == 1:
        d = d or {}
        d.setdefault('hsl', 0)
        d['hsl'] += 1
        p = hp + sp + lp
        if p:
            d.setdefault('%', 0)
            d['%'] = p
        return ('hsl(%s, %s%%, %s%%)' % (float2str(h), float2str(s*100.0), float2str(l*100.0)), None, (r*255, g*255, b*255, 1.0), d)
    else:
        d = {}
        d.setdefault('hsla', 0)
        d['hsla'] += 1
        p = hp + sp + lp + ap
        if p:
            d.setdefault('%', 0)
            d['%'] = p
        return ('hsla(%s, %s%%, %s%%)' % (float2str(h), float2str(s*100.0), float2str(l*100.0), float2str(a)), None, (r*255, g*255, b*255, a), d)

def _float(val):
    _val = val[1]
    val[3].pop(None, None)
    units = sorted(val[3], key=val[3].get, reverse=True)
    if units:
        units_type = set()
        for unit in units:
            units_type.add(_conv_mapping.get(unit))
        unit = units[0]
        unit_type = _conv_mapping.get(unit)
        factor = _conv.get(unit_type, {}).get(unit, 1)
        assert len(units_type) <= 1, "Units mismatch"
        _val /= factor
        _val = float2str(_val)

        if unit in _units:
            _val += unit
    _val = float2str(_val)
    return (_val, val[1], val[2], val[3])

def __rgba_add(_color, _r, _g, _b, _a, d=None):
    r = ('', _color[2][0] + _r, None, {})
    g = ('', _color[2][1] + _g, None, {})
    b = ('', _color[2][2] + _b, None, {})
    a = ('', _color[2][3] + _a, None, {})
    return _rgba(r, g, b, a, d)

def _opacify(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __rgba_add(_color, 0, 0, 0, a)

def _transparentize(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __rgba_add(_color, 0, 0, 0, -a)

def __hsla_add(_color, _h, _s, _l, _a, d=None):
    h, l, s = colorsys.rgb_to_hls(_color[2][0]/255.0, _color[2][1]/255.0, _color[2][2]/255.0)
    h = ('', h*360.0 + _h, None, {})
    s = ('', s + _s, None, {'%': 1})
    l = ('', l + _l, None, {'%': 1})
    a = ('', _color[2][3] + _a, None, {})
    return _hsla(h, s, l, a, d)

def _darken(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __hsla_add(_color, 0, 0, -a, 0)

def _lighten(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __hsla_add(_color, 0, 0, a, 0)

def _saturate(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __hsla_add(_color, 0, a, 0, 0)

def _desaturate(_color, _amount):
    a = _amount[1]
    a = 0.0 if a < 0 else 1.0 if a > 1 else a
    return __hsla_add(_color, 0, -a, 0, 0)

def _grayscale(_color):
    return __hsla_add(_color, 0, -1.0, 0, 0)

def _adjust_hue(_color, _degrees):
    return __hsla_add(_color, _degrees[1] % 360.0, 0, 0, 0)

def _complement(_color):
    return __hsla_add(_color, 180.0, 0, 0, 0)

def _mix(_color1, _color2, _weight=None):
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

    p = _weight[1] if _weight is not None else 0.5
    p = 0.0 if p < 0 else 1.0 if p > 1 else p
    w = p * 2 - 1
    a = _color1[2][3] - _color2[2][3]

    w1 = ((w if (w * a == -1) else (w + a) / (1 + w * a)) + 1) / 2.0
    w2 = 1 - w1

    d = _color1[3].copy()
    for k, v in _color2[3].items():
        d.setdefault(k, 0)
        d[k] += 1
    r = ('', _color1[2][0] * w1 + _color2[2][0] * w2, None, {})
    g = ('', _color1[2][1] * w1 + _color2[2][1] * w2, None, {})
    b = ('', _color1[2][2] * w1 + _color2[2][2] * w2, None, {})
    a = ('', _color1[2][3] * p + _color2[2][3] * (1 - p), None, {})
    return _rgba(r, g, b, a, d)

def _red(_color):
    return _float(('', _color[2][0], None, {}))
def _green(_color):
    return _float(('', _color[2][1], None, {}))
def _blue(_color):
    return _float(('', _color[2][2], None, {}))
def _alpha(_color):
    return _float(('', _color[2][3], None, {}))

def _hue(_color):
    h, l, s = colorsys.rgb_to_hls(_color[2][0]/255.0, _color[2][1]/255.0, _color[2][2]/255.0)
    return _float(('', h*360.0, None, {}))
def _saturation(_color):
    h, l, s = colorsys.rgb_to_hls(_color[2][0]/255.0, _color[2][1]/255.0, _color[2][2]/255.0)
    return _float(('', s, None, { '%': 1 }))
def _lightness(_color):
    h, l, s = colorsys.rgb_to_hls(_color[2][0]/255.0, _color[2][1]/255.0, _color[2][2]/255.0)
    return _float(('', l, None, { '%': 1 }))

################################################################################

def _percentage(_value):
    return _float(('', _value[1], None, { '%': 1 }))

def _unitless(_value):
    return _float(('', _value[1], None, {}))

def dequote(s):
    if s[0] in ('"', "'"):
        s = s[1:-1]
    return unescape(s)

def _unquote(_str):
    return ("'%s'" % escape(dequote(_str[0])), _str[1], _str[2], _str[3])

def _quote(_str):
    if _str[0][0] == '"':
        return _str
    if _str[0][0] == "'":
        s = _str[0][1:-1]
    else:
        s = escape(_str[0])
    return ('"%s"' % s, None, None, {})

################################################################################

def _ops(op):
    _op = op
    op = {
        '+' : operator.add,
        '-' : operator.sub,
        '*' : operator.mul,
        '/' : operator.truediv,
        '^' : operator.pow,
    }[op]
    def __ops(_a, _b):
        d = _a[3].copy()
        for k, v in _b[3].items():
            d.setdefault(k, 0)
            d[k] += 1
        a = _a[1]
        b = _b[1]
        if a is not None and b is not None:
            if '%' in d:
                if '%' not in _a[3]:
                    a /= 100.0;
                if '%' not in _b[3]:
                    b /= 100.0;
            val = op(a, b)
            return _float(('', val, _a[2], d))

        a_str = _a[0]
        b_str = _b[0]
        a_rgba = _a[2]
        b_rgba = _b[2]
        quoting = (a_str[0] == '"' or b_str[0] == '"')
        a_str = dequote(a_str)
        b_str = dequote(b_str)

        if (a_rgba is not None and b is not None or
            b_rgba is not None and a is not None or
           a_rgba is not None and b_rgba is not None):
            __rgba = [0, 0, 0, 0]
            for c in range(4):
                __a = a_rgba[c] if a_rgba is not None else a if c < 3 else None
                __b = b_rgba[c] if b_rgba is not None else b if c < 3 else None
                if c == 3:
                    __rgba[c] = __a if __b is None else __b if __a is None else (__a + __b) / 2
                else:
                    __rgba[c] = op(__a, __b)
            final = _rgba(('',__rgba[0],None,{}), ('',__rgba[1],None,{}), ('',__rgba[2],None,{}), ('',__rgba[3],None,{}))
            final[3].update(d)
        elif quoting:
            if _op == '*':
                val = u'"%s"' % op(int(a) if a is not None else a_str, int(b) if b is not None else b_str)
            else:
                val = u'"%s"' % op(a_str, b_str)
            final = (val, None, None, None, {})
        else:
            val = u"'%s%s%s'" % (a_str, _op, b_str)
            final = (val, None, None, None, {})

        return final
    return __ops
opn = {
    '+' : _ops('+'),
    '-' : _ops('-'),
    '*' : _ops('*'),
    '/' : _ops('/'),
    '^' : _ops('^'),
}

def _func(fn):
    def _func(_val):
        if _val[1] is not None:
            val = fn(_val[1])
        else:
            val = 0.0
        val = ('', val, None, _val[3])
        return _float(val)
    return _func

fncs = {
    'sprite_map:1': _sprite_map,
    'sprite:2': _sprite,
    'sprite:3': _sprite,
    'sprite:4': _sprite,
    'sprite_map_name:1': _sprite_map_name,
    'sprite_file:2': _sprite_file,
    'sprite_url:1': _sprite_url,
    'sprite_position:2': _sprite_position,
    'sprite_position:3': _sprite_position,
    'sprite_position:4': _sprite_position,

    'inline_image:1': _inline_image,
    'inline_image:2': _inline_image,
    'image_url:1': _image_url,
    'image_width:1': _image_width,
    'image_height:1': _image_height,

    'opacify:2': _opacify,
    'fadein:2': _opacify,
    'fade_in:2': _opacify,
    'transparentize:2': _transparentize,
    'fadeout:2': _transparentize,
    'fade_out:2': _transparentize,
    'lighten:2': _lighten,
    'darken:2': _darken,
    'saturate:2': _saturate,
    'desaturate:2': _desaturate,
    'grayscale:1': _grayscale,
    'adjust_hue:2': _adjust_hue,
    'spin:2': _adjust_hue,
    'complement:1': _complement,
    'mix:2': _mix,
    'mix:3': _mix,
    'hsl:3': _hsl,
    'hsla:4': _hsla,
    'rgb:3': _rgb,
    'rgba:4': _rgba,

    'red:1': _red,
    'green:1': _green,
    'blue:1': _blue,
    'alpha:1': _alpha,
    'opacity:1': _alpha,
    'hue:1': _hue,
    'saturation:1': _saturation,
    'lightness:1': _lightness,

    'percentage:1': _percentage,
    'unitless:1': _unitless,
    'quote:1': _quote,
    'unquote:1': _unquote,
    'escape:1': _unquote,
    'e:1': _unquote,

    'sin:1': _func(math.sin),
    'cos:1': _func(math.cos),
    'tan:1': _func(math.tan),
    'abs:1': _func(abs),
    'round:1': _func(round),
    'ceil:1': _func(math.ceil),
    'floor:1': _func(math.floor),
    'pi:0': lambda: _float(('', math.pi, None, {})),
}

def evaluateStack( s ):
    op = s.pop()
    if op.startswith('unary '):
        op = op[6:]
        if op == '-':
            op = evaluateStack( s )
            if op[1] is not None:
                val = -op[1]
                return (float2str(val), val, op[2], op[3])
            elif op[2] is None:
                if op[0][0] == '"':
                    val = op[0]
                else:
                    val = '-' + dequote(op[0])
                return (val, None, op[2], op[3])
            return op
        else:
            val = evaluateStack( s )
            if val[1]:
                val[3].clear()
                val[3][op] = 1
                val = _float(val)
                return val
            return val
    elif op in '+-*/^':
        op2 = evaluateStack( s )
        op1 = evaluateStack( s )
        return opn[op]( op1, op2 )
    elif op.startswith('funct '):
        fn = op[6:]
        
        _, _, args = op.partition(':')
        args = int(args)
        ops = []
        while args:
            args -= 1
            op = evaluateStack( s )
            ops.insert(0, op)
        fn = fncs[fn]
        return fn( *ops )
    elif op[0] == '#':
        return _rgbhex(op)
    elif op[0] in ( '"', "'" ):
        return (op, None, None, {})
    else:
        unit = None
        for i in range(len(op)):
            if op[-i-1].isdigit():
                if i:
                    unit = op[-i:]
                    op = op[:-i]
                break
        val = float(op)
        if unit:
            unit_type = _conv_mapping.get(unit)
            val *= _conv.get(unit_type, {}).get(unit, 1)
            return (op+unit, val, None, {unit:1})
        return (op, val, None, {})

def eval_expr(expr):
    global exprStack
    exprStack = []

    #print >>sys.stderr, '>>',expr,'<<'
    results = BNF().parseString( expr, parseAll=True )
    val = evaluateStack( exprStack[:] )
    #print >>sys.stderr, '--',val,'--'

    val = val[0]
    if val:
        if val[0] == "'":
            val = val[1:-1]
    return val or ''


__doc__ += """
>>> css = xCSS()

VARIABLES
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/variables

>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... @variables {
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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

>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
... @variables {
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
... @options compress:false, short_colors:true, reverse_colors:true;
... .selector {
...     padding: [(5px - 3) * (5px - 3)];
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
	padding: 4px;
}


>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
	border-top-radius: 10px;
	-moz-border-radius-top: 10px;
	-webkit-border-top-radius: 10px;
}
#footer {
	border-top-radius: 5px;
	-moz-border-radius-top: 5px;
	-webkit-border-top-radius: 5px;
}
#sidebar {
	border-left-radius: 8px;
	-moz-border-radius-left: 8px;
	-webkit-border-left-radius: 8px;
}


SASS EXTEND COMPATIBILITY
--------------------------------------------------------------------------------
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html#extend

>>> from xcss import *
>>> css = xCSS()
>>>
>>>
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
... .error {
...   border: 1px #f00;
...   background-color: #fdd;
... }
... .attention {
...   font-size: 3em;
...   background-color: #ff0;
... }
... .seriousError {
...   @extend .error, .attention;
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
... @options compress:false, short_colors:true, reverse_colors:true;
... body {
...     _width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
body {
	_width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
}


http://groups.google.com/group/xcss/browse_thread/thread/2d27ddec3c15c385#
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... @variables {
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
... @options compress:false, short_colors:true, reverse_colors:true;
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


ERRORS
--------------------------------------------------------------------------------

http://groups.google.com/group/xcss/browse_thread/thread/5f4f3af046883c3b#
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
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


TESTS
--------------------------------------------------------------------------------
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... a {
...     $color: rgba(0.872536*255, 0.48481984*255, 0.375464*255, 1);
...     color: $color;
...     color: hsl(13.2, 0.661, 0.624);
...     color-hue: hue($color); // 60deg
...     color-saturation: saturation($color); // 60%
...     color-lightness: lightness($color); // 50%
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
a {
	color: #de7b5f;
	color: hsl(13.2, 66.1%, 62.4%);
	color-hue: 13.2;
	color-saturation: 66.1%;
	color-lightness: 62.4%;
}

>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... .functions {
...     opacify: opacify(rgba(0, 0, 0, 0.5), 0.1); // rgba(0, 0, 0, 0.6)
...     opacify: opacify(rgba(0, 0, 17, 0.8), 0.2); // #001
...
...     transparentize: transparentize(rgba(0, 0, 0, 0.5), 0.1); // rgba(0, 0, 0, 0.4)
...     transparentize: transparentize(rgba(0, 0, 0, 0.8), 0.2); // rgba(0, 0, 0, 0.6)
...
...     lighten: lighten(hsl(0, 0%, 0%), 30%); // hsl(0, 0, 30)
...     lighten: lighten(#800, 20%); // #e00
...
...     darken: darken(hsl(25, 100%, 80%), 30%); // hsl(25, 100%, 50%)
...     darken: darken(#800, 20%); // #200
...
...     saturate: saturate(hsl(120, 30%, 90%), 20%); // hsl(120, 50%, 90%)
...     saturate: saturate(#855, 20%); // #9e3f3f
...
...     desaturate: desaturate(hsl(120, 30%, 90%), 20%); // hsl(120, 10%, 90%)
...     desaturate: desaturate(#855, 20%); // #726b6b
...
...     adjust: adjust_hue(hsl(120, 30%, 90%), 60deg); // hsl(180, 30%, 90%)
...     adjust: adjust_hue(hsl(120, 30%, 90%), 060deg); // hsl(60, 30%, 90%)
...     adjust: adjust_hue(#811, 45deg); // #886a11
...
...     mix: mix(#f00, #00f, 50%); // #7f007f
...     mix: mix(#f00, #00f, 25%); // #3f00bf
...     mix: mix(rgba(255, 0, 0, 0.5), #00f, 50%); // rgba(64, 0, 191, 0.75)
...
...     percentage: percentage(100px / 50px); // 200%
...
...     round: round(10.4px); // 10px
...     round: round(10.6px); // 11px
...
...     ceil: ceil(10.4px); // 11px
...     ceil: ceil(10.6px); // 11px
...
...     floor: floor(10.4px); // 10px
...     floor: floor(10.6px); // 10px
...
...     abs: abs(10px); // 10px
...     abs: abs(-10px); // 10px
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.functions {
    opacify: rgba(0, 0, 0, 0.6);
    opacify: #001;
    transparentize: rgba(0, 0, 0, 0.4);
    transparentize: rgba(0, 0, 0, 0.6);
    lighten: hsl(0, 0, 30%);
    lighten: hsl(0, 100%, 46.667%);
    darken: hsl(25, 100%, 50%);
    darken: hsl(0, 100%, 6.667%);
    saturate: hsl(120, 50%, 90%);
    saturate: hsl(0, 43.077%, 43.333%);
    desaturate: hsl(120, 10%, 90%);
    desaturate: hsl(0, 3.077%, 43.333%);
    adjust: hsl(180, 30%, 90%);
    adjust: hsl(180, 30%, 90%);
    adjust: hsl(45, 77.778%, 30%);
    mix: #7f007f;
    mix: #3f00bf;
    mix: rgba(64, 0, 191, 0.75);
    percentage: 200%;
    round: 10px;
    round: 11px;
    ceil: 11px;
    ceil: 11px;
    floor: 10px;
    floor: 10px;
    abs: 10px;
    abs: 10px;
}

>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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
... @options compress:false, short_colors:true, reverse_colors:true;
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... '''
>>> css.xcss_files['second.css'] = '''
... @options compress:false, short_colors:true, reverse_colors:true;
... .basicClass {
...     padding: 20px;
...     background-color: #FF0000;
... }
... '''
>>> print css.compile() #doctest: +NORMALIZE_WHITESPACE
/* Generated from: second.css */
.basicClass,
.specialClass {
    padding: 20px;
    background-color: red;
}
/* Generated from: first.css */
.specialClass {
    padding: 10px;
    font-size: 14px;
}


>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... a, button {
...     color: blue;
...     &:hover, .some & {
...         text-decoration: underline;
...     }
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
a,
button {
    color: #00f;
}
.some a,
.some button,
a:hover,
button:hover {
    text-decoration: underline;
}


All styles defined for a:hover are also applied to .hoverlink:
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... a:hover { text-decoration: underline }
... .hoverlink { @extend a:hover }
... ''') #doctest: +NORMALIZE_WHITESPACE
.hoverlink,
a:hover {
	text-decoration: underline;
}


http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... #fake-links .link {@extend a}
...
... a {
...   color: blue;
...   &:hover {text-decoration: underline}
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
#fake-links .link,
a {
	color: #00f;
}
#fake-links .link:hover,
a:hover {
	text-decoration: underline;
}


>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
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


"""
"""
ADVANCED STUFF, NOT SUPPORTED (FROM SASS):
--------------------------------------------------------------------------------
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html

Any rule that uses a:hover will also work for .hoverlink, even if they have other selectors as well
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... .comment a.user:hover { font-weight: bold }
... .hoverlink { @extend a:hover }
... ''') #doctest: +NORMALIZE_WHITESPACE
.comment a.user:hover,
.comment .hoverlink.user {
	font-weight: bold;
}


Sometimes a selector sequence extends another selector that appears in another
sequence. In this case, the two sequences need to be merged.
While it would technically be possible to generate all selectors that could
possibly match either sequence, this would make the stylesheet far too large.
The simple example above, for instance, would require ten selectors. Instead,
Sass generates only selectors that are likely to be useful.
>>> print css.compile('''
... @options compress:false, short_colors:true, reverse_colors:true;
... #admin .tabbar a { font-weight: bold }
... #demo .overview .fakelink { @extend a }
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
