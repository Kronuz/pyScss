#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
pyScss, a Scss compiler for Python

@author     German M. Bravo (Kronuz)
@version    1.0 beta
@see        https://github.com/Kronuz/pyScss
@copyright  (c) 2011 German M. Bravo (Kronuz)
@license    MIT License
            http://www.opensource.org/licenses/mit-license.php

pyScss compiles Scss, a superset of CSS that is more powerful, elegant and
easier to maintain than plain-vanilla CSS. The library acts as a CSS source code
preprocesor which allows you to use variables, nested rules, mixins, andhave
inheritance of rules, all with a CSS-compatible syntax which the preprocessor
then compiles to standard CSS.

Scss, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten, many bugs have been fixed and it
has been extensively extended to support almost the full range of Sass' Scss
syntax and functionality.

Bits of code in pyScss come from various projects:
Compass:
    (c) 2009 Christopher M. Eppstein
    http://compass-style.org/
Sass:
    (c) 2006-2009 Hampton Catlin and Nathan Weizenbaum
    http://sass-lang.com/
xCSS:
    (c) 2010 Anton Pawlik
    http://xcss.antpaw.org/docs/

"""
################################################################################
# Configuration:

# Sass @import load_paths:
LOAD_PATHS = '/usr/local/www/project/sass/frameworks/'
# Media base root path where images, fonts and other resources are located:
MEDIA_ROOT = '/usr/local/www/project/media/'
# Assets path, where new sprite files are created:
ASSETS_ROOT = MEDIA_ROOT + 'assets/'
# Urls for the media and assets:
MEDIA_URL = '/media/'
ASSETS_URL = MEDIA_URL + 'assets/'

################################################################################
import re
import sys
import time
import textwrap

# units and conversions
_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
_units_weights = {
    'em': 10,
    'mm': 10,
    'ms': 10,
    'hz': 10,
    '%': 100,
}
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
_conv_type = {}
_conv_factor = {}
for t, m in _conv.items():
    for k, f in m.items():
        _conv_type[k] = t
        _conv_factor[k] = f
del t, m, k, f

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

_default_scss_vars = {
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

_default_scss_opts = {
    'verbosity': 0,
    'compress': 1,
    'compress_short_colors': 1, # Converts things like #RRGGBB to #RGB
    'compress_reverse_colors': 1, # Gets the shortest name of all for colors
    'short_colors': 0, # Converts things like #RRGGBB to #RGB
    'reverse_colors': 0, # Gets the shortest name of all for colors
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
_reverse_colors_re = re.compile(r'(?<![-\w])(' + '|'.join(map(re.escape, _reverse_colors))+r')(?![-\w])', re.IGNORECASE)
_colors_re = re.compile(r'(?<![-\w])(' + '|'.join(map(re.escape, _colors))+r')(?![-\w])', re.IGNORECASE)

_expr_glob_re = re.compile(r'''
    \#\{.*?\}                   # Global Interpolation only
''', re.VERBOSE)

_expr_re = re.compile(r'''
(?:
    \#\{.*?\}                   # Global Interpolation only
|
    (?<=:\s)[^\{;}]+            # Any properties in rules
)
''', re.VERBOSE)

_ml_comment_re = re.compile(r'\/\*(.*?)\*\/', re.DOTALL)
_sl_comment_re = re.compile(r'(?<!\w{2}:)\/\/.*')
_zero_units_re = re.compile(r'\b0(' + '|'.join(map(re.escape, _units)) + r')(?!\w)', re.IGNORECASE)
_zero_re = re.compile(r'\b0\.(?=\d)')

_interpolate_re = re.compile(r'(?:\#\{)?(\$[-\w]+)\}?')
_spaces_re = re.compile(r'\s+')
_expand_rules_space_re = re.compile(r'\s*{')
_collapse_properties_space_re = re.compile(r'([:#])\s*{')

_reverse_default_scss_vars = dict((v, k) for k, v in _default_scss_vars.items())
_reverse_default_scss_vars_re = re.compile(r'(content.*:.*(\'|").*)(' + '|'.join(map(re.escape, _reverse_default_scss_vars)) + ')(.*\2)')

_blocks_re = re.compile(r'[{},;()\'"]|\n+|$')

_skip_word_re = re.compile(r'-?[\w\s#.,:%]*$|[\w\-#.,:%]*$', re.MULTILINE)
_skip_re = re.compile(r'''
    (?:url|alpha)\([^)]*\)$
|
    [\w\-#.,:%]+(?:\s+[\w\-#.,:%]+)*$
''', re.MULTILINE | re.IGNORECASE | re.VERBOSE)
_has_code_re = re.compile('''
    (?:^|(?<=[{;}]))            # the character just before it should be a '{', a ';' or a '}'
    \s*                         # ...followed by any number of spaces
    (?:
        (?:
            \+
        |
            @include
        |
            @mixin
        |
            @if
        |
            @else
        |
            @for
        )
        (?![^(:;}]*['"])
    |
        @import
    )
''', re.VERBOSE)

FILEID = 0
POSITION = 1
CODESTR = 2
DEPS = 3
CONTEXT = 4
OPTIONS = 5
SELECTORS = 6
PROPERTIES = 7
PATH = 8

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print >>sys.stderr, '%s took %0.3fs' % (func.func_name, (t2-t1))
        return res
    return wrapper

def split_params(params):
    params = params.split(',') or []
    if params:
        final_params = []
        param = params.pop(0)
        try:
            while True:
                while param.count('(') != param.count(')'):
                    try:
                        param = param + ',' + params.pop(0)
                    except IndexError:
                        break
                final_params.append(param)
                param = params.pop(0)
        except IndexError:
            pass
        params = final_params
    return params

def dequote(str):
    if str and str[0] in ('"', "'"):
        str = str[1:-1]
        str = unescape(str)
    return str

class Scss(object):
    # configuration:
    construct = 'self'

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
        Returns all code blocks between `{` and `}` and a proper key
        that can be multilined as long as it's joined by `,` or enclosed in
        `(` and `)`.
        Returns the "lose" code that's not part of the block as a third item.
        """
        par = 0
        instr = None
        depth = 0
        skip = False
        thin = None
        i = init = safe = lose = 0
        start = end = None

        for m in _blocks_re.finditer(str):
            i = m.end(0) - 1
            if m.start(0) == m.end(0):
                break
            if instr is not None:
                if str[i] == instr:
                    instr = None
            elif str[i] in ('"', "'"):
                instr = str[i]
            elif str[i] == '(':
                par += 1
                thin = None
                safe = i + 1
            elif str[i] == ')':
                par -= 1
            elif not par and not instr:
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
        if depth > 0:
            if not skip:
                #FIXME: raise exception (block not closed!)
                selectors = str[init:start].strip()
                codestr = str[start+1:].strip()
                if selectors:
                    yield selectors, codestr, None
                return
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
            return ''
        if extra_parents:
            parents.update(s.strip() for s in extra_parents if s.strip())
        parents.discard('')
        if parents:
            return ','.join(sorted(selectors)) + ' extends ' + '&'.join(sorted(parents))
        return ','.join(sorted(selectors))

    def apply_vars(self, cont, context, _dequote=False):
        if '$' not in cont:
            return cont
        if cont in context:
            while cont in context:
                _cont = context[cont]
                if _cont == cont:
                    break
                cont = _cont
            return cont
        # Flatten the context (no variables mapping to variables)
        flat_context = {}
        for k, v in context.items():
            while v in context:
                _v = context[v]
                if _v == v:
                    break
                v = _v
            flat_context[k] = v
        # Interpolate variables:
        def _av(m):
            v = flat_context.get(m.group(1))
            if v:
                if _dequote:
                    v = dequote(v)
                if ' ' in v:
                    v = '(' + v + ')'
            return v if v is not None else m.group(0)
        cont = _interpolate_re.sub(_av, cont)
        return cont

    @print_timing
    def Compilation(self, input_scss=None):
        # Initialize
        self.rules = []
        self._rules = {}
        self.parts = {}
        self.css_files = []
        self.scss_vars = _default_scss_vars.copy()
        self.scss_opts = _default_scss_opts.copy()

        self._contexts = {}
        self._replaces = {}

        if input_scss is not None:
            self.scss_files = {}
            self.scss_files['string'] = input_scss + '\n'
        self.scss_files = self.scss_files or {}

        # Compile
        for fileid, str in self.scss_files.iteritems():
            self.parse_scss_string(fileid, str)

        # this will manage rule: child objects inside of a node
        self.parse_children()

        # this will manage rule: ' extends '
        self.parse_extends()

        # this will manage the order of the rules
        self.manage_order()

        self.parse_properties()

        final_cont = ''
        for fileid in self.css_files:
            if fileid != 'string':
                final_cont += '/* Generated from: ' + fileid + ' */\n'
            fcont = self.create_css(fileid)
            final_cont += fcont

        final_cont = self.pre_process(final_cont)
        final_cont = self.do_math(final_cont)
        final_cont = self.post_process(final_cont)

        return final_cont
    compile = Compilation

    def load_string(self, str):
        # protects content: "..." strings
        str = _reverse_default_scss_vars_re.sub(lambda m: m.group(0) + _reverse_default_scss_vars.get(m.group(2)) + m.group(3), str)

        # removes multiple line comments
        str = _ml_comment_re.sub('', str)

        # removes inline comments, but not :// (protocol)
        str = _sl_comment_re.sub('', str)

        # expand the space in rules
        str = _expand_rules_space_re.sub(' {', str)

        # collapse the space in properties blocks
        str = _collapse_properties_space_re.sub(r'\1{', str)

        return str

    def parse_scss_string(self, fileid, str):
        str = self.load_string(str)
        # give each rule a new copy of the context and its options
        rule = [ fileid, len(self.rules), str, set(), self.scss_vars, self.scss_opts, '', [], './' ]
        self.rules.append(rule)

    def process_properties(self, codestr, context, options, properties=None, scope=''):
        def _process_properties(codestr, scope):
            codes = [ s.strip() for s in codestr.split(';') if s.strip() ]
            for code in codes:
                if code[0] == '@':
                    code, name = (code.split(None, 1)+[''])[:2]
                    if code == '@option':
                        for option in name.split(','):
                            option, value = (option.split(':', 1)+[''])[:2]
                            option = option.strip().lower()
                            value = value.strip()
                            if option:
                                if value.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
                                    value = 1
                                elif value.lower() in ('0', 'false', 'f', 'no', 'n', 'off'):
                                    value = 0
                                options[option] = value
                    elif code == '@extend':
                        options.setdefault(code, set())
                        options[code].update(p.strip() for p in name.replace(',', '&').split('&'))
                        options[code].discard('')
                    else:
                        options[code] = name
                else:
                    prop, value = (re.split(r'[:=]', code, 1) + [None])[:2]
                    try:
                        is_var = (code[len(prop)] == '=')
                    except IndexError:
                        is_var = False
                    prop = prop.strip()
                    if prop:
                        value = value and value.strip()
                        value = value and self.apply_vars(value, context)
                        _prop = scope + prop
                        if is_var or prop[0] == '$' and value is not None:
                            if value:
                                if '!default' in value:
                                    value = value.replace('!default', '').replace('  ', ' ').strip()
                                    if _prop not in context:
                                        context[_prop] = value
                                else:
                                    context[_prop] = value
                        elif properties is not None:
                            _prop = self.apply_vars(_prop, context, True)
                            properties.append((_prop, value))
        for p_selectors, p_codestr, lose in self.locate_blocks(codestr):
            if lose is not None:
                codestr = lose
                _process_properties(lose, scope)
            elif p_selectors[-1] == ':':
                self.process_properties(p_codestr, context, options, properties, scope + p_selectors[:-1] + '-')

    #@print_timing
    def parse_children(self):
        for pos, rule in enumerate(self.rules):
            if rule[POSITION] is not None:
                # Check if the block has nested blocks and work it out:
                if ' {' in rule[CODESTR] or _has_code_re.search(rule[CODESTR]):
                    construct = self.construct
                    _selectors, _, _parents = rule[SELECTORS].partition(' extends ')
                    _selectors = _selectors.split(',')
                    if _parents:
                        construct += ' extends ' + _parents # This passes the inheritance to 'self' children
                    # manage children or expand children:
                    self.manage_children(pos, rule, _selectors, construct)
                #print >>sys.stderr, '='*80
                #for i in range(max(pos-10, 0), min(pos+10, len(self.rules))): l=80; r = self.rules[i]; print >>sys.stderr, ('>>' if rule[POSITION] is None else ' >') if i == pos else '  ', repr(r[POSITION]), repr(r[SELECTORS]), repr(r[CODESTR][:l]+('...' if len(r[CODESTR])>l else '')), repr(r[PROPERTIES])
                # prepare maps:
                if rule[POSITION] is not None:
                    rule[POSITION] = pos
                    selectors = rule[SELECTORS]
                    self.parts.setdefault(selectors, [])
                    self.parts[selectors].append(rule)

    def _insert_child(self, pos, rule, p_selectors, c_selectors, c_codestr, extra_context=None, path=None):
        c_selectors, _, c_parents = c_selectors.partition(' extends ')
        if c_selectors == self.construct:
            # Context and options for constructors ('self') are the same as the parent
            _deps = rule[DEPS]
            _context = rule[CONTEXT]
            _options = rule[OPTIONS]
            if extra_context is not None: # Nested contexts like @import of mixins:
                _context = rule[CONTEXT].copy()
            _context.update(extra_context or {})
            _properties = []

            better_selectors = ','.join(sorted(p_selectors))
        else:
            _deps = set(rule[DEPS])
            _context = rule[CONTEXT].copy()
            _options = rule[OPTIONS].copy()
            _options.pop('@extend', None)
            _context.update(extra_context or {})
            _properties = []

            better_selectors = set()
            c_selectors = c_selectors.split(',')
            for c_selector in c_selectors:
                c_selector = c_selector.strip()
                for p_selector in p_selectors:
                    if c_selector == self.construct:
                        better_selectors.add(p_selector)
                    elif '&' in c_selector: # Parent References
                        better_selectors.add(c_selector.replace('&', p_selector))
                    elif p_selector:
                        better_selectors.add(p_selector + ' ' + c_selector)
                    else:
                        better_selectors.add(c_selector)
            better_selectors = ','.join(sorted(better_selectors))

        self.process_properties(c_codestr, _context, _options, _properties)
        p_parents = _options.get('@extend')

        if p_parents or c_parents:
            if c_parents:
                parents = set(p.strip() for p in c_parents.split('&'))
                parents.update(p_parents or [])
                parents.discard('')
            else:
                parents = p_parents
            if parents:
                better_selectors += ' extends ' + '&'.join(sorted(parents))

        _better_selectors = better_selectors
        better_selectors = self.apply_vars(better_selectors, _context, True)
        better_selectors = self.do_glob_math(better_selectors)
        if _better_selectors != better_selectors:
            # Normalize the whole thing:
            better_selectors = self.normalize_selectors(better_selectors)
        else:
            # ...or only fix tabs and spaces in selectors:
            better_selectors = _spaces_re.sub(' ', better_selectors)

        rule[POSITION] = None # Disable this old rule (perhaps it could simply be removed instead??)...
        # ...and insert new rule
        self.rules.insert(pos + 1, [ rule[FILEID], len(self.rules), c_codestr, _deps, _context, _options, better_selectors, _properties, path or rule[PATH] ])
        return pos + 1

    def manage_children(self, pos, rule, p_selectors, construct):
        fileid, position, codestr, deps, context, options, selectors, properties, path = rule

        rewind = False
        for c_selectors, c_codestr, lose in self.locate_blocks(codestr):
            if rewind:
                if lose is not None:
                    pos = self._insert_child(pos, rule, p_selectors, construct, lose)
                else:
                    pos = self._insert_child(pos, rule, p_selectors, construct, c_selectors + ' {' + c_codestr + '}')
                c_selectors = None
            elif lose is not None:
                # This is either a raw lose rule...
                if _has_code_re.search(lose):
                    new_codestr = []
                    props = [ s.strip() for s in lose.split(';') if s.strip() ]
                    for prop in props:
                        if prop[0] == '+': # expands a '+' at the beginning of a rule as @include
                            code = '@include'
                            name = prop[1:]
                            try:
                                if '(' not in name or name.index(':') < name.index('('):
                                    name = name.replace(':', '(', 1)
                                    if '(' in name: name += ')'
                            except ValueError:
                                pass
                            
                        else:
                            code, name = (prop.split(None, 1)+[''])[:2]
                        if rewind:
                            new_codestr.append(prop)
                        elif code == '@include':
                            # It's an @include, insert pending rules...
                            if new_codestr:
                                lose = ';'.join(new_codestr)
                                pos = self._insert_child(pos, rule, p_selectors, construct, lose)
                                new_codestr = []
                            # ...then insert the include here:

                            funct, params = (name.split('(', 1)+[''])[:2]
                            params = params[:-1]
                            params = split_params(params)

                            defaults = {}
                            new_params = []
                            for param in params:
                                param, _, default = param.partition(':')
                                param = param.strip()
                                default = default.strip()
                                if param:
                                    new_params.append(param)
                                    if default:
                                        defaults[param] = default.strip()
                            mixin = rule[OPTIONS].get('@mixin ' + funct + ':' + str(len(new_params)))
                            if mixin:
                                m_params = mixin[0]
                                m_vars = mixin[1].copy()
                                m_codestr = mixin[2]
                                for i, param in enumerate(new_params):
                                    m_param = m_params[i]
                                    m_vars[m_param] = self.apply_vars(param, context)
                                for p in m_vars:
                                    if p not in new_params:
                                        m_vars[p] = self.apply_vars(m_vars[p], m_vars)
                                pos = self._insert_child(pos, rule, p_selectors, construct, m_codestr, extra_context=m_vars)
                                rewind = True
                        elif code == '@import':
                            i_codestr = None
                            if '..' not in name and '://' not in name and 'url(' not in name: # Protect against going to prohibited places...
                                names = name.split(',')
                                for name in names:
                                    name = dequote(name.strip())
                                    filename = os.path.basename(name)
                                    dirname = os.path.dirname(name)
                                    load_paths = []
                                    i_codestr = None
                                    for path in [ './' ] + LOAD_PATHS.split(','):
                                        for basepath in [ './', rule[PATH] ]:
                                            i_codestr = None
                                            full_path = os.path.realpath(os.path.join(path, basepath, dirname))
                                            if full_path not in load_paths:
                                                try:
                                                    i_codestr = open(os.path.join(full_path, '_'+filename+'.scss')).read()
                                                except:
                                                    try:
                                                        i_codestr = open(os.path.join(full_path, filename+'.scss')).read()
                                                    except:
                                                        try:
                                                            i_codestr = open(os.path.join(full_path, '_'+filename)).read()
                                                        except:
                                                            try:
                                                                i_codestr = open(os.path.join(full_path, filename)).read()
                                                            except:
                                                                pass
                                                if i_codestr is not None:
                                                    break
                                                else:
                                                    load_paths.append(full_path)
                                        if i_codestr is not None:
                                            break
                                    if i_codestr is None:
                                        err = "File to import not found or unreadable: '" + filename + "'\nLoad paths:\n\t" + "\n\t".join(load_paths)
                                        print >>sys.stderr, err
                                    else:
                                        i_codestr = self.load_string(i_codestr)
                                        pos = self._insert_child(pos, rule, p_selectors, construct, i_codestr, path=full_path)
                                        rewind = True
                            else:
                                #new_codestr.append(prop) #FIXME: if I remove the comment, the include is added as a new rule again and it loops
                                pass
                        else:
                            new_codestr.append(prop)
                    if new_codestr:
                        lose = ';'.join(new_codestr)
                        pos = self._insert_child(pos, rule, p_selectors, construct, lose)
                else:
                    pos = self._insert_child(pos, rule, p_selectors, construct, lose)
            elif c_selectors[-1] == ':':
                # ...it was a nested property or varialble, treat as raw
                lose = c_selectors + '{' + c_codestr + '}'
                pos = self._insert_child(pos, rule, p_selectors, construct, lose)
                c_selectors = None
            elif c_selectors[0] == '@':
                code, name = (c_selectors.split(None, 1)+[''])[:2]
                if code in ('@variables', '@vars'):
                    self.process_properties(c_codestr, context, options, context)
                elif code == '@if' or c_selectors.startswith('@else if '):
                    if code != '@if':
                        val = options.get('@if', True)
                        name = c_selectors[9:]
                    else:
                        val = True
                    if val:
                        name = self.apply_vars(name, context)
                        name = self.calculate(name)
                        val = name and name.split()[0].lower()
                        val = bool(False if not val or val in('0', 'false',) else val)
                        options['@if'] = val
                        if val:
                            pos = self._insert_child(pos, rule, p_selectors, construct, c_codestr)
                    c_selectors = None
                elif code == '@else':
                    val = options.get('@if', True)
                    if not val:
                        pos = self._insert_child(pos, rule, p_selectors, construct, c_codestr)
                    c_selectors = None
                elif code == '@for':
                    var, _, name = name.partition('from')
                    name = self.apply_vars(name, context)
                    name = self.calculate(name)

                    start, _, end = name.partition('through')
                    if not end:
                        start, _, end = start.partition('to')
                    var = var.strip()
                    try:
                        start = int(float(start.strip()))
                        end = int(float(end.strip()))
                    except ValueError:
                        pass
                    else:
                        for i in range(start, end + 1):
                            pos = self._insert_child(pos, rule, p_selectors, construct, c_codestr, { var: str(i) })
                    c_selectors = None
                elif code == '@mixin':
                    if name:
                        funct, _, params = name.partition('(')
                        funct = funct.strip()
                        params = params.strip('()').split(',')
                        defaults = {}
                        new_params = []
                        for param in params:
                            param, _, default = param.partition(':')
                            param = param.strip()
                            default = default.strip()
                            if param:
                                new_params.append(param)
                                if default:
                                    default = self.apply_vars(default, context)
                                    defaults[param] = default
                        mixin = [ list(new_params), defaults, self.apply_vars(c_codestr, context) ]
                        # Insert as many @mixin options as the default parameters:
                        while len(new_params):
                            options['@mixin ' + funct + ':' + str(len(new_params))] = mixin
                            param = new_params.pop()
                            if param not in defaults:
                                break
                        if not new_params:
                            options['@mixin ' + funct + ':0'] = mixin
                    c_selectors = None
                elif code == '@prototype':
                    c_selectors = name # prototype keyword simply ignored (all selectors are prototypes)
            if c_selectors:
                pos = self._insert_child(pos, rule, p_selectors, c_selectors, c_codestr)


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

    #@print_timing
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

        cnt = 0
        parents_left = True
        while parents_left and cnt < 10:
            cnt += 1
            parents_left = False
            for _selectors in self.parts.keys():
                selectors, _, parent = _selectors.partition(' extends ')
                if parent:
                    parents_left = True
                    if _selectors not in self.parts:
                        continue # Nodes might have been renamed while linking parents...

                    rules = self.parts[_selectors]

                    del self.parts[_selectors]
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

    #@print_timing
    def manage_order(self):
        # order rules according with their dependencies
        for rule in self.rules:
            if rule[POSITION] is not None:
                rule[DEPS].add(rule[POSITION]+1)
                # This moves the rules just above the topmost dependency during the sorted() below:
                rule[POSITION] = min(rule[DEPS])
        self.rules = sorted(self.rules, key=lambda o: o[POSITION])

    #@print_timing
    def parse_properties(self):
        self.css_files = []
        self._rules = {}
        css_files = set()
        old_fileid = None
        for rule in self.rules:
            if rule[POSITION] is not None:
                fileid, position, codestr, deps, context, options, selectors, properties, path = rule
                #print >>sys.stderr, fileid, position, [ c for c in context if c[1] != '_' ], options.keys(), selectors, deps
                if properties:
                    self._rules.setdefault(fileid, [])
                    self._rules[fileid].append(rule)
                    if old_fileid != fileid:
                        old_fileid = fileid
                        if fileid not in css_files:
                            css_files.add(fileid)
                            self.css_files.append(fileid)

    #@print_timing
    def create_css(self, fileid=None):
        """
        Generate the final CSS string
        """
        result = ''
        if fileid:
            rules = self._rules.get(fileid) or []
        else:
            rules = self.rules

        compress = self.scss_opts.get('compress', 1)
        if compress:
            sc = False
            sp = ''
            tb = ''
            nl = ''
        else:
            sc = True
            sp = ' '
            tb = '  '
            nl = '\n'

        scope = set()
        open = False
        old_selectors = None
        old_property = None
        for rule in rules:
            fileid, position, codestr, deps, context, options, selectors, properties, path = rule
            #print >>sys.stderr, fileid, position, [ c for c in context if c[1] != '_' ], options.keys(), selectors, deps
            if position is not None and properties:
                if old_selectors != selectors:
                    if open:
                        if not sc:
                            if result[-1] == ';':
                                result = result [:-1]
                        result += '}' + nl
                    # feel free to modify the indentations the way you like it
                    selector = (',' + sp).join(selectors.split(',')) + sp + '{'
                    if nl: selector = nl.join(textwrap.wrap(selector))
                    result += selector + nl
                    old_selectors = selectors
                    open = True
                    scope = set()
                if not compress and options.get('verbosity', 0) > 0:
                    result += tb + '/* file: ' + fileid + ' */' + nl
                    if context:
                        result += tb + '/* vars:' + nl
                        for k, v in context.items():
                            result += tb + tb + k + ' = ' + v + ';' + nl
                        result += tb + '*/' + nl
                for prop, value in properties:
                    if value is not None:
                        property = prop + ':' + sp + value
                    else:
                        property = prop
                    if '!default' in property:
                        property = property.replace('!default', '').replace('  ', ' ').strip()
                        if prop in scope:
                            continue
                    if old_property != property:
                        old_property = property
                        scope.add(prop)
                        old_property = property
                        result += tb + property + ';' + nl
        if open:
            if not sc:
                if result[-1] == ';':
                    result = result [:-1]
            result += '}' + nl
        return result + '\n'


    def calculate(self, _base_str):
        try:
            better_expr_str = self._replaces[_base_str]
        except KeyError:
            better_expr_str = _base_str

            if _skip_word_re.match(better_expr_str) and  ' and ' not in better_expr_str and ' or ' not in better_expr_str and 'not ' not in better_expr_str:
                    self._replaces[_base_str] = better_expr_str
                    return better_expr_str

            better_expr_str = eval_expr(better_expr_str)
            if better_expr_str is None:
                better_expr_str = _base_str

            self._replaces[_base_str] = better_expr_str
        return better_expr_str

    def _calculate_expr(self, result):
        _group0 = result.group(0)
        _base_str = _group0
        try:
            better_expr_str = self._replaces[_group0]
        except KeyError:
            # If we are in a global variable, we remove '#{' and '}'
            if _base_str.startswith('#{') and _base_str.endswith('}'):
                _base_str = _base_str[2:-1]

            better_expr_str = _base_str

            if _skip_re.match(better_expr_str) and ' - ' not in better_expr_str:
                self._replaces[_group0] = better_expr_str
                return better_expr_str

            better_expr_str = eval_expr(better_expr_str)
            if better_expr_str is None:
                better_expr_str = _base_str

            self._replaces[_group0] = better_expr_str

        return better_expr_str

    def do_glob_math(self, content):
        content = _expr_glob_re.sub(self._calculate_expr, content)
        return content

    #@print_timing
    def do_math(self, content):
        content = _expr_re.sub(self._calculate_expr, content)
        return content

    #@print_timing
    def pre_process(self, cont):
        # To do math operations, we need to get the color's hex values (for color names)
        # ...also we change brackets to parenthesis:
        def _pp(m):
            v = m.group(0)
            return _colors.get(v, v)
        cont = _colors_re.sub(_pp, cont)
        return cont

    #@print_timing
    def post_process(self, cont):
        compress = self.scss_opts.get('compress', 1) and 'compress_' or ''
        # short colors:
        if self.scss_opts.get(compress+'short_colors', 1):
            cont = _short_color_re.sub(r'#\1\2\3', cont)
        # color names:
        if self.scss_opts.get(compress+'reverse_colors', 1):
            cont = _reverse_colors_re.sub(lambda m: _reverse_colors[m.group(0).lower()], cont)
        if compress:
            # zero units out (i.e. 0px or 0em -> 0):
            cont = _zero_units_re.sub('0', cont)
            # remove zeros before decimal point (i.e. 0.3 -> .3)
            cont = _zero_re.sub('.', cont)
        return cont

