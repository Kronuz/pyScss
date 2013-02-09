#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
pyScss, a Scss compiler for Python

@author     German M. Bravo (Kronuz) <german.mb@gmail.com>
@version    1.1.4
@see        https://github.com/Kronuz/pyScss
@copyright  (c) 2012 German M. Bravo (Kronuz)
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
from __future__ import absolute_import

from scss.scss_meta import BUILD_INFO, PROJECT, VERSION, REVISION, URL, AUTHOR, AUTHOR_EMAIL, LICENSE

__project__ = PROJECT
__version__ = VERSION
__author__ = AUTHOR + ' <' + AUTHOR_EMAIL + '>'
__license__ = LICENSE


from collections import deque
import glob
import logging
import os.path
import re
import sys
import textwrap
import time

from scss import config
from scss.cssdefs import _colors, _units, _zero_units
import scss.functions
from scss.functions import _sprite_map
from scss.parseutil import _inv
from scss.types import BooleanValue, ColorValue, ListValue, NumberValue, ParserValue, QuotedStringValue, StringValue
from scss.util import depar, dequote, normalize_var, split_params, to_str

log = logging.getLogger(__name__)

################################################################################
# Load C acceleration modules
locate_blocks = None
Scanner = None
try:
    from scss._speedups import locate_blocks, Scanner, NoMoreTokens
except ImportError:
    print >>sys.stderr, "Scanning acceleration disabled (_speedups not found)!"
    from scss._native import locate_blocks, Scanner, NoMoreTokens
    pass

################################################################################

profiling = {}


_safe_strings = {
    '^doubleslash^': '//',
    '^bigcopen^': '/*',
    '^bigcclose^': '*/',
    '^doubledot^': ':',
    '^semicolon^': ';',
    '^curlybracketopen^': '{',
    '^curlybracketclosed^': '}',
}
_reverse_safe_strings = dict((v, k) for k, v in _safe_strings.items())
_safe_strings_re = re.compile('|'.join(map(re.escape, _safe_strings)))
_reverse_safe_strings_re = re.compile('|'.join(map(re.escape, _reverse_safe_strings)))

_default_scss_files = {}  # Files to be compiled ({file: content, ...})

_default_scss_index = {0: '<unknown>:0'}

_default_scss_vars = {
    '$BUILD-INFO': BUILD_INFO,
    '$PROJECT': PROJECT,
    '$VERSION': VERSION,
    '$REVISION': REVISION,
    '$URL': URL,
    '$AUTHOR': AUTHOR,
    '$AUTHOR-EMAIL': AUTHOR_EMAIL,
    '$LICENSE': LICENSE,

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
    'verbosity': config.VERBOSITY,
    'compress': 1,
    'compress_short_colors': 1,  # Converts things like #RRGGBB to #RGB
    'compress_reverse_colors': 1,  # Gets the shortest name of all for colors
    'short_colors': 0,  # Converts things like #RRGGBB to #RGB
    'reverse_colors': 0,  # Gets the shortest name of all for colors
}

SEPARATOR = '\x00'
_nl_re = re.compile(r'[ \t\r\f\v]*\n[ \t\r\f\v]*', re.MULTILINE)
_nl_num_re = re.compile(r'\n.+' + SEPARATOR, re.MULTILINE)
_nl_num_nl_re = re.compile(r'\n.+' + SEPARATOR + r'[ \t\r\f\v]*\n', re.MULTILINE)

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
_reverse_colors_re = re.compile(r'(?<![-\w.#$])(' + '|'.join(map(re.escape, _reverse_colors)) + r')(?![-\w])', re.IGNORECASE)
_colors_re = re.compile(r'(?<![-\w.#$])(' + '|'.join(map(re.escape, _colors)) + r')(?![-\w])', re.IGNORECASE)

_expr_glob_re = re.compile(r'''
    \#\{(.*?)\}                   # Global Interpolation only
''', re.VERBOSE)

# XXX these still need to be fixed; the //-in-functions thing is a chumpy hack
_ml_comment_re = re.compile(r'\/\*(.*?)\*\/', re.DOTALL)
_sl_comment_re = re.compile(r'(?<![(])(?<!\w{2}:)\/\/.*')
_zero_units_re = re.compile(r'\b(?<![.])0(' + '|'.join(map(re.escape, _zero_units)) + r')(?!\w)', re.IGNORECASE)
_zero_re = re.compile(r'\b0\.(?=\d)')

_escape_chars_re = re.compile(r'([^-a-zA-Z0-9_])')
_variable_re = re.compile('^\\$[-a-zA-Z0-9_]+$')
_interpolate_re = re.compile(r'(#\{\s*)?(\$[-\w]+)(?(1)\s*\})')
_spaces_re = re.compile(r'\s+')
_expand_rules_space_re = re.compile(r'\s*{')
_collapse_properties_space_re = re.compile(r'([:#])\s*{')
_undefined_re = re.compile('^(?:\\$[-a-zA-Z0-9_]+|undefined)$')

_strings_re = re.compile(r'([\'"]).*?\1')
_blocks_re = re.compile(r'[{},;()\'"\n]')

_prop_split_re = re.compile(r'[:=]')
_skip_word_re = re.compile(r'-?[_\w\s#.,:%]*$|[-_\w#.,:%]*$', re.MULTILINE)
_has_code_re = re.compile('''
    (?:^|(?<=[{;}]))            # the character just before it should be a '{', a ';' or a '}'
    \s*                         # ...followed by any number of spaces
    (?:
        (?:
            \+
        |
            @include
        |
            @warn
        |
            @mixin
        |
            @function
        |
            @if
        |
            @else
        |
            @for
        |
            @each
        )
        (?![^(:;}]*['"])
    |
        @import
    )
''', re.VERBOSE)

FUNCTIONS_CSS2 = 'attr counter counters url rgb rect'
## CSS3
FUNCTIONS_UNITS = 'calc min max cycle'  # http://www.w3.org/TR/css3-values/
FUNCTIONS_COLORS = 'rgba hsl hsla'  # http://www.w3.org/TR/css3-color/
FUNCTIONS_FONTS = 'local format'  # http://www.w3.org/TR/css3-fonts/
# http://www.w3.org/TR/css3-images
FUNCTIONS_IMAGES = 'image element linear-gradient radial-gradient '\
                   'repeating-linear-gradient repeating-radial-gradient'
# http://www.w3.org/TR/css3-2d-transforms/
FUNCTIONS_2D = 'matrix translate translateX translateY scale '\
               'scale scaleX scaleY rotate skew skewX skewY'
# http://www.w3.org/TR/css3-3d-transforms/
FUNCTIONS_3D = 'matrix3d translate3d translateZ scale3d scaleZ rotate3d '\
               'rotateX rotateY rotateZ perspective'
# http://www.w3.org/TR/css3-transitions/
FUNCTIONS_TRANSITIONS = 'cubic-bezier'
# http://www.w3.org/TR/css3-animations/
FUNCTIONS_ANIMATIONS = ''  # has 'from' and 'to' block selectors, but no new function
FUNCTIONS_FILTER = 'grayscale blur sepia saturate opacity brightness contrast hue-rotate invert'
FUNCTIONS_OTHERS = 'from to mask'
VENDORS = '-[^-]+-.+'

_css_functions_re = re.compile(r'^(%s)$' % (
    '|'.join(' '.join([
        FUNCTIONS_CSS2,
        FUNCTIONS_UNITS,
        FUNCTIONS_COLORS,
        FUNCTIONS_FONTS,
        FUNCTIONS_IMAGES,
        FUNCTIONS_2D,
        FUNCTIONS_3D,
        FUNCTIONS_TRANSITIONS,
        FUNCTIONS_ANIMATIONS,
        FUNCTIONS_FILTER,
        FUNCTIONS_OTHERS,
        VENDORS,
    ]).split())))

FILEID = 0
POSITION = 1
CODESTR = 2
DEPS = 3
CONTEXT = 4
OPTIONS = 5
SELECTORS = 6
PROPERTIES = 7
PATH = 8
INDEX = 9
LINENO = 10
FINAL = 11
MEDIA = 12
RULE_VARS = {
    'FILEID': FILEID,
    'POSITION': POSITION,
    'CODESTR': CODESTR,
    'DEPS': DEPS,
    'CONTEXT': CONTEXT,
    'OPTIONS': OPTIONS,
    'SELECTORS': SELECTORS,
    'PROPERTIES': PROPERTIES,
    'PATH': PATH,
    'INDEX': INDEX,
    'LINENO': LINENO,
    'FINAL': FINAL,
    'MEDIA': MEDIA,
}