import os
import hashlib
import base64
import datetime
import mimetypes
import glob
import math
import operator
import colorsys

try:
    from PIL import Image
except ImportError:
    Image = None

################################################################################

def to_str(num):
    if isinstance(num, float):
        num = ('%0.03f' % num).rstrip('0').rstrip('.')
        return num
    elif isinstance(num, bool):
        return 'true' if num else 'false'
    elif num is None:
        return ''
    return str(num)

def to_float(num):
    if isinstance(num, (float, int)):
        return float(num)
    num = to_str(num)
    try:
        if num and num[-1] == '%':
            return float(num[:-1]) / 100.0
        else:
            return float(num)
    except ValueError:
        return 0.0

hex2rgba = {
    9: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), int(c[7:9], 16)),
    7: lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 1.0),
    5: lambda c: (int(c[1]*2, 16), int(c[2]*2, 16), int(c[3]*2, 16), int(c[4]*2, 16)),
    4: lambda c: (int(c[1]*2, 16), int(c[2]*2, 16), int(c[3]*2, 16), 1.0),
}

def escape(str):
    return re.sub(r'''(["'])''', r'\\\1', str)

def unescape(str):
    return re.sub(r'''\\(['"])''', r'\1', str)

################################################################################
# Sass/Compass Library Functions:

def _rgb(r, g, b, type='rgb'):
    return _rgba(r, g, b, 1.0, type)

def _rgba(r, g, b, a, type='rgba'):
    c = NumberValue(r), NumberValue(g), NumberValue(b), NumberValue(a)

    col = [ c[i].value * 255.0 if (c[i].unit == '%' or c[i].value > 0 and c[i].value <= 1) else
            0.0 if c[i].value < 0 else
            255.0 if c[i].value > 255 else
            c[i].value
            for i in range(3)
          ]
    col += [ 0.0 if c[3].value < 0 else 1.0 if c[3].value > 1 else c[3].value ]
    col += [ type ]
    return ColorValue(col)

def _hsl(h, s, l, type='hsl'):
    return _hsla(h, s, l, 1.0, type)

def _hsla(h, s, l, a, type='hsla'):
    c = NumberValue(h), NumberValue(s), NumberValue(l), NumberValue(a)
    col = [ c[0] if (c[0].unit == '%' or c[0].value > 0 and c[0].value <= 1) else (c[0].value % 360.0) / 360.0 ]
    col += [ c[i].value if (c[i].unit == '%' or c[i].value > 0 and c[i].value <= 1) else
            0.0 if c[i].value < 0 else
            1.0 if c[i].value > 1 else
            c[i].value / 255.0
            for i in range(1, 4)
          ]
    col += [ type ]
    col = ColorValue(tuple([ c * 255.0 for c in colorsys.hls_to_rgb(col[0], col[2], col[1]) ] + [ col[3], type ]))
    return col