def spawn_rule(rule=None, **kwargs):
    if rule is None:
        rule = [None] * len(RULE_VARS)
        rule[DEPS] = set()
        rule[SELECTORS] = ''
        rule[PROPERTIES] = []
        rule[PATH] = './'
        rule[INDEX] = {0: '<unknown>'}
        rule[LINENO] = 0
        rule[FINAL] = False
    else:
        rule = list(rule)
    for k, v in kwargs.items():
        rule[RULE_VARS[k.upper()]] = v
    return rule


def print_timing(level=0):
    def _print_timing(func):
        if config.VERBOSITY:
            def wrapper(*args, **kwargs):
                if config.VERBOSITY >= level:
                    t1 = time.time()
                    res = func(*args, **kwargs)
                    t2 = time.time()
                    profiling.setdefault(func.func_name, 0)
                    profiling[func.func_name] += (t2 - t1)
                    return res
                else:
                    return func(*args, **kwargs)
            return wrapper
        else:
            return func
    return _print_timing


# Profiler decorator
# import pstats
# import cProfile
# def profile(fn):
#     def wrapper(*args, **kwargs):
#         profiler = cProfile.Profile()
#         stream = StringIO()
#         profiler.enable()
#         try:
#             res = fn(*args, **kwargs)
#         finally:
#             profiler.disable()
#             stats = pstats.Stats(profiler, stream=stream)
#             stats.sort_stats('time')
#             print >>stream, ""
#             print >>stream, "=" * 100
#             print >>stream, "Stats:"
#             stats.print_stats()
#             print >>stream, "=" * 100
#             print >>stream, "Callers:"
#             stats.print_callers()
#             print >>stream, "=" * 100
#             print >>stream, "Callees:"
#             stats.print_callees()
#             print >>sys.stderr, stream.getvalue()
#             stream.close()
#         return res
#     return wrapper


################################################################################