def __rgba_add(color, r, g, b, a):
    color = ColorValue(color)
    c = color.value
    a = r, g, b, a
    # Do the additions:
    c = [ c[i] + a[i] for i in range(4) ]
    # Validations:
    r = 255.0, 255.0, 255.0, 1.0
    c = [ 0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4) ]
    color.value = tuple(c)
    return color

def _opacify(color, amount):
    a = NumberValue(amount).value
    return __rgba_add(color, 0, 0, 0, a)

def _transparentize(color, amount):
    a = NumberValue(amount).value
    return __rgba_add(color, 0, 0, 0, -a)

def __hsl_add(color, h, s, l):
    color = ColorValue(color)
    c = color.value
    a = h / 360.0, s, l
    # Convert to HSL:
    h, l, s = list(colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0))
    c = h, s, l
    # Do the additions:
    c = [ 0.0 if c[i] < 0 else 1.0 if c[i] > 1 else c[i] + a[i] for i in range(3) ]
    # Validations:
    c[0] = (c[0] * 360.0) % 360
    r = 360.0, 1.0, 1.0
    c = [ 0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(3) ]
    # Convert back to RGB:
    c = colorsys.hls_to_rgb(c[0] / 360.0, c[2], c[1])
    color.value = (c[0] * 255.0, c[1] * 255.0, c[2] * 255.0, color.value[3])
    return color

def _lighten(color, amount):
    a = NumberValue(amount).value
    return __hsl_add(color, 0, 0, a)

def _darken(color, amount):
    a = NumberValue(amount).value
    return __hsl_add(color, 0, 0, -a)

def _saturate(color, amount):
    a = NumberValue(amount).value
    return __hsl_add(color, 0, a, 0)

def _desaturate(color, amount):
    a = NumberValue(amount).value
    return __hsl_add(color, 0, -a, 0)

def _grayscale(color):
    return __hsl_add(color, 0, -1.0, 0)

def _adjust_hue(color, degrees):
    d = NumberValue(degrees).value
    return __hsl_add(color, d, 0, 0)

def _complement(color):
    return __hsl_add(color, 180.0, 0, 0)


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
    q = [ w1, w1, w1, p ]
    r = [ w2, w2, w2, 1 - p ]

    color = ColorValue(None).merge(c1).merge(c2)
    color.value = [ c1[i] * q[i] + c2[i] * r[i] for i in range(4) ]

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
    return ret
def _saturation(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(s)
    ret.units = { '%': _units_weights.get('%', 1), '_': '%' }
    return ret
def _lightness(color):
    c = ColorValue(color).value
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    ret = NumberValue(l)
    ret.units = { '%': _units_weights.get('%', 1), '_': '%' }
    return ret

def __color_stops(*args):
    if isinstance(args[0], StringValue):
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
        if isinstance(c, ColorValue):
            if prev_color:
                stops.append(None)
            colors.append(c)
            prev_color = True
        else:
            stops.append(NumberValue(c))
            prev_color = False
    if prev_color:
        stops.append(None)
    stops = stops[:len(colors)]
    max_stops = max(s and s.value for s in stops)
    stops = [ s and (s.value / max_stops if s.unit != '%' else s.value) for s in stops ]

    init = 0
    start = None
    for i, s in enumerate(stops+[1.0]):
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

    return zip(stops, colors)

def _grad_color_stops(*args):
    color_stops = __color_stops(*args)
    ret = ', '.join([ 'color-stop(%s, %s)' % (to_str(s), c) for s,c in color_stops ])
    return StringValue(ret)

def _color_stops(*args):
    color_stops = __color_stops(*args)
    ret = ', '.join([ '%s %s%%' % (c, to_str(s*100.0)) for s,c in color_stops ])
    return StringValue(ret)

################################################################################
# Compass like functionality for sprites and images:
sprite_maps = {}
def _sprite_map(g, *args):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.
    """
    g = StringValue(g).value

    if not Image:
        raise Exception("Images manipulation require PIL")

    if g in sprite_maps:
        sprite_maps[glob]['_'] = datetime.datetime.now()
    elif '..' not in g: # Protect against going to prohibited places...
        gutter = 0
        offset_x = 0
        offset_y = 0
        repeat = 'no-repeat'

        files = sorted(glob.glob(MEDIA_ROOT + g))

        if not files:
            return StringValue(None)

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

        url = '%s%s?_=%s' % (ASSETS_URL, asset_file, filetime)
        asset = "url('%s') %dpx %dpx %s" % (escape(url), int(offset_x), int(offset_y), repeat)
        # Use the sorted list to remove older elements (keep only 500 objects):
        if len(sprite_maps) > 1000:
            for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['_'], reverse=True)[500:]:
                del sprite_maps[a]
        # Add the new object:
        sprite_maps[asset] = dict(zip(names, zip(sizes, files, offsets)))
        sprite_maps[asset]['_'] = datetime.datetime.now()
        sprite_maps[asset]['_f_'] = asset_file
        sprite_maps[asset]['_k_'] = key
        sprite_maps[asset]['_t_'] = filetime
    return StringValue(asset)

def _sprite_map_name(_map):
    """
    Returns the name of a sprite map The name is derived from the folder than
    contains the sprites.
    """
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map, {})
    if sprite_map:
        return StringValue(sprite_map['_k_'])
    return StringValue(None)

def _sprite_file(map, sprite):
    """
    Returns the relative path (from the images directory) to the original file
    used when construction the sprite. This is suitable for passing to the
    image_width and image_height helpers.
    """
    map = StringValue(map).value
    sprite = StringValue(sprite).value
    sprite = sprite_maps.get(map, {}).get(sprite)
    if sprite:
        return StringValue(sprite[1])
    return StringValue(None)

def _sprite(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the image and background position for use in a single shorthand
    property
    """
    map = StringValue(map).value
    sprite = StringValue(sprite).value
    sprite_map = sprite_maps.get(map, {})
    sprite = sprite_map.get(sprite)
    if sprite:
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['_f_'], sprite_map['_t_'])
        offset_x = NumberValue(offset_x).value or 0
        offset_y = NumberValue(offset_y).value or 0
        pos = "url('%s') %dpx %dpx" % (escape(url), int(offset_x - sprite[2]), int(offset_y))
        return StringValue(pos)
    return StringValue('0 0')

def _sprite_url(map):
    """
    Returns a url to the sprite image.
    """
    map = StringValue(map).value
    if map in sprite_maps:
        sprite_map = sprite_maps[map]
        url = '%s%s?_=%s' % (ASSETS_URL, sprite_map['_f_'], sprite_map['_t_'])
        return StringValue(url)
    return StringValue(None)