class Scss(object):
    # configuration:
    construct = 'self'

    def __init__(self, scss_vars=None, scss_opts=None, scss_files=None, super_selector=None, func_registry=scss.functions.scss_builtins, search_paths=None):
        if super_selector:
            self.super_selector = super_selector + ' '
        else:
            self.super_selector = ''
        self._scss_vars = scss_vars
        self._scss_opts = scss_opts or {}
        self._scss_files = scss_files
        self._func_registry = func_registry

        # Figure out search paths.  Fall back from provided explicitly to
        # defined globally to just searching the current directory
        if search_paths is not None:
            assert not isinstance(search_paths, basestring), \
                "`search_paths` should be an iterable, not a string"
            self._search_paths = search_paths
        else:
            self._search_paths = ["."]

            if config.LOAD_PATHS:
                if isinstance(config.LOAD_PATHS, basestring):
                    # Back-compat: allow comma-delimited
                    self._search_paths.extend(config.LOAD_PATHS.split(','))
                else:
                    self._search_paths.extend(config.LOAD_PATHS)

            self._search_paths.extend(self._scss_opts.get('load_paths', []))

        self.reset()

    def get_scss_constants(self):
        scss_vars = self.scss_vars or {}
        return dict((k, v) for k, v in scss_vars.items() if k and (not k.startswith('$') or k.startswith('$') and k[1].isupper()))

    def get_scss_vars(self):
        scss_vars = self.scss_vars or {}
        return dict((k, v) for k, v in scss_vars.items() if k and not (not k.startswith('$') or k.startswith('$') and k[1].isupper()))

    def clean(self):
        self.children = deque()
        self.rules = []
        self._rules = {}
        self.parts = {}

    def reset(self, input_scss=None):
        if hasattr(CalculatorScanner, 'cleanup'):
            CalculatorScanner.cleanup()

        # Initialize
        self.css_files = []

        self.scss_vars = _default_scss_vars.copy()
        if self._scss_vars is not None:
            self.scss_vars.update(self._scss_vars)

        self.scss_opts = _default_scss_opts.copy()
        if self._scss_opts is not None:
            self.scss_opts.update(self._scss_opts)

        self.scss_files = {}
        self._scss_files_order = []
        for f, c in _default_scss_files.iteritems():
            if f not in self.scss_files:
                self._scss_files_order.append(f)
            self.scss_files[f] = c
        if self._scss_files is not None:
            for f, c in self._scss_files.iteritems():
                if f not in self.scss_files:
                    self._scss_files_order.append(f)
                self.scss_files[f] = c

        self._scss_index = _default_scss_index.copy()

        self._contexts = {}

        self.clean()

    #@profile
    #@print_timing(2)
    def Compilation(self, scss_string=None, scss_file=None, super_selector=None, filename=None):
        if super_selector:
            self.super_selector = super_selector + ' '
        if scss_string is not None:
            self._scss_files = {filename or '<string %r>' % (scss_string.strip()[:50] + '...'): scss_string}
        elif scss_file is not None:
            self._scss_files = {filename or scss_file: open(scss_file).read()}

        self.reset()

        # Compile
        for fileid in self._scss_files_order:
            codestr = self.scss_files[fileid]
            codestr = self.load_string(codestr, fileid)
            self.scss_files[fileid] = codestr
            rule = spawn_rule(fileid=fileid, codestr=codestr, context=self.scss_vars, options=self.scss_opts, index=self._scss_index)
            self.children.append(rule)

        # this will manage rule: child objects inside of a node
        self.parse_children()

        # this will manage rule: ' extends '
        self.parse_extends()

        # this will manage the order of the rules
        self.manage_order()

        self.parse_properties()

        all_rules = 0
        all_selectors = 0
        exceeded = ''
        final_cont = ''
        for fileid in self.css_files:
            fcont, total_rules, total_selectors = self.create_css(fileid)
            all_rules += total_rules
            all_selectors += total_selectors
            if not exceeded and all_selectors > 4095:
                exceeded = " (IE exceeded!)"
                log.error("Maximum number of supported selectors in Internet Explorer (4095) exceeded!")
            if self.scss_opts.get('debug_info', False):
                if fileid.startswith('<string '):
                    final_cont += "/* %s, add to %s%s selectors generated */\n" % (total_selectors, all_selectors, exceeded)
                else:
                    final_cont += "/* %s, add to %s%s selectors generated from '%s' */\n" % (total_selectors, all_selectors, exceeded, fileid)
            final_cont += fcont

        final_cont = self.post_process(final_cont)

        return final_cont
    compile = Compilation

    def load_string(self, codestr, filename=None):
        if filename is not None:
            codestr += '\n'

            idx = {
                'next_id': len(self._scss_index),
                'line': 1,
            }

            def _cnt(m):
                idx['line'] += 1
                lineno = '%s:%d' % (filename, idx['line'])
                next_id = idx['next_id']
                self._scss_index[next_id] = lineno
                idx['next_id'] += 1
                return '\n' + str(next_id) + SEPARATOR
            lineno = '%s:%d' % (filename, idx['line'])
            next_id = idx['next_id']
            self._scss_index[next_id] = lineno
            codestr = str(next_id) + SEPARATOR + _nl_re.sub(_cnt, codestr)

        # remove empty lines
        codestr = _nl_num_nl_re.sub('\n', codestr)

        # protects codestr: "..." strings
        codestr = _strings_re.sub(lambda m: _reverse_safe_strings_re.sub(lambda n: _reverse_safe_strings[n.group(0)], m.group(0)), codestr)

        # removes multiple line comments
        codestr = _ml_comment_re.sub('', codestr)

        # removes inline comments, but not :// (protocol)
        codestr = _sl_comment_re.sub('', codestr)

        codestr = _safe_strings_re.sub(lambda m: _safe_strings[m.group(0)], codestr)

        # expand the space in rules
        codestr = _expand_rules_space_re.sub(' {', codestr)

        # collapse the space in properties blocks
        codestr = _collapse_properties_space_re.sub(r'\1{', codestr)

        # to do math operations, we need to get the color's hex values (for color names):
        def _pp(m):
            v = m.group(0)
            return _colors.get(v, v)
        codestr = _colors_re.sub(_pp, codestr)

        return codestr

    def longest_common_prefix(self, seq1, seq2):
        start = 0
        common = 0
        length = min(len(seq1), len(seq2))
        while start < length:
            if seq1[start] != seq2[start]:
                break
            if seq1[start] == ' ':
                common = start + 1
            elif seq1[start] in ('#', ':', '.'):
                common = start
            start += 1
        return common

    def longest_common_suffix(self, seq1, seq2):
        seq1, seq2 = seq1[::-1], seq2[::-1]
        start = 0
        common = 0
        length = min(len(seq1), len(seq2))
        while start < length:
            if seq1[start] != seq2[start]:
                break
            if seq1[start] == ' ':
                common = start + 1
            elif seq1[start] in ('#', ':', '.'):
                common = start + 1
            start += 1
        return common

    def normalize_selectors(self, _selectors, extra_selectors=None):
        """
        Normalizes or extends selectors in a string.
        An optional extra parameter that can be a list of extra selectors to be
        added to the final normalized selectors string.
        """
        # Fixe tabs and spaces in selectors
        _selectors = _spaces_re.sub(' ', _selectors)

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

        parents.discard('')
        if parents:
            return ','.join(sorted(selectors)) + ' extends ' + '&'.join(sorted(parents))
        return ','.join(sorted(selectors))

    def apply_vars(self, cont, context, options=None, rule=None, _dequote=False):
        if isinstance(cont, basestring) and '$' in cont:
            if cont in context:
                # Optimization: the full cont is a variable in the context,
                # flatten the interpolation and use it:
                while isinstance(cont, basestring) and cont in context:
                    _cont = context[cont]
                    if _cont == cont:
                        break
                    cont = _cont
            else:
                # Flatten the context (no variables mapping to variables)
                flat_context = {}
                for k, v in context.items():
                    while isinstance(v, basestring) and v in context:
                        _v = context[v]
                        if _v == v:
                            break
                        v = _v
                    flat_context[k] = v

                # Interpolate variables:
                def _av(m):
                    v = flat_context.get(normalize_var(m.group(2)))
                    if v:
                        v = to_str(v)
                        if _dequote and m.group(1):
                            v = dequote(v)
                    elif v is not None:
                        v = to_str(v)
                    else:
                        v = m.group(0)
                    return v

                cont = _interpolate_re.sub(_av, cont)
        if options is not None:
            # ...apply math:
            cont = self.do_glob_math(cont, context, options, rule, _dequote)
        return cont

    @print_timing(3)
    def parse_children(self):
        pos = 0
        while self.children:
            rule = self.children.popleft()

            # Check if the block has nested blocks and work it out:
            _selectors, _, _parents = rule[SELECTORS].partition(' extends ')
            _selectors = _selectors.split(',')
            _parents = set(_parents.split('&'))
            _parents.discard('')

            # manage children or expand children:
            _children = deque()
            self.manage_children(rule, _selectors, _parents, _children, None, rule[MEDIA])
            self.children.extendleft(_children)

            # prepare maps:
            if _parents:
                rule[SELECTORS] = ','.join(_selectors) + ' extends ' + '&'.join(_parents)
            rule[POSITION] = pos
            selectors = rule[SELECTORS]
            self.parts.setdefault(selectors, [])
            self.parts[selectors].append(rule)
            self.rules.append(rule)
            pos += 1

            #print >>sys.stderr, '='*80
            #for r in [rule]+list(self.children)[:5]: print >>sys.stderr, repr(r[POSITION]), repr(r[SELECTORS]), repr(r[CODESTR][:80]+('...' if len(r[CODESTR])>80 else ''))
            #for r in [rule]+list(self.children)[:5]: print >>sys.stderr, repr(r[POSITION]), repr(r[SELECTORS]), repr(r[CODESTR][:80]+('...' if len(r[CODESTR])>80 else '')), dict((k, v) for k, v in r[CONTEXT].items() if k.startswith('$') and not k.startswith('$__')), dict(r[PROPERTIES]).keys()

    @print_timing(4)
    def manage_children(self, rule, p_selectors, p_parents, p_children, scope, media):
        for c_lineno, c_property, c_codestr in locate_blocks(rule[CODESTR]):
            if '@return' in rule[OPTIONS]:
                return
            # Rules preprocessing...
            if c_property.startswith('+'):  # expands a '+' at the beginning of a rule as @include
                c_property = '@include ' + c_property[1:]
                try:
                    if '(' not in c_property or c_property.index(':') < c_property.index('('):
                        c_property = c_property.replace(':', '(', 1)
                        if '(' in c_property:
                            c_property += ')'
                except ValueError:
                    pass
            elif c_property.startswith('='):  # expands a '=' at the beginning of a rule as @mixin
                c_property = '@mixin' + c_property[1:]
            elif c_property == '@prototype ':  # Remove '@prototype '
                c_property = c_property[11:]
            ####################################################################
            if c_property.startswith('@'):
                code, name = (c_property.split(None, 1) + [''])[:2]
                code = code.lower()
                if code == '@warn':
                    name = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
                    log.warn(dequote(to_str(name)))
                elif code == '@print':
                    name = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
                    print >>sys.stderr, dequote(to_str(name))
                elif code == '@raw':
                    name = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
                    print >>sys.stderr, repr(name)
                elif code == '@dump_context':
                    log.info(repr(rule[CONTEXT]))
                elif code == '@dump_options':
                    log.info(repr(rule[OPTIONS]))
                elif code == '@debug':
                    name = name.strip()
                    if name.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
                        name = 1
                    elif name.lower() in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
                        name = 0
                    config.DEBUG = name
                    log.info("Debug mode is %s", 'On' if config.DEBUG else 'Off')
                elif code == '@option':
                    self._settle_options(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@content':
                    self._do_content(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@import':
                    self._do_import(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@extend':
                    name = self.apply_vars(name, rule[CONTEXT], rule[OPTIONS], rule)
                    p_parents.update(p.strip() for p in name.replace(',', '&').split('&'))
                    p_parents.discard('')
                elif code == '@return':
                    ret = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
                    rule[OPTIONS]['@return'] = ret
                elif code == '@include':
                    self._do_include(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif c_codestr is None:
                    rule[PROPERTIES].append((c_lineno, c_property, None))
                elif code in ('@mixin', '@function'):
                    self._do_functions(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@if' or c_property.startswith('@else if '):
                    self._do_if(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@else':
                    self._do_else(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@for':
                    self._do_for(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code == '@each':
                    self._do_each(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                # elif code == '@while':
                #     self._do_while(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                elif code in ('@variables', '@vars'):
                    self._get_variables(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr)
                elif code == '@media':
                    _media = (media or []) + [name]
                    rule[CODESTR] = self.construct + ' {' + c_codestr + '}'
                    self.manage_children(rule, p_selectors, p_parents, p_children, scope, _media)
                elif scope is None:  # needs to have no scope to crawl down the nested rules
                    self._nest_rules(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr)
            ####################################################################
            # Properties
            elif c_codestr is None:
                self._get_properties(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr)
            # Nested properties
            elif c_property.endswith(':'):
                rule[CODESTR] = c_codestr
                self.manage_children(rule, p_selectors, p_parents, p_children, (scope or '') + c_property[:-1] + '-', media)
            ####################################################################
            # Nested rules
            elif scope is None:  # needs to have no scope to crawl down the nested rules
                self._nest_rules(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr)

    @print_timing(10)
    def _settle_options(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        for option in name.split(','):
            option, value = (option.split(':', 1) + [''])[:2]
            option = option.strip().lower()
            value = value.strip()
            if option:
                if value.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
                    value = 1
                elif value.lower() in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
                    value = 0
                rule[OPTIONS][option] = value

    @print_timing(10)
    def _do_functions(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @mixin and @function
        """
        if not name:
            return

        funct, params, _ = name.partition('(')
        funct = normalize_var(funct.strip())
        params = split_params(depar(params + _))
        defaults = {}
        new_params = []
        for param in params:
            param, _, default = param.partition(':')
            param = normalize_var(param.strip())
            default = default.strip()
            if param:
                new_params.append(param)
                if default:
                    default = self.apply_vars(default, rule[CONTEXT], None, rule)
                    defaults[param] = default
        context = rule[CONTEXT].copy()
        for p in new_params:
            context.pop(p, None)
        mixin = [list(new_params), defaults, self.apply_vars(c_codestr, context, None, rule)]
        if code == '@function':
            def _call(mixin):
                def __call(R, *args, **kwargs):
                    m_params = mixin[0]
                    m_vars = rule[CONTEXT].copy()
                    m_vars.update(mixin[1])
                    m_codestr = mixin[2]
                    for i, a in enumerate(args):
                        m_vars[m_params[i]] = a
                    for k, v in kwargs.items():
                        m_vars['$' + normalize_var(k)] = v
                    _options = rule[OPTIONS].copy()
                    _rule = spawn_rule(R, codestr=m_codestr, context=m_vars, options=_options, deps=set(), properties=[], final=False, lineno=c_lineno)
                    self.manage_children(_rule, p_selectors, p_parents, p_children, (scope or '') + '', R[MEDIA])
                    ret = _rule[OPTIONS].pop('@return', '')
                    return ret
                return __call
            _mixin = _call(mixin)
            _mixin.mixin = mixin
            mixin = _mixin
        # Insert as many @mixin options as the default parameters:
        while len(new_params):
            rule[OPTIONS]['%s %s:%d' % (code, funct, len(new_params))] = mixin
            param = new_params.pop()
            if param not in defaults:
                break
        if not new_params:
            rule[OPTIONS][code + ' ' + funct + ':0'] = mixin

    @print_timing(10)
    def _do_include(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @include, for @mixins
        """
        funct, params, _ = name.partition('(')
        funct = normalize_var(funct.strip())
        funct = self.do_glob_math(funct, rule[CONTEXT], rule[OPTIONS], rule, True)
        params = split_params(depar(params + _))
        new_params = {}
        num_args = 0
        for param in params:
            varname, _, param = param.partition(':')
            if param:
                param = param.strip()
                varname = varname.strip()
            else:
                param = varname.strip()
                varname = num_args
                if param:
                    num_args += 1
            if param:
                new_params[varname] = param
        mixin = rule[OPTIONS].get('@mixin %s:%s' % (funct, num_args))
        if not mixin:
            # Fallback to single parmeter:
            mixin = rule[OPTIONS].get('@mixin %s:1' % (funct,))
            if mixin and all(map(lambda o: isinstance(o, int), new_params.keys())):
                new_params = {0: ', '.join(new_params.values())}
        if not mixin:
            log.error("Required mixin not found: %s:%d (%s)", funct, num_args, rule[INDEX][rule[LINENO]], extra={'stack': True})
            return

        m_params = mixin[0]
        m_vars = mixin[1].copy()
        m_codestr = mixin[2]
        for varname, value in new_params.items():
            try:
                m_param = m_params[varname]
            except (IndexError, KeyError, TypeError):
                m_param = varname
            value = self.calculate(value, rule[CONTEXT], rule[OPTIONS], rule)
            m_vars[m_param] = value
        for p in m_params:
            if p not in new_params and isinstance(m_vars[p], basestring):
                value = self.calculate(m_vars[p], m_vars, rule[OPTIONS], rule)
                m_vars[p] = value
        _context = rule[CONTEXT].copy()
        _context.update(m_vars)
        _rule = spawn_rule(rule, codestr=m_codestr, context=_context, lineno=c_lineno)
        _rule[OPTIONS]['@content'] = c_codestr
        self.manage_children(_rule, p_selectors, p_parents, p_children, scope, media)

    @print_timing(10)
    def _do_content(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @content
        """
        if '@content' not in rule[OPTIONS]:
            log.error("Content string not found for @content (%s)", rule[INDEX][rule[LINENO]])
        c_codestr = rule[OPTIONS].pop('@content', '')
        rule[CODESTR] = c_codestr
        self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)

    @print_timing(10)
    def _do_import(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @import
        Load and import mixins and functions and rules
        """
        # Protect against going to prohibited places...
        if '..' in name or '://' in name or 'url(' in name:
            rule[PROPERTIES].append((c_lineno, c_property, None))
            return

        full_filename = None
        i_codestr = None
        names = name.split(',')
        for name in names:
            name = dequote(name.strip())
            if '@import ' + name in rule[OPTIONS]:
                # If already imported in this scope, skip
                continue

            unsupported = []
            load_paths = []
            filename = os.path.basename(name)
            dirname = os.path.dirname(name)

            try:
                i_codestr = self.scss_files[name]
            except KeyError:
                i_codestr = None

                for path in self._search_paths:
                    for basepath in ['./', os.path.dirname(rule[PATH])]:
                        i_codestr = None
                        full_path = os.path.realpath(os.path.join(path, basepath, dirname))
                        if full_path in load_paths:
                            continue
                        try:
                            full_filename = os.path.join(full_path, '_' + filename)
                            i_codestr = open(full_filename + '.scss').read()
                            full_filename += '.scss'
                        except IOError:
                            if os.path.exists(full_filename + '.sass'):
                                unsupported.append(full_filename + '.sass')
                            try:
                                full_filename = os.path.join(full_path, filename)
                                i_codestr = open(full_filename + '.scss').read()
                                full_filename += '.scss'
                            except IOError:
                                if os.path.exists(full_filename + '.sass'):
                                    unsupported.append(full_filename + '.sass')
                                try:
                                    full_filename = os.path.join(full_path, '_' + filename)
                                    i_codestr = open(full_filename).read()
                                except IOError:
                                    try:
                                        full_filename = os.path.join(full_path, filename)
                                        i_codestr = open(full_filename).read()
                                    except IOError:
                                        pass
                        if i_codestr is not None:
                            break
                        else:
                            load_paths.append(full_path)
                    if i_codestr is not None:
                        break
                if i_codestr is None:
                    i_codestr = self._do_magic_import(rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name)
                i_codestr = self.scss_files[name] = i_codestr and self.load_string(i_codestr, full_filename)
                if name not in self.scss_files:
                    self._scss_files_order.append(name)
            if i_codestr is None:
                load_paths = load_paths and "\nLoad paths:\n\t%s" % "\n\t".join(load_paths) or ''
                unsupported = unsupported and "\nPossible matches (for unsupported file format SASS):\n\t%s" % "\n\t".join(unsupported) or ''
                log.warn("File to import not found or unreadable: '%s' (%s)%s%s", filename, rule[INDEX][rule[LINENO]], load_paths, unsupported)
            else:
                _rule = spawn_rule(rule, codestr=i_codestr, path=full_filename, lineno=c_lineno)
                self.manage_children(_rule, p_selectors, p_parents, p_children, scope, media)
                rule[OPTIONS]['@import ' + name] = True

    @print_timing(10)
    def _do_magic_import(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @import for sprite-maps
        Imports magic sprite map directories
        """
        if callable(config.STATIC_ROOT):
            files = sorted(config.STATIC_ROOT(name))
        else:
            glob_path = os.path.join(config.STATIC_ROOT, name)
            files = glob.glob(glob_path)
            files = sorted((file[len(config.STATIC_ROOT):], None) for file in files)

        if not files:
            return

        # Build magic context
        map_name = os.path.normpath(os.path.dirname(name)).replace('\\', '_').replace('/', '_')
        kwargs = {}

        def setdefault(var, val):
            _var = '$' + map_name + '-' + var
            if _var in rule[CONTEXT]:
                kwargs[var] = interpolate(rule[CONTEXT][_var], rule, self._func_registry)
            else:
                rule[CONTEXT][_var] = val
                kwargs[var] = interpolate(val, rule, self._func_registry)
            return rule[CONTEXT][_var]

        setdefault('sprite-base-class', StringValue('.' + map_name + '-sprite'))
        setdefault('sprite-dimensions', BooleanValue(False))
        position = setdefault('position', NumberValue(0, '%'))
        spacing = setdefault('spacing', NumberValue(0))
        repeat = setdefault('repeat', StringValue('no-repeat'))
        names = tuple(os.path.splitext(os.path.basename(file))[0] for file, storage in files)
        for n in names:
            setdefault(n + '-position', position)
            setdefault(n + '-spacing', spacing)
            setdefault(n + '-repeat', repeat)
        sprite_map = _sprite_map(name, **kwargs)
        rule[CONTEXT]['$' + map_name + '-' + 'sprites'] = sprite_map
        ret = '''
            @import "compass/utilities/sprites/base";

            // All sprites should extend this class
            // The %(map_name)s-sprite mixin will do so for you.
            #{$%(map_name)s-sprite-base-class} {
                background: $%(map_name)s-sprites;
            }

            // Use this to set the dimensions of an element
            // based on the size of the original image.
            @mixin %(map_name)s-sprite-dimensions($name) {
                @include sprite-dimensions($%(map_name)s-sprites, $name);
            }

            // Move the background position to display the sprite.
            @mixin %(map_name)s-sprite-position($name, $offset-x: 0, $offset-y: 0) {
                @include sprite-position($%(map_name)s-sprites, $name, $offset-x, $offset-y);
            }

            // Extends the sprite base class and set the background position for the desired sprite.
            // It will also apply the image dimensions if $dimensions is true.
            @mixin %(map_name)s-sprite($name, $dimensions: $%(map_name)s-sprite-dimensions, $offset-x: 0, $offset-y: 0) {
                @extend #{$%(map_name)s-sprite-base-class};
                @include sprite($%(map_name)s-sprites, $name, $dimensions, $offset-x, $offset-y);
            }

            @mixin %(map_name)s-sprites($sprite-names, $dimensions: $%(map_name)s-sprite-dimensions) {
                @include sprites($%(map_name)s-sprites, $sprite-names, $%(map_name)s-sprite-base-class, $dimensions);
            }

            // Generates a class for each sprited image.
            @mixin all-%(map_name)s-sprites($dimensions: $%(map_name)s-sprite-dimensions) {
                @include %(map_name)s-sprites(%(sprites)s, $dimensions);
            }
        ''' % {'map_name': map_name, 'sprites': ' '.join(names)}
        return ret

    @print_timing(10)
    def _do_if(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @if and @else if
        """
        if code != '@if':
            if '@if' not in rule[OPTIONS]:
                log.error("@else with no @if (%s)", rule[INDEX][rule[LINENO]])
            val = not rule[OPTIONS].get('@if', True)
            name = c_property[9:].strip()
        else:
            val = True
        if val:
            val = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
            val = bool(False if not val or isinstance(val, basestring) and (val in ('0', 'false', 'undefined') or _variable_re.match(val)) else val)
            if val:
                rule[CODESTR] = c_codestr
                self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)
            rule[OPTIONS]['@if'] = val

    @print_timing(10)
    def _do_else(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @else
        """
        if '@if' not in rule[OPTIONS]:
            log.error("@else with no @if (%s)", rule[INDEX][rule[LINENO]])
        val = rule[OPTIONS].pop('@if', True)
        if not val:
            rule[CODESTR] = c_codestr
            self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)

    @print_timing(10)
    def _do_for(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @for
        """
        var, _, name = name.partition(' from ')
        frm, _, through = name.partition(' through ')
        if not through:
            frm, _, through = frm.partition(' to ')
        frm = self.calculate(frm, rule[CONTEXT], rule[OPTIONS], rule)
        through = self.calculate(through, rule[CONTEXT], rule[OPTIONS], rule)
        try:
            frm = int(float(frm))
            through = int(float(through))
        except ValueError:
            return
        except Exception:
            raise

        if frm > through:
            frm, through = through, frm
            rev = reversed
        else:
            rev = lambda x: x
        var = var.strip()
        var = self.do_glob_math(var, rule[CONTEXT], rule[OPTIONS], rule, True)

        for i in rev(range(frm, through + 1)):
            rule[CODESTR] = c_codestr
            rule[CONTEXT][var] = str(i)
            self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)

    @print_timing(10)
    def _do_each(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
        """
        Implements @each
        """
        var, _, name = name.partition(' in ')
        name = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
        if not name:
            return

        name = ListValue(name)
        var = var.strip()
        var = self.do_glob_math(var, rule[CONTEXT], rule[OPTIONS], rule, True)

        for n, v in name.items():
            v = to_str(v)
            rule[CODESTR] = c_codestr
            rule[CONTEXT][var] = v
            if not isinstance(n, int):
                rule[CONTEXT][n] = v
            self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)

    # @print_timing(10)
    # def _do_while(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr, code, name):
    #     THIS DOES NOT WORK AS MODIFICATION OF INNER VARIABLES ARE NOT KNOWN AT THIS POINT!!
    #     """
    #     Implements @while
    #     """
    #     first_val = None
    #     while True:
    #         val = self.calculate(name, rule[CONTEXT], rule[OPTIONS], rule)
    #         val = bool(False if not val or isinstance(val, basestring) and (val in ('0', 'false', 'undefined') or _variable_re.match(val)) else val)
    #         if first_val is None:
    #             first_val = val
    #         if not val:
    #             break
    #         rule[CODESTR] = c_codestr
    #         self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)
    #     rule[OPTIONS]['@if'] = first_val

    @print_timing(10)
    def _get_variables(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr):
        """
        Implements @variables and @vars
        """
        _rule = list(rule)
        _rule[CODESTR] = c_codestr
        _rule[PROPERTIES] = rule[CONTEXT]
        self.manage_children(_rule, p_selectors, p_parents, p_children, scope, media)

    @print_timing(10)
    def _get_properties(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr):
        """
        Implements properties and variables extraction and assignment
        """
        prop, value = (_prop_split_re.split(c_property, 1) + [None])[:2]
        try:
            is_var = (c_property[len(prop)] == '=')
        except IndexError:
            is_var = False
        prop = prop.strip()
        prop = self.do_glob_math(prop, rule[CONTEXT], rule[OPTIONS], rule, True)
        if not prop:
            return

        if value:
            value = value.strip()
            value = self.calculate(value, rule[CONTEXT], rule[OPTIONS], rule)
        _prop = (scope or '') + prop
        if is_var or prop.startswith('$') and value is not None:
            _prop = normalize_var(_prop)
            in_context = rule[CONTEXT].get(_prop)
            is_defined = not (in_context is None or isinstance(in_context, basestring) and _undefined_re.match(in_context))
            if isinstance(value, basestring):
                if '!default' in value:
                    if is_defined:
                        value = None
                    if value is not None:
                        value = value.replace('!default', '').replace('  ', ' ').strip()
                if value is not None and prop.startswith('$') and prop[1].isupper():
                    if is_defined:
                        log.warn("Constant %r redefined", prop)
            elif isinstance(value, ListValue):
                value = ListValue(value)
                for k, v in value.value.items():
                    if v == '!default':
                        if is_defined:
                            value = None
                        if value is not None:
                            del value.value[k]
                            value = value.first() if len(value) == 1 else value
                        break
            if value is not None:
                rule[CONTEXT][_prop] = value
        else:
            _prop = self.apply_vars(_prop, rule[CONTEXT], rule[OPTIONS], rule, True)
            rule[PROPERTIES].append((c_lineno, _prop, to_str(value) if value is not None else None))

    @print_timing(10)
    def _nest_rules(self, rule, p_selectors, p_parents, p_children, scope, media, c_lineno, c_property, c_codestr):
        """
        Implements Nested CSS rules
        """
        if c_property == self.construct and rule[MEDIA] == media:
            rule[CODESTR] = c_codestr
            self.manage_children(rule, p_selectors, p_parents, p_children, scope, media)
            return

        c_property = self.apply_vars(c_property, rule[CONTEXT], rule[OPTIONS], rule, True)

        c_selectors = self.normalize_selectors(c_property)
        c_selectors, _, c_parents = c_selectors.partition(' extends ')

        better_selectors = set()
        c_selectors = c_selectors.split(',')
        for c_selector in c_selectors:
            for p_selector in p_selectors:
                if c_selector == self.construct:
                    better_selectors.add(p_selector)
                elif '&' in c_selector:  # Parent References
                    better_selectors.add(c_selector.replace('&', p_selector))
                elif p_selector:
                    better_selectors.add(p_selector + ' ' + c_selector)
                else:
                    better_selectors.add(c_selector)
        better_selectors = ','.join(sorted(better_selectors))

        if c_parents:
            parents = set(p.strip() for p in c_parents.split('&'))
            parents.discard('')
            if parents:
                better_selectors += ' extends ' + '&'.join(sorted(parents))

        _rule = spawn_rule(rule, codestr=c_codestr, deps=set(), context=rule[CONTEXT].copy(), options=rule[OPTIONS].copy(), selectors=better_selectors, properties=[], final=False, media=media, lineno=c_lineno)

        p_children.appendleft(_rule)

    @print_timing(4)
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
                if parent not in p_selector:
                    continue

                # get the new child selector to add (same as the parent selector but with the child name)
                # since selectors can be together, separated with # or . (i.e. something.parent) check that too:
                for c_selector in c_selectors.split(','):
                    # Get whatever is different between the two selectors:
                    _c_selector, _parent = c_selector, parent
                    lcp = self.longest_common_prefix(_c_selector, _parent)
                    if lcp:
                        _c_selector = _c_selector[lcp:]
                        _parent = _parent[lcp:]
                    lcs = self.longest_common_suffix(_c_selector, _parent)
                    if lcs:
                        _c_selector = _c_selector[:-lcs]
                        _parent = _parent[:-lcs]
                    if _c_selector and _parent:
                        # Get the new selectors:
                        prev_symbol = '(?<![%#.:])' if _parent[0] in ('%', '#', '.', ':') else r'(?<![-\w%#.:])'
                        post_symbol = r'(?![-\w])'
                        new_parent = re.sub(prev_symbol + _parent + post_symbol, _c_selector, p_selector)
                        if p_selector != new_parent:
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
                    c_rule[SELECTORS] = c_selectors  # re-set the SELECTORS for the rules
                    deps.add(c_rule[POSITION])

                for p_rule in p_rules:
                    p_rule[SELECTORS] = new_selectors  # re-set the SELECTORS for the rules
                    p_rule[DEPS].update(deps)  # position is the "index" of the object

        return parent_found

    @print_timing(3)
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
                    rules = []  # further rules extending other parents will be empty

        cnt = 0
        parents_left = True
        while parents_left and cnt < 10:
            cnt += 1
            parents_left = False
            for _selectors in self.parts.keys():
                selectors, _, parent = _selectors.partition(' extends ')
                if not parent:
                    continue

                parents_left = True
                if _selectors not in self.parts:
                    continue  # Nodes might have been renamed while linking parents...

                rules = self.parts[_selectors]

                del self.parts[_selectors]
                self.parts.setdefault(selectors, [])
                self.parts[selectors].extend(rules)

                parents = self.link_with_parents(parent, selectors, rules)

                if parents is None:
                    log.warn("Parent rule not found: %s", parent)
                    continue

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

    @print_timing(3)
    def manage_order(self):
        # order rules according with their dependencies
        for rule in self.rules:
            if rule[POSITION] is None:
                continue

            rule[DEPS].add(rule[POSITION] + 1)
            # This moves the rules just above the topmost dependency during the sorted() below:
            rule[POSITION] = min(rule[DEPS])
        self.rules = sorted(self.rules, key=lambda o: o[POSITION])

    @print_timing(3)
    def parse_properties(self):
        self.css_files = []
        self._rules = {}
        css_files = set()
        old_fileid = None
        for rule in self.rules:
            #print >>sys.stderr, rule[FILEID], rule[POSITION], [ c for c in rule[CONTEXT] if c[1] != '_' ], rule[OPTIONS].keys(), rule[SELECTORS], rule[DEPS]
            if rule[POSITION] is not None and rule[PROPERTIES]:
                fileid = rule[FILEID]
                self._rules.setdefault(fileid, [])
                self._rules[fileid].append(rule)
                if old_fileid != fileid:
                    old_fileid = fileid
                    if fileid not in css_files:
                        css_files.add(fileid)
                        self.css_files.append(fileid)

    @print_timing(3)
    def create_css(self, fileid=None):
        """
        Generate the final CSS string
        """

        if fileid:
            rules = self._rules.get(fileid) or []
        else:
            rules = self.rules

        compress = self.scss_opts.get('compress', True)
        if compress:
            sc, sp, tb, nl = False, '', '', ''
        else:
            sc, sp, tb, nl = True, ' ', '  ', '\n'

        scope = set()
        return self._create_css(rules, scope, sc, sp, tb, nl, not compress and self.scss_opts.get('debug_info', False))

    def _create_css(self, rules, scope=None, sc=True, sp=' ', tb='  ', nl='\n', debug_info=False):
        if scope is None:
            scope = set()

        open_selectors = False
        skip_selectors = False
        old_selectors = None
        open_media = False
        old_media = None
        old_property = None

        wrap = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
        wrap.wordsep_re = re.compile(r'(?<=,)(\s*)')
        wrap = wrap.wrap

        total_rules = 0
        total_selectors = 0

        result = ''
        for rule in rules:
            #print >>sys.stderr, rule[FILEID], rule[MEDIA], rule[POSITION], [ c for c in rule[CONTEXT] if not c.startswith('$__') ], rule[OPTIONS].keys(), rule[SELECTORS], rule[DEPS]
            if rule[POSITION] is None or not rule[PROPERTIES]:
                continue

            selectors = rule[SELECTORS]
            media = rule[MEDIA]
            _tb = tb if old_media else ''
            if old_media != media or media is not None:
                if open_selectors:
                    if not skip_selectors:
                        if not sc and result[-1] == ';':
                            result = result[:-1]
                        result += _tb + '}' + nl
                    open_selectors = False
                    skip_selectors = False
                if open_media:
                    if not sc and result[-1] == ';':
                        result = result[:-1]
                    result += '}' + nl
                    open_media = False
                if media:
                    result += '@media ' + (' and ').join(set(media)) + sp + '{' + nl
                    open_media = True
                old_media = media
                old_selectors = None  # force entrance to add a new selector
            _tb = tb if media else ''
            if old_selectors != selectors or selectors is not None:
                if open_selectors:
                    if not skip_selectors:
                        if not sc and result[-1] == ';':
                            result = result[:-1]
                        result += _tb + '}' + nl
                    open_selectors = False
                    skip_selectors = False
                if selectors:
                    _selectors = [s for s in selectors.split(',') if '%' not in s]
                    if _selectors:
                        total_rules += 1
                        total_selectors += len(_selectors)
                        if debug_info:
                            _lineno = rule[LINENO]
                            line = rule[INDEX][_lineno]
                            filename, lineno = line.rsplit(':', 1)
                            real_filename, real_lineno = filename, lineno
                            # Walk up to a non-library file:
                            # while _lineno >= 0:
                            #     path, name = os.path.split(line)
                            #     if not name.startswith('_'):
                            #         filename, lineno = line.rsplit(':', 1)
                            #         break
                            #     line = rule[INDEX][_lineno]
                            #     _lineno -= 1
                            sass_debug_info = ''
                            if filename.startswith('<string '):
                                filename = '<unknown>'
                            if real_filename.startswith('<string '):
                                real_filename = '<unknown>'
                            if real_filename != filename or real_lineno != lineno:
                                if debug_info == 'comments':
                                    sass_debug_info += '/* file: %s, line: %s */' % (real_filename, real_lineno) + nl
                                else:
                                    real_filename = _escape_chars_re.sub(r'\\\1', real_filename)
                                    sass_debug_info += "@media -sass-debug-info{filename{font-family:file\:\/%s;}line{font-family:'%s';}}" % (real_filename, real_lineno) + nl
                            if debug_info == 'comments':
                                sass_debug_info += '/* file: %s, line: %s */' % (filename, lineno) + nl
                            else:
                                filename = _escape_chars_re.sub(r'\\\1', filename)
                                sass_debug_info += "@media -sass-debug-info{filename{font-family:file\:\/%s;}line{font-family:'%s';}}" % (filename, lineno) + nl
                            result += sass_debug_info
                        selector = (',' + sp).join('%s%s' % (self.super_selector, s) for s in _selectors) + sp + '{'
                        if nl:
                            selector = nl.join(wrap(selector))
                        result += _tb + selector + nl
                    else:
                        skip_selectors = True
                    open_selectors = True
                old_selectors = selectors
                scope = set()
            if selectors:
                _tb += tb
            if rule[OPTIONS].get('verbosity', 0) > 1:
                result += _tb + '/* file: ' + rule[FILEID] + ' */' + nl
                if rule[CONTEXT]:
                    result += _tb + '/* vars:' + nl
                    for k, v in rule[CONTEXT].items():
                        result += _tb + _tb + k + ' = ' + v + ';' + nl
                    result += _tb + '*/' + nl
            if not skip_selectors:
                result += self._print_properties(rule[PROPERTIES], scope, [old_property], sc, sp, _tb, nl, wrap)

        if open_media:
            _tb = tb
        else:
            _tb = ''
        if open_selectors and not skip_selectors:
            if not sc and result[-1] == ';':
                result = result[:-1]
            result += _tb + '}' + nl

        if open_media:
            if not sc and result[-1] == ';':
                result = result[:-1]
            result += '}' + nl

        return (result, total_rules, total_selectors)

    def _print_properties(self, properties, scope=None, old_property=None, sc=True, sp=' ', _tb='', nl='\n', wrap=None):
        if wrap is None:
            wrap = textwrap.TextWrapper(break_long_words=False)
            wrap.wordsep_re = re.compile(r'(?<=,)(\s*)')
            wrap = wrap.wrap
        if old_property is None:
            old_property = [None]
        if scope is None:
            scope = set()

        result = ''
        for lineno, prop, value in properties:
            if value is not None:
                if nl:
                    value = (nl + _tb + _tb).join(wrap(value))
                property = prop + ':' + sp + value
            else:
                property = prop
            if '!default' in property:
                property = property.replace('!default', '').replace('  ', ' ').strip()
                if prop in scope:
                    continue
            if old_property[0] != property:
                old_property[0] = property
                scope.add(prop)
                old_property[0] = property
                result += _tb + property + ';' + nl
        return result

    def calculate(self, _base_str, context, options, rule):
        better_expr_str = _base_str

        if _skip_word_re.match(better_expr_str) and '- ' not in better_expr_str and ' and ' not in better_expr_str and ' or ' not in better_expr_str and 'not ' not in better_expr_str:
            return better_expr_str

        rule = list(rule)
        rule[CONTEXT] = context
        rule[OPTIONS] = options

        better_expr_str = self.do_glob_math(better_expr_str, context, options, rule)

        better_expr_str = eval_expr(better_expr_str, rule, self._func_registry, True)

        if better_expr_str is None:
            better_expr_str = self.apply_vars(_base_str, context, options, rule)

        return better_expr_str

    def _calculate_expr(self, context, options, rule, _dequote):
        def __calculate_expr(result):
            _group0 = result.group(1)
            _base_str = _group0
            better_expr_str = eval_expr(_base_str, rule, self._func_registry)

            if better_expr_str is None:
                better_expr_str = self.apply_vars(_base_str, context, options, rule)
            elif _dequote:
                better_expr_str = dequote(str(better_expr_str))
            else:
                better_expr_str = str(better_expr_str)

            return better_expr_str
        return __calculate_expr

    def do_glob_math(self, cont, context, options, rule, _dequote=False):
        cont = str(cont)
        if '#{' not in cont:
            return cont
        cont = _expr_glob_re.sub(self._calculate_expr(context, options, rule, _dequote), cont)
        return cont

    @print_timing(3)
    def post_process(self, cont):
        compress = self.scss_opts.get('compress', 1) and 'compress_' or ''
        # short colors:
        if self.scss_opts.get(compress + 'short_colors', 1):
            cont = _short_color_re.sub(r'#\1\2\3', cont)
        # color names:
        if self.scss_opts.get(compress + 'reverse_colors', 1):
            cont = _reverse_colors_re.sub(lambda m: _reverse_colors[m.group(0).lower()], cont)
        if compress:
            # zero units out (i.e. 0px or 0em -> 0):
            cont = _zero_units_re.sub('0', cont)
            # remove zeros before decimal point (i.e. 0.3 -> .3)
            cont = _zero_re.sub('.', cont)
        return cont







def interpolate(var, rule, func_registry):
    context = rule[CONTEXT]
    var = normalize_var(var)
    value = context.get(var, var)
    if var != value and isinstance(value, basestring):
        _vi = eval_expr(value, rule, func_registry, True)
        if _vi is not None:
            value = _vi
    return value


def call(name, args, R, func_registry, is_function=True):
    C, O = R[CONTEXT], R[OPTIONS]
    # Function call:
    _name = normalize_var(name)
    s = args and args.value.items() or []
    _args = [v for n, v in s if isinstance(n, int)]
    _kwargs = dict((str(n[1:]).replace('-', '_'), v) for n, v in s if not isinstance(n, int) and n != '_')
    _fn_a = '%s:%d' % (_name, len(_args))
    #print >>sys.stderr, '#', _fn_a, _args, _kwargs
    _fn_n = '%s:n' % _name
    try:
        fn = O and O.get('@function ' + _fn_a)
        if fn:
            node = fn(R, *_args, **_kwargs)
        else:
            fn = func_registry.lookup(_name, len(_args))
            node = fn(*_args, **_kwargs)
    except KeyError:
        sp = args and args.value.get('_') or ''
        if is_function:
            if not _css_functions_re.match(_name):
                log.error("Required function not found: %s (%s)", _fn_a, R[INDEX][R[LINENO]], extra={'stack': True})
            _args = (sp + ' ').join(to_str(v) for n, v in s if isinstance(n, int))
            _kwargs = (sp + ' ').join('%s: %s' % (n, to_str(v)) for n, v in s if not isinstance(n, int) and n != '_')
            if _args and _kwargs:
                _args += (sp + ' ')
            # Function not found, simply write it as a string:
            node = StringValue(name + '(' + _args + _kwargs + ')')
        else:
            node = StringValue((sp + ' ').join(str(v) for n, v in s if n != '_'))
    return node



class CachedScanner(Scanner):
    """
    Same as Scanner, but keeps cached tokens for any given input
    """
    _cache_ = {}
    _goals_ = ['END']

    @classmethod
    def cleanup(cls):
        cls._cache_ = {}

    def __init__(self, patterns, ignore, input=None):
        try:
            self._tokens = self._cache_[input]
        except KeyError:
            self._tokens = None
            self.__tokens = {}
            self.__input = input
            super(CachedScanner, self).__init__(patterns, ignore, input)

    def reset(self, input):
        try:
            self._tokens = self._cache_[input]
        except KeyError:
            self._tokens = None
            self.__tokens = {}
            self.__input = input
            super(CachedScanner, self).reset(input)

    def __repr__(self):
        if self._tokens is None:
            return super(CachedScanner, self).__repr__()
        output = ''
        for t in self._tokens[-10:]:
            output = "%s\n  (@%s)  %s  =  %s" % (output, t[0], t[2], repr(t[3]))
        return output

    def token(self, i, restrict=None):
        if self._tokens is None:
            token = super(CachedScanner, self).token(i, restrict)
            self.__tokens[i] = token
            if token[2] in self._goals_:  # goal tokens
                self._cache_[self.__input] = self._tokens = self.__tokens
            return token
        else:
            token = self._tokens.get(i)
            if token is None:
                raise NoMoreTokens
            return token

    def rewind(self, i):
        if self._tokens is None:
            super(CachedScanner, self).rewind(i)


class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._pos = 0

    def reset(self, input):
        self._scanner.reset(input)
        self._pos = 0

    def _peek(self, types):
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
        tok = self._scanner.token(self._pos, set([type]))
        if tok[2] != type:
            raise SyntaxError("SyntaxError[@ char %s: %s]" % (repr(tok[0]), "Trying to find " + type))
        self._pos += 1
        return tok[3]

    def _rewind(self, n=1):
        self._pos -= min(n, self._pos)
        self._scanner.rewind(self._pos)


################################################################################
#'(?<!\\s)(?:' + '|'.join(_units) + ')(?![-\\w])'
## Grammar compiled using Yapps:

class CalculatorScanner(CachedScanner):
    patterns = None
    _patterns = [
        ('":"', ':'),
        ('[ \r\t\n]+', '[ \r\t\n]+'),
        ('COMMA', ','),
        ('LPAR', '\\(|\\['),
        ('RPAR', '\\)|\\]'),
        ('END', '$'),
        ('MUL', '[*]'),
        ('DIV', '/'),
        ('ADD', '[+]'),
        ('SUB', '-\\s'),
        ('SIGN', '-(?![a-zA-Z_])'),
        ('AND', '(?<![-\\w])and(?![-\\w])'),
        ('OR', '(?<![-\\w])or(?![-\\w])'),
        ('NOT', '(?<![-\\w])not(?![-\\w])'),
        ('NE', '!='),
        ('INV', '!'),
        ('EQ', '=='),
        ('LE', '<='),
        ('GE', '>='),
        ('LT', '<'),
        ('GT', '>'),
        ('STR', "'[^']*'"),
        ('QSTR', '"[^"]*"'),
        ('UNITS', '(?<!\\s)(?:' + '|'.join(_units) + ')(?![-\\w])'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('BOOL', '(?<![-\\w])(?:true|false)(?![-\\w])'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('ID', '[-a-zA-Z_][-a-zA-Z0-9_]*'),
    ]

    def __init__(self, input=None):
        if hasattr(self, 'setup_patterns'):
            self.setup_patterns(self._patterns)
        elif self.patterns is None:
            self.__class__.patterns = []
            for t, p in self._patterns:
                self.patterns.append((t, re.compile(p)))
        super(CalculatorScanner, self).__init__(None, ['[ \r\t\n]+'], input)


class Calculator(Parser):
    def goal(self, R):
        expr_lst = self.expr_lst(R)
        v = expr_lst.first() if len(expr_lst) == 1 else expr_lst
        END = self._scan('END')
        return v

    def expr(self, R):
        and_test = self.and_test(R)
        v = and_test
        while self._peek(self.expr_rsts) == 'OR':
            OR = self._scan('OR')
            and_test = self.and_test(R)
            v = and_test if isinstance(v, basestring) and _undefined_re.match(v) else (v or and_test)
        return v

    def and_test(self, R):
        not_test = self.not_test(R)
        v = not_test
        while self._peek(self.and_test_rsts) == 'AND':
            AND = self._scan('AND')
            not_test = self.not_test(R)
            v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) else (v and not_test)
        return v

    def not_test(self, R):
        _token_ = self._peek(self.not_test_rsts)
        if _token_ not in self.not_test_chks:
            comparison = self.comparison(R)
            return comparison
        else:  # in self.not_test_chks
            while 1:
                _token_ = self._peek(self.not_test_chks)
                if _token_ == 'NOT':
                    NOT = self._scan('NOT')
                    not_test = self.not_test(R)
                    v = 'undefined' if isinstance(not_test, basestring) and _undefined_re.match(not_test) else (not not_test)
                else:  # == 'INV'
                    INV = self._scan('INV')
                    not_test = self.not_test(R)
                    v = 'undefined' if isinstance(not_test, basestring) and _undefined_re.match(not_test) else _inv('!', not_test)
                if self._peek(self.not_test_rsts_) not in self.not_test_chks:
                    break
            return v

    def comparison(self, R):
        a_expr = self.a_expr(R)
        v = a_expr
        while self._peek(self.comparison_rsts) in self.comparison_chks:
            _token_ = self._peek(self.comparison_chks)
            if _token_ == 'LT':
                LT = self._scan('LT')
                a_expr = self.a_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else (v < a_expr)
            elif _token_ == 'GT':
                GT = self._scan('GT')
                a_expr = self.a_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else (v > a_expr)
            elif _token_ == 'LE':
                LE = self._scan('LE')
                a_expr = self.a_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else (v <= a_expr)
            elif _token_ == 'GE':
                GE = self._scan('GE')
                a_expr = self.a_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else (v >= a_expr)
            elif _token_ == 'EQ':
                EQ = self._scan('EQ')
                a_expr = self.a_expr(R)
                v = (None if isinstance(v, basestring) and _undefined_re.match(v) else v) == (None if isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else a_expr)
            else:  # == 'NE'
                NE = self._scan('NE')
                a_expr = self.a_expr(R)
                v = (None if isinstance(v, basestring) and _undefined_re.match(v) else v) != (None if isinstance(a_expr, basestring) and _undefined_re.match(a_expr) else a_expr)
        return v

    def a_expr(self, R):
        m_expr = self.m_expr(R)
        v = m_expr
        while self._peek(self.a_expr_rsts) in self.a_expr_chks:
            _token_ = self._peek(self.a_expr_chks)
            if _token_ == 'ADD':
                ADD = self._scan('ADD')
                m_expr = self.m_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(m_expr, basestring) and _undefined_re.match(m_expr) else (v + m_expr)
            else:  # == 'SUB'
                SUB = self._scan('SUB')
                m_expr = self.m_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(m_expr, basestring) and _undefined_re.match(m_expr) else (v - m_expr)
        return v

    def m_expr(self, R):
        u_expr = self.u_expr(R)
        v = u_expr
        while self._peek(self.m_expr_rsts) in self.m_expr_chks:
            _token_ = self._peek(self.m_expr_chks)
            if _token_ == 'MUL':
                MUL = self._scan('MUL')
                u_expr = self.u_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(u_expr, basestring) and _undefined_re.match(u_expr) else (v * u_expr)
            else:  # == 'DIV'
                DIV = self._scan('DIV')
                u_expr = self.u_expr(R)
                v = 'undefined' if isinstance(v, basestring) and _undefined_re.match(v) or isinstance(u_expr, basestring) and _undefined_re.match(u_expr) else (v / u_expr)
        return v

    def u_expr(self, R):
        _token_ = self._peek(self.u_expr_rsts)
        if _token_ == 'SIGN':
            SIGN = self._scan('SIGN')
            u_expr = self.u_expr(R)
            return 'undefined' if isinstance(u_expr, basestring) and _undefined_re.match(u_expr) else _inv('-', u_expr)
        elif _token_ == 'ADD':
            ADD = self._scan('ADD')
            u_expr = self.u_expr(R)
            return 'undefined' if isinstance(u_expr, basestring) and _undefined_re.match(u_expr) else u_expr
        else:  # in self.u_expr_chks
            atom = self.atom(R)
            v = atom
            if self._peek(self.u_expr_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
                v = call(UNITS, ListValue(ParserValue({0: v, 1: UNITS})), R, self._func_registry, False)
            return v

    def atom(self, R):
        _token_ = self._peek(self.u_expr_chks)
        if _token_ == 'LPAR':
            LPAR = self._scan('LPAR')
            expr_lst = self.expr_lst(R)
            RPAR = self._scan('RPAR')
            return expr_lst.first() if len(expr_lst) == 1 else expr_lst
        elif _token_ == 'ID':
            ID = self._scan('ID')
            return ID
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            v = None
            LPAR = self._scan('LPAR')
            if self._peek(self.atom_rsts) != 'RPAR':
                expr_lst = self.expr_lst(R)
                v = expr_lst
            RPAR = self._scan('RPAR')
            return call(FNCT, v, R, self._func_registry)
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
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return ColorValue(ParserValue(COLOR))
        else:  # == 'VAR'
            VAR = self._scan('VAR')
            return interpolate(VAR, R, self._func_registry)

    def expr_lst(self, R):
        n = None
        if self._peek(self.expr_lst_rsts) == 'VAR':
            VAR = self._scan('VAR')
            if self._peek(self.expr_lst_rsts_) == '":"':
                self._scan('":"')
                n = VAR
            else: self._rewind()
        expr_slst = self.expr_slst(R)
        v = {n or 0: expr_slst}
        while self._peek(self.expr_lst_rsts__) == 'COMMA':
            n = None
            COMMA = self._scan('COMMA')
            v['_'] = COMMA
            if self._peek(self.expr_lst_rsts) == 'VAR':
                VAR = self._scan('VAR')
                if self._peek(self.expr_lst_rsts_) == '":"':
                    self._scan('":"')
                    n = VAR
                else: self._rewind()
            expr_slst = self.expr_slst(R)
            v[n or len(v)] = expr_slst
        return ListValue(ParserValue(v))

    def expr_slst(self, R):
        expr = self.expr(R)
        v = {0: expr}
        while self._peek(self.expr_slst_rsts) not in self.expr_lst_rsts__:
            expr = self.expr(R)
            v[len(v)] = expr
        return ListValue(ParserValue(v)) if len(v) > 1 else v[0]

    not_test_rsts_ = set(['AND', 'LPAR', 'QSTR', 'END', 'COLOR', 'INV', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'ID', 'RPAR', 'OR'])
    m_expr_chks = set(['MUL', 'DIV'])
    comparison_rsts = set(['LPAR', 'QSTR', 'RPAR', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'ADD', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'INV', 'GE', 'BOOL', 'NOT', 'OR'])
    atom_rsts = set(['LPAR', 'QSTR', 'COLOR', 'INV', 'SIGN', 'NOT', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'RPAR', 'ID'])
    not_test_chks = set(['NOT', 'INV'])
    u_expr_chks = set(['LPAR', 'COLOR', 'QSTR', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    m_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'MUL', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'INV', 'ADD', 'BOOL', 'NOT', 'OR'])
    expr_lst_rsts_ = set(['LPAR', 'QSTR', 'COLOR', 'INV', 'SIGN', 'VAR', 'ADD', 'NUM', 'BOOL', '":"', 'STR', 'NOT', 'ID', 'FNCT'])
    expr_lst_rsts = set(['LPAR', 'QSTR', 'COLOR', 'INV', 'SIGN', 'NOT', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    and_test_rsts = set(['AND', 'LPAR', 'QSTR', 'END', 'COLOR', 'INV', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'ID', 'RPAR', 'OR'])
    u_expr_rsts_ = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'VAR', 'MUL', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'UNITS', 'EQ', 'ID', 'AND', 'INV', 'ADD', 'BOOL', 'NOT', 'OR'])
    u_expr_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    expr_rsts = set(['LPAR', 'QSTR', 'END', 'COLOR', 'INV', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'ID', 'RPAR', 'OR'])
    not_test_rsts = set(['LPAR', 'QSTR', 'COLOR', 'INV', 'SIGN', 'VAR', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'NOT', 'ID'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    expr_slst_rsts = set(['LPAR', 'QSTR', 'END', 'COLOR', 'INV', 'RPAR', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'SIGN', 'ID'])
    a_expr_chks = set(['ADD', 'SUB'])
    a_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'INV', 'ADD', 'BOOL', 'NOT', 'OR'])
    expr_lst_rsts__ = set(['END', 'COMMA', 'RPAR'])


    expr_lst_rsts_ = None

    def __init__(self, scanner, func_registry):
        self._func_registry = func_registry
        super(Calculator, self).__init__(scanner)


### Grammar ends.
################################################################################

expr_cache = {}
def eval_expr(expr, rule, func_registry, raw=False):
    # print >>sys.stderr, '>>',expr,'<<'
    results = None

    if not isinstance(expr, basestring):
        results = expr

    if results is None:
        if _variable_re.match(expr):
            expr = normalize_var(expr)
        if expr in rule[CONTEXT]:
            chkd = {}
            while expr in rule[CONTEXT] and expr not in chkd:
                chkd[expr] = 1
                _expr = rule[CONTEXT][expr]
                if _expr == expr:
                    break
                expr = _expr
        if not isinstance(expr, basestring):
            results = expr

    if results is None:
        if expr in expr_cache:
            results = expr_cache[expr]
        else:
            try:
                P = Calculator(CalculatorScanner(), func_registry)
                P.reset(expr)
                results = P.goal(rule)
            except SyntaxError:
                if config.DEBUG:
                    raise
            except Exception, e:
                log.exception("Exception raised: %s in `%s' (%s)", e, expr, rule[INDEX][rule[LINENO]])
                if config.DEBUG:
                    raise

            # TODO this is a clumsy hack for nondeterministic functions;
            # something better (and per-compiler rather than global) would be
            # nice
            if '$' not in expr and '(' not in expr:
                expr_cache[expr] = results

    if not raw and results is not None:
        results = to_str(results)

    # print >>sys.stderr, repr(expr),'==',results,'=='
    return results