def _sprite_position(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the position for the original image in the sprite.
    This is suitable for use as a value to background-position.
    """
    map = StringValue(map).value
    sprite = StringValue(sprite).value
    sprite = sprite_maps.get(map, {}).get(sprite)
    if sprite:
        offset_x = NumberValue(offset_x).value or 0
        offset_y = NumberValue(offset_y).value or 0
        pos = '%dpx %dpx' % (int(offset_x - sprite[2]), int(offset_y))
        return StringValue(pos)
    return StringValue('0 0')

def _inline_image(image, mime_type=None):
    """
    Embeds the contents of a file directly inside your stylesheet, eliminating
    the need for another HTTP request. For small files such images or fonts,
    this can be a performance benefit at the cost of a larger generated CSS
    file.
    """
    image = StringValue(image).value
    file = MEDIA_ROOT+image
    if os.path.exists(file):
        mime_type = StringValue(mime_type).value or mimetypes.guess_type(file)[0]
        file = open(file, 'rb')
        url = 'data:'+_mime_type+';base64,'+base64.b64encode(file.read())
        inline = "url('%s')" % escape(url)
        return StringValue(inline)
    return StringValue(None)

def _image_url(image):
    """
    Generates a path to an asset found relative to the project's images
    directory.
    """
    file = StringValue(image).value
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        filetime = int(os.path.getmtime(path))
        url = '%s%s?_=%s' % (MEDIA_URL, file, filetime)
        return StringValue(url)
    return StringValue(None)

def _image_width(image):
    """
    Returns the width of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    file = StringValue(image).value
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        image = Image.open(path)
        width = image.size[0]
        ret = NumberValue(width)
        ret.units = { 'px': _units_weights.get('px', 1), '_': 'px' }
        return ret
    ret = NumberValue(0)
    ret.units = { 'px': _units_weights.get('px', 1), '_': 'px' }
    return ret

def _image_height(image):
    """
    Returns the height of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")
    file = StringValue(image).value
    path = MEDIA_ROOT + file
    if os.path.exists(path):
        image = Image.open(path)
        height = image.size[1]
        ret = NumberValue(height)
        ret.units['px'] = _units_weights.get('px', 1)
        return ret
    ret = NumberValue(0)
    ret.units['px'] = _units_weights.get('px', 1)
    return ret

################################################################################
def _opposite_position(*p):
    pos = set()
    new_pos = set()
    for _p in p:
        pos.update(StringValue(_p).value.split())
    if 'center' in pos:
        new_pos.add('center')
    if 'left' in pos:
        new_pos.add('right')
    elif 'right' in pos:
        new_pos.add('right')
    if 'top' in pos:
        new_pos.add('bottom')
    elif 'bottom' in pos:
        new_pos.add('top')
    val = ' '.join(new_pos)
    return StringValue(val)

def _grad_point(*p):
    pos = set()
    hrz = vrt = 50
    for _p in p:
        pos.update(StringValue(_p).value.split())
    if 'left' in pos:
        hrz = 0
    elif 'right' in pos:
        hrz = 100
    if 'top' in pos:
        vrt = 0
    elif 'bottom' in pos:
        vrt = 100
    val = '%s%% %s%%' % (hrz, vrt)
    return val

def _nth(s, n=None):
    """
    Return the Nth item in the string
    """
    s = StringValue(s)
    n = NumberValue(n).value
    val = s.value
    try:
        s.value = val.split()[int(n) - 1]
    except IndexError:
        pass
    return s

def _percentage(value):
    value = NumberValue(value)
    value.units = { '%': _units_weights.get('%', 1), '_': '%' }
    return value

def _unitless(value):
    value = NumberValue(value)
    value.units.clear()
    return value

def _unquote(*args):
    return StringValue(' '.join([ StringValue(s).value for s in args ]))

def _quote(*args):
    return QuotedStringValue(' '.join([ StringValue(s).value for s in args ]))

def _pi():
    return NumberValue(math.pi)

################################################################################
# Specific to pyScss parser functions:

def _convert_to(value, type):
    return value.convert_to(type)

def _inv(sign, value):
    if isinstance(value, NumberValue):
        return value * -1
    elif isinstance(value, BooleanValue):
        return not value
    val = StringValue(value)
    val.value = sign + val.value
    return val

# pyScss data types:

class ParserValue(object):
    def __init__(self, value):
        self.value = value

class Value(object):
    @staticmethod
    def _operatorOperands(tokenlist):
        "generator to extract operators and operands in pairs"
        it = iter(tokenlist)
        while 1:
            try:
                yield (it.next(), it.next())
            except StopIteration:
                break
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
        return '<%s: %s: %s>' % (self.__class__.__name__, repr(self.value), repr(self.tokens))
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
        return self.value and True or False
    def __add__(self, other):
        return self._do_op(self, other, operator.__add__)
    __radd__ = __add__
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
    __rmul__ = __mul__
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
            self.value = tokens.value.lower() in ('true', '1', 'on', 'yes', 't', 'y')
        elif isinstance(tokens, BooleanValue):
            self.value = tokens.value
        elif isinstance(tokens, NumberValue):
            self.value = bool(tokens.value)
        elif isinstance(tokens, (float, int)):
            self.value = bool(tokens)
        else:
            self.value = to_str(tokens).lower() in ('true', '1', 'on', 'yes', 't', 'y')
    def __str__(self):
        return 'true' if self.value else 'false'
    @classmethod
    def _do_cmps(cls, first, second, op):
        first = BooleanValue(first)
        second = BooleanValue(second)
        return op(first.value, second.value)
    @classmethod
    def _do_op(cls, first, second, op):
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
    def __init__(self, tokens):
        self.tokens = tokens
        self.units = {}
        if tokens is None:
            self.value = 0.0
        elif isinstance(tokens, ParserValue):
            self.value = float(tokens.value)
        elif isinstance(tokens, NumberValue):
            self.value = tokens.value
            self.units = tokens.units.copy()
        elif isinstance(tokens, StringValue):
            try:
                if tokens.value and tokens.value[-1] == '%':
                    self.value = to_float(tokens.value[:-1]) / 100.0
                    self.units = { '%': _units_weights.get('%', 1), '_': '%' }
                else:
                    self.value = to_float(tokens.value)
            except ValueError:
                self.value = 0.0
        elif isinstance(tokens, (int, float)):
            self.value = float(tokens)
        else:
            try:
                self.value = to_float(to_str(tokens))
            except ValueError:
                self.value = 0.0
    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, repr(self.value), repr(self.units))
    def __str__(self):
        unit = self.unit
        val = self.value / _conv_factor.get(unit, 1.0)
        val = to_str(val) + unit
        return val
    @classmethod
    def _do_cmps(cls, first, second, op):
        first = NumberValue(first)
        second = NumberValue(second)
        first_type = _conv_type.get(first.unit)
        second_type = _conv_type.get(second.unit)
        if first_type == second_type or first_type is None or second_type is None:
            return op(first.value, second.value)
        else:
            return op(first_type, second_type)
    @classmethod
    def _do_op(cls, first, second, op):
        first = NumberValue(first)
        second = NumberValue(second)
        first_unit = first.unit
        second_unit = second.unit
        if op == operator.__add__ or op == operator.__sub__:
            if first_unit == '%' and not second_unit:
                second.units = { '%': _units_weights.get('%', 1), '_': '%' }
                second.value /= 100.0
            elif second_unit == '%' and not first_unit:
                first.units = { '%': _units_weights.get('%', 1), '_': '%' }
                first.value /= 100.0
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
        if '_' not in self.units:
            self.units['_'] = obj.unit
        return self
    def convert_to(self, type):
        val = self.value
        if not self.unit:
            val *= _conv_factor.get(type, 1.0)
        ret = NumberValue(val)
        ret.units = { type: _units_weights.get(type, 1), '_': type }
        return ret
    @property
    def unit(self):
        unit = ''
        if self.units:
            if '_'in self.units:
                units = self.units.copy()
                _unit = units.pop('_')
                units.setdefault(_unit, 0)
                units[_unit] += _units_weights.get(_unit, 1) # Give more weight to the first unit ever set
            else:
                units = self.units
            units = sorted(units, key=units.get)
            while len(units):
                unit = units.pop()
                if unit:
                    break
        return unit

class ColorValue(Value):
    def __init__(self, tokens):
        self.tokens = tokens
        self.types = {}
        self.value = (0, 0, 0, 1)
        if tokens is None:
            self.value = (0, 0, 0, 1)
        elif isinstance(tokens, ParserValue):
            hex = tokens.value
            self.value = hex2rgba[len(hex)](hex)
            self.types = { 'rgba': 1 }
        elif isinstance(tokens, ColorValue):
            self.value = tokens.value
            self.types = tokens.types.copy()
        elif isinstance(tokens, NumberValue):
            val = tokens.value
            self.value = (val, val, val, 1)
        elif isinstance(tokens, (list, tuple)):
            c = tokens[:4]
            r = 255.0, 255.0, 255.0, 1.0
            c = [ 0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4) ]
            self.value = tuple(c)
            type = tokens[-1]
            if type in ('rgb', 'rgba', 'hsl', 'hsla'):
                self.types = { type: 1 }
        elif isinstance(tokens, (int, float)):
            val = float(tokens)
            self.value = (val, val, val, 1)
        else:
            hex = to_str(tokens)
            try:
                self.value = hex2rgba[len(hex)](hex)
            except:
                try:
                    val = to_float(hex)
                    self.values = (val, val, val, 1)
                except ValueError:
                    try:
                        hex.replace(' ', '').lower()
                        type, _, colors = hex.pertition('(').rstrip(')')
                        if type in ('rgb', 'rgba'):
                            c = tuple(colors.split(','))
                            try:
                                c = [ to_float(c[i]) for i in range(4) ]
                                col = [ 0.0 if c[i] < 0 else 255.0 if c[i] > 255 else c[i] for i in range(3) ]
                                col += [ 0.0 if c[3] < 0 else 1.0 if c[3] > 1 else c[3] ]
                                self.value = tuple(col)
                                self.types = { type: 1 }
                            except:
                                pass
                        if type in ('hsl', 'hsla'):
                            c = colors.split(',')
                            try:
                                c = [ to_float(c[i]) for i in range(4) ]
                                col = [ c[0] % 360.0 ] / 360.0
                                col += [ 0.0 if c[i] < 0 else 1.0 if c[i] > 1 else c[i] for i in range(1,4) ]
                                self.value = tuple([ c * 255.0 for c in colorsys.hls_to_rgb(col[0], col[2], col[1]) ] + [ col[3] ])
                                self.types = { type: 1 }
                            except:
                                pass
                    except:
                        pass
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
            return 'hsla(%s, %s%%, %s%%, %s)' % (to_str(h * 360.0), to_str(s * 100.0), to_str(l * 100.0), to_str(a))
        if c[3] == 1:
            return '#%02x%02x%02x' % (c[0], c[1], c[2])
        return 'rgba(%d, %d, %d, %s)' % (c[0], c[1], c[2], to_str(c[3]))
    @classmethod
    def _do_cmps(cls, first, second, op):
        first = ColorValue(first)
        second = ColorValue(second)
        return op(first.value, second.value)
    @classmethod
    def _do_op(cls, first, second, op):
        first = ColorValue(first)
        second = ColorValue(second)
        val = [ op(first.value[i], second.value[i]) for i in range(4) ]
        val[3] = (first.value[3] + second.value[3]) / 2
        c = val
        r = 255.0, 255.0, 255.0, 1.0
        c = [ 0.0 if c[i] < 0 else r[i] if c[i] > r[i] else c[i] for i in range(4) ]
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
    def convert_to(self, type):
        return QuotedStringValue(self.value + type)
    def __str__(self):
        return '"%s"' % escape(self.value)
    @classmethod
    def _do_cmps(cls, first, second, op):
        first = QuotedStringValue(first)
        second = QuotedStringValue(second)
        return op(first.value, second.value)
    @classmethod
    def _do_op(cls, first, second, op):
        first = QuotedStringValue(first)
        second = QuotedStringValue(second)
        val = op(first.value, second.value)
        ret = QuotedStringValue(None).merge(first).merge(second)
        ret.value = val
        return ret
    def merge(self, obj):
        obj = QuotedStringValue(obj)
        self.value = obj.value
        return self

class StringValue(QuotedStringValue):
    def __str__(self):
        return self.value
    def __add__(self, other):
        if self.__class__ == QuotedStringValue or other.__class__ == QuotedStringValue:
            other = QuotedStringValue(other)
            return QuotedStringValue(self.value + other.value)
        other = StringValue(other)
        return StringValue(self.value + '+' + other.value)
    def __radd__(self, other):
        if self.__class__ == QuotedStringValue or other.__class__ == QuotedStringValue:
            other = QuotedStringValue(other)
            return QuotedStringValue(other.value + self.value)
        other = StringValue(other)
        return StringValue(other.value + '+' + self.value)

# Parser/functions map:
fnct = {
    'sprite-map:1': _sprite_map,
    'sprite:2': _sprite,
    'sprite:3': _sprite,
    'sprite:4': _sprite,
    'sprite-map-name:1': _sprite_map_name,
    'sprite-file:2': _sprite_file,
    'sprite-url:1': _sprite_url,
    'sprite-position:2': _sprite_position,
    'sprite-position:3': _sprite_position,
    'sprite-position:4': _sprite_position,

    'inline-image:1': _inline_image,
    'inline-image:2': _inline_image,
    'image-url:1': _image_url,
    'image-width:1': _image_width,
    'image-height:1': _image_height,

    'opposite-position:n': _opposite_position,
    'grad-point:n': _grad_point,
    'color-stops:n': _color_stops,
    'grad-color-stops:n': _grad_color_stops,

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
    'adjust-hue:2': _adjust_hue,
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

    'nth:2': _nth,
    'first-value-of:1': _nth,

    'percentage:1': _percentage,
    'unitless:1': _unitless,
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
    fnct[u+':2'] = _convert_to

def call(name, args):
    # Function call:
    fn_name = '%s:%d' % (name, len(args))
    try:
        fn = fnct.get(fn_name) or fnct['%s:n' % name]
        node = fn(*args)
    except:
        # Function not found, simply write it as a string:
        node = StringValue(name + '(' + ', '.join(str(a) for a in args) + ')')
    return node

class SyntaxError(Exception):
    """
    When we run into an unexpected token, this is the exception to use
    """
    def __init__(self, pos=-1, msg="Bad Token"):
        Exception.__init__(self)
        self.pos = pos
        self.msg = msg
    def __repr__(self):
        if self.pos < 0: return "#<syntax-error>"
        else: return "SyntaxError[@ char %s: %s]" % (repr(self.pos), self.msg)

class NoMoreTokens(Exception):
    """
    Another exception object, for when we run out of tokens
    """
    pass

class Scanner(object):
    def __init__(self, patterns, ignore, input=None):
        """
        Patterns is [(terminal,regex)...]
        Ignore is [terminal,...];
        Input is a string
        """
        self.tokens = []
        self.restrictions = []
        self.input = input
        self.pos = 0
        self.ignore = ignore
        # The stored patterns are a pair (compiled regex,source
        # regex).  If the patterns variable passed in to the
        # constructor is None, we assume that the class already has a
        # proper .patterns list constructed
        if patterns is not None:
            self.patterns = []
            for k, r in patterns:
                self.patterns.append( (k, re.compile(r)) )

    def reset(self, input):
        self.tokens = []
        self.restrictions = []
        self.input = input
        self.pos = 0
        
    def token(self, i, restrict=None):
        """
        Get the i'th token, and if i is one past the end, then scan
        for another token; restrict is a list of tokens that
        are allowed, or 0 for any token.
        """
        if i == len(self.tokens):
            self.scan(restrict)
        if i < len(self.tokens):
            # Make sure the restriction is more restricted
            if restrict and self.restrictions[i]:
                for r in restrict:
                    if r not in self.restrictions[i]:
                        raise NotImplementedError("Unimplemented: restriction set changed")
            return self.tokens[i]
        raise NoMoreTokens()
    
    def __repr__(self):
        """
        Print the last 10 tokens that have been scanned in
        """
        output = ''
        for t in self.tokens[-10:]:
            output = "%s\n  (@%s)  %s  =  %s" % (output, t[0], t[2], repr(t[3]))
        return output
    
    def scan(self, restrict):
        """
        Should scan another token and add it to the list, self.tokens,
        and add the restriction to self.restrictions
        """
        # Keep looking for a token, ignoring any in self.ignore
        while True:
            # Search the patterns for the longest match, with earlier
            # tokens in the list having preference
            best_match = -1
            best_pat = '(error)'
            for p, regexp in self.patterns:
                # First check to see if we're ignoring this token
                if restrict and p not in restrict and p not in self.ignore:
                    continue
                m = regexp.match(self.input, self.pos)
                if m and len(m.group(0)) > best_match:
                    # We got a match that's better than the previous one
                    best_pat = p
                    best_match = len(m.group(0))
                    break
                    
            # If we didn't find anything, raise an error
            if best_pat == '(error)' and best_match < 0:
                msg = "Bad Token"
                if restrict:
                    msg = "Trying to find one of " + ", ".join(restrict)
                raise SyntaxError(self.pos, msg)

            # If we found something that isn't to be ignored, return it
            if best_pat not in self.ignore or restrict and best_pat in restrict:
                # Create a token with this data
                token = (
                    self.pos,
                    self.pos + best_match,
                    best_pat,
                    self.input[self.pos:self.pos + best_match]
                )
                self.pos = self.pos + best_match
                # Only add this token if it's not in the list
                # (to prevent looping)
                if not self.tokens or token != self.tokens[-1]:
                    self.tokens.append(token)
                    self.restrictions.append(restrict)
                break
            else:
                # This token should be ignored ..
                self.pos += best_match

class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._pos = 0

    def reset(self, input):
        self._scanner.reset(input)
        self._pos = 0

    def _peek(self, *types):
        """
        Returns the token type for lookahead; if there are any args
        then the list of args is the set of token types to allow
        """
        tok = self._scanner.token(self._pos, types)
        return tok[2]
        
    def _scan(self, type):
        """
        Returns the matched text, and moves to the next token
        """
        tok = self._scanner.token(self._pos, [type])
        if tok[2] != type:
            raise SyntaxError(tok[0], "Trying to find " + type)
        self._pos += 1
        return tok[3]

#'|'.join(_units)
## Grammar compiled using Yapps:
class CalculatorScanner(Scanner):
    patterns = [
        ('[ \r\t\n]+', re.compile('[ \r\t\n]+')),
        ('COMMA', re.compile(',')),
        ('LPAR', re.compile('\\(|\\[')),
        ('RPAR', re.compile('\\)|\\]')),
        ('END', re.compile('$')),
        ('MUL', re.compile('[*]')),
        ('DIV', re.compile('/')),
        ('ADD', re.compile('[+]')),
        ('SUB', re.compile('-\\s')),
        ('SIGN', re.compile('-')),
        ('AND', re.compile('and')),
        ('OR', re.compile('or')),
        ('NOT', re.compile('not')),
        ('INV', re.compile('!')),
        ('EQ', re.compile('==')),
        ('NE', re.compile('!=')),
        ('LT', re.compile('<')),
        ('GT', re.compile('>')),
        ('LE', re.compile('<=')),
        ('GE', re.compile('>=')),
        ('STR', re.compile("'[^']*'")),
        ('QSTR', re.compile('"[^"]*"')),
        ('UNITS', re.compile('|'.join(_units))),
        ('NUM', re.compile('(?:\\d+(?:\\.\\d*)?|\\.\\d+)')),
        ('BOOL', re.compile('(?:true|false)')),
        ('COLOR', re.compile('#(?:[a-fA-F0-9]{8}|[a-fA-F0-9]{6}|[a-fA-F0-9]{3,4})')),
        ('ID', re.compile('[-a-zA-Z_][-a-zA-Z0-9_]*')),
    ]
    def __init__(self):
        Scanner.__init__(self,None,['[ \r\t\n]+'])

class Calculator(Parser):
    def goal(self):
        expr = self.expr()
        v = [ str(expr) ]
        while self._peek('END', 'NOT', 'INV', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') != 'END':
            expr = self.expr()
            v.append(str(expr))
        END = self._scan('END')
        return v

    def expr(self):
        and_test = self.and_test()
        v = and_test
        while self._peek('OR', 'RPAR', 'COMMA', 'END', 'NOT', 'INV', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') == 'OR':
            OR = self._scan('OR')
            and_test = self.and_test()
            v = v or and_test
        return v

    def and_test(self):
        not_test = self.not_test()
        v = not_test
        while self._peek('AND', 'OR', 'RPAR', 'COMMA', 'END', 'NOT', 'INV', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') == 'AND':
            AND = self._scan('AND')
            not_test = self.not_test()
            v = v and not_test
        return v

    def not_test(self):
        _token_ = self._peek('NOT', 'INV', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR')
        if _token_ not in ['NOT', 'INV']:
            comparison = self.comparison()
            return comparison
        else:# in ['NOT', 'INV']
            while 1:
                _token_ = self._peek('NOT', 'INV')
                if _token_ == 'NOT':
                    NOT = self._scan('NOT')
                    not_test = self.not_test()
                    v = not not_test
                else:# == 'INV'
                    INV = self._scan('INV')
                    not_test = self.not_test()
                    v = _inv('!', not_test)
                if self._peek('NOT', 'INV', 'AND', 'OR', 'RPAR', 'COMMA', 'END', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') not in ['NOT', 'INV']: break
            return v

    def comparison(self):
        or_expr = self.or_expr()
        v = or_expr
        while self._peek('LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'AND', 'NOT', 'INV', 'OR', 'RPAR', 'COMMA', 'END', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') in ['LT', 'GT', 'LE', 'GE', 'EQ', 'NE']:
            _token_ = self._peek('LT', 'GT', 'LE', 'GE', 'EQ', 'NE')
            if _token_ == 'LT':
                LT = self._scan('LT')
                or_expr = self.or_expr()
                v = v < or_expr
            elif _token_ == 'GT':
                GT = self._scan('GT')
                or_expr = self.or_expr()
                v = v > or_expr
            elif _token_ == 'LE':
                LE = self._scan('LE')
                or_expr = self.or_expr()
                v = v <= or_expr
            elif _token_ == 'GE':
                GE = self._scan('GE')
                or_expr = self.or_expr()
                v = v >= or_expr
            elif _token_ == 'EQ':
                EQ = self._scan('EQ')
                or_expr = self.or_expr()
                v = v == or_expr
            else:# == 'NE'
                NE = self._scan('NE')
                or_expr = self.or_expr()
                v = v != or_expr
        return v

    def or_expr(self):
        and_expr = self.and_expr()
        v = and_expr
        while self._peek('OR', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'AND', 'NOT', 'INV', 'RPAR', 'COMMA', 'END', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') == 'OR':
            OR = self._scan('OR')
            and_expr = self.and_expr()
            v = v or and_expr
        return v

    def and_expr(self):
        a_expr = self.a_expr()
        v = a_expr
        while self._peek('AND', 'OR', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'NOT', 'INV', 'RPAR', 'COMMA', 'END', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') == 'AND':
            AND = self._scan('AND')
            a_expr = self.a_expr()
            v = v and a_expr
        return v

    def a_expr(self):
        m_expr = self.m_expr()
        v = m_expr
        while self._peek('ADD', 'SUB', 'AND', 'OR', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'NOT', 'INV', 'RPAR', 'COMMA', 'END', 'SIGN', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') in ['ADD', 'SUB']:
            _token_ = self._peek('ADD', 'SUB')
            if _token_ == 'ADD':
                ADD = self._scan('ADD')
                m_expr = self.m_expr()
                v = v + m_expr
            else:# == 'SUB'
                SUB = self._scan('SUB')
                m_expr = self.m_expr()
                v = v - m_expr
        return v

    def m_expr(self):
        u_expr = self.u_expr()
        v = u_expr
        while self._peek('MUL', 'DIV', 'ADD', 'SUB', 'AND', 'OR', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'NOT', 'INV', 'RPAR', 'COMMA', 'END', 'SIGN', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') in ['MUL', 'DIV']:
            _token_ = self._peek('MUL', 'DIV')
            if _token_ == 'MUL':
                MUL = self._scan('MUL')
                u_expr = self.u_expr()
                v = v * u_expr
            else:# == 'DIV'
                DIV = self._scan('DIV')
                u_expr = self.u_expr()
                v = v / u_expr
        return v

    def u_expr(self):
        _token_ = self._peek('SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR')
        if _token_ == 'SIGN':
            SIGN = self._scan('SIGN')
            u_expr = self.u_expr()
            return _inv('-', u_expr)
        elif _token_ == 'ADD':
            ADD = self._scan('ADD')
            u_expr = self.u_expr()
            return u_expr
        else:# in ['LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR']
            atom = self.atom()
            v = atom
            if self._peek() == 'UNITS':
                UNITS = self._scan('UNITS')
                v = call(UNITS, [v, UNITS])
            return v

    def atom(self):
        _token_ = self._peek('LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR')
        if _token_ == 'LPAR':
            LPAR = self._scan('LPAR')
            expr = self.expr()
            RPAR = self._scan('RPAR')
            return expr
        elif _token_ == 'ID':
            ID = self._scan('ID')
            v = ID
            if self._peek() == 'LPAR':
                LPAR = self._scan('LPAR')
                expr_lst = self.expr_lst()
                RPAR = self._scan('RPAR')
                return call(v, expr_lst)
            return v
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            return NumberValue(ParserValue(NUM))
        elif _token_ == 'STR':
            STR = self._scan('STR')
            return StringValue(ParserValue(STR))
        elif _token_ == 'QSTR':
            QSTR = self._scan('QSTR')
            return QuotedStringValue(ParserValue(QSTR))
        elif _token_ == 'BOOL':
            BOOL = self._scan('BOOL')
            return BooleanValue(ParserValue(BOOL))
        else:# == 'COLOR'
            COLOR = self._scan('COLOR')
            return ColorValue(ParserValue(COLOR))

    def expr_lst(self):
        expr = self.expr()
        v = [expr]
        while self._peek('COMMA', 'NOT', 'INV', 'RPAR', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') != 'RPAR':
            if self._peek('COMMA', 'NOT', 'INV', 'SIGN', 'ADD', 'LPAR', 'ID', 'NUM', 'STR', 'QSTR', 'BOOL', 'COLOR') == 'COMMA':
                COMMA = self._scan('COMMA')
            expr = self.expr()
            v.append(expr)
        return v
### Grammar ends.

P = Calculator(CalculatorScanner())
def eval_expr(expr):
    #print >>sys.stderr, '>>',expr,'<<'
    val = None
    try:
        P.reset(expr)
        results = P.goal()
        val = results and ' '.join(e for e in results if e != '')
        #print >>sys.stderr, '--',val,'--'
    except SyntaxError:
        pass
        #raise
    except:
        pass
        raise
    return val


__doc__ += """
>>> css = Scss()

VARIABLES
--------------------------------------------------------------------------------
http://xcss.antpaw.org/docs/syntax/variables

>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
... .selector {
...     padding: [(5px - 3) * (5px - 3)];
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.selector {
	padding: 4px;
}


>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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

>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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

Multiple Extends
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
... .bad {
...     color: red !important;
... }
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
...   @extend .bad;
...   border-width: 3px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.bad, .seriousError {
	color: red !important;
}
.error, .seriousError {
	border: 1px red;
	background-color: #fdd;
}
.attention, .seriousError {
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
... body {
...     _width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
body {
	_width: expression(document.body.clientWidth > 1440? "1440px" : "auto");
}


http://groups.google.com/group/xcss/browse_thread/thread/2d27ddec3c15c385#
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
...     adjust: adjust-hue(hsl(120, 30%, 90%), 60deg); // hsl(180, 30%, 90%)
...     adjust: adjust-hue(hsl(120, 30%, 90%), -60deg); // hsl(60, 30%, 90%)
...     adjust: adjust-hue(#811, 45deg); // #886a11
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
    lighten: hsl(0, 0%, 30%);
    lighten: #e00;
    darken: hsl(25, 100%, 50%);
    darken: #210000;
    saturate: hsl(120, 50%, 90%);
    saturate: #9e3e3e;
    desaturate: hsl(120, 10%, 90%);
    desaturate: #716b6b;
    adjust: hsl(180, 30%, 90%);
    adjust: hsl(60, 30%, 90%);
    adjust: #886a10;
    mix: #7f007f;
    mix: #3f00bf;
    mix: rgba(63, 0, 191, 0.75);
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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


>>> css.scss_files = {}
>>> css.scss_files['first.css'] = '''
... @option compress:no, short_colors:yes, reverse_colors:yes;
... .specialClass extends .basicClass {
...     padding: 10px;
...     font-size: 14px;
... }
... '''
>>> css.scss_files['second.css'] = '''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
... a:hover { text-decoration: underline }
... .hoverlink { @extend a:hover }
... ''') #doctest: +NORMALIZE_WHITESPACE
.hoverlink,
a:hover {
	text-decoration: underline;
}


http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
... @option compress:no, short_colors:yes, reverse_colors:yes;
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
        css = Scss()
        sys.stdout.write(css.compile(sys.stdin.read()))
