#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
pyScss, a Scss compiler for Python

@author     German M. Bravo (Kronuz) <german.mb@gmail.com>
@version    1.2.0 alpha
@see        https://github.com/Kronuz/pyScss
@copyright  (c) 2012-2013 German M. Bravo (Kronuz)
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


from collections import defaultdict, deque
import glob
import logging
import os.path
import re
import sys
import textwrap

from scss import config
from scss.cssdefs import (
    SEPARATOR,
    _short_color_re, _reverse_colors, _reverse_colors_re,
    _ml_comment_re, _sl_comment_re,
    _zero_units_re, _zero_re,
    _escape_chars_re,
    _spaces_re, _expand_rules_space_re, _collapse_properties_space_re,
    _strings_re, _prop_split_re,
)
from scss.expression import Calculator
from scss.functions import ALL_BUILTINS_LIBRARY
from scss.functions.compass.sprites import sprite_map
from scss.rule import UnparsedBlock, SassRule
from scss.types import BooleanValue, ListValue, Null, NumberValue, StringValue
from scss.util import depar, dequote, normalize_var, split_params, to_str, profile, print_timing

log = logging.getLogger(__name__)

################################################################################
# Load C acceleration modules
locate_blocks = None
try:
    from scss._speedups import locate_blocks
except ImportError:
    print >>sys.stderr, "Scanning acceleration disabled (_speedups not found)!"
    from scss._native import locate_blocks

################################################################################


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
    '$--doubleslash': '//',
    '$--bigcopen': '/*',
    '$--bigcclose': '*/',
    '$--doubledot': ':',
    '$--semicolon': ';',
    '$--curlybracketopen': '{',
    '$--curlybracketclosed': '}',

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

_default_search_paths = ['.']


################################################################################


class SourceFile(object):
    def __init__(self, filename, contents, parent_dir='.', is_string=False, is_sass=None, line_numbers=True, line_strip=True):
        self.filename = filename
        self.sass = filename.endswith('.sass') if is_sass is None else is_sass
        self.line_numbers = line_numbers
        self.line_strip = line_strip
        self.contents = self.prepare_source(contents)
        self.parent_dir = parent_dir
        self.is_string = is_string

    @classmethod
    def from_filename(cls, fn, filename=None, is_sass=None, line_numbers=True):
        if filename is None:
            _, filename = os.path.split(fn)

        with open(fn) as f:
            contents = f.read()

        return cls(filename, contents, is_sass=is_sass, line_numbers=line_numbers)

    @classmethod
    def from_string(cls, string, filename=None, is_sass=None, line_numbers=True):
        if filename is None:
            filename = "<string %r...>" % string[:50]

        return cls(filename, string, is_string=True, is_sass=is_sass, line_numbers=line_numbers)

    def parse_scss_line(self, line_no, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line.rstrip()  # remove EOL character

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ''
        else:
            state['line_buffer'] = ''

        output = state['prev_line']
        if self.line_strip:
            output = output.strip()
        output_line_no = state['prev_line_no']

        state['prev_line'] = line
        state['prev_line_no'] = line_no

        if output:
            if self.line_numbers:
                output = str(output_line_no + 1) + SEPARATOR + output
            output += '\n'
            ret += output

        return ret

    def parse_sass_line(self, line_no, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line.rstrip()  # remove EOL character

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ret
        else:
            state['line_buffer'] = ''

        indent = len(line) - len(line.lstrip())

        # make sure we support multi-space indent as long as indent is consistent
        if indent and not state['indent_marker']:
            state['indent_marker'] = indent

        if state['indent_marker']:
            indent /= state['indent_marker']

        if indent == state['prev_indent']:
            # same indentation as previous line
            if state['prev_line']:
                state['prev_line'] += ';'
        elif indent > state['prev_indent']:
            # new indentation is greater than previous, we just entered a new block
            state['prev_line'] += ' {'
            state['nested_blocks'] += 1
        else:
            # indentation is reset, we exited a block
            block_diff = state['prev_indent'] - indent
            if state['prev_line']:
                state['prev_line'] += ';'
            state['prev_line'] += ' }' * block_diff
            state['nested_blocks'] -= block_diff

        output = state['prev_line']
        if self.line_strip:
            output = output.strip()
        output_line_no = state['prev_line_no']

        state['prev_indent'] = indent
        state['prev_line'] = line
        state['prev_line_no'] = line_no

        if output:
            if self.line_numbers:
                output = str(output_line_no + 1) + SEPARATOR + output
            output += '\n'
            ret += output
        return ret

    def prepare_source(self, codestr, sass=False):
        # Decorate lines with their line numbers and a delimiting NUL and remove empty lines
        state = {
            'line_buffer': '',
            'prev_line': '',
            'prev_line_no': 0,
            'prev_indent': 0,
            'nested_blocks': 0,
            'indent_marker': 0,
        }
        if self.sass:
            parse_line = self.parse_sass_line
        else:
            parse_line = self.parse_scss_line
        _codestr = codestr
        codestr = ''
        for line_no, line in enumerate(_codestr.splitlines()):
            codestr += parse_line(line_no, line, state)
        codestr += parse_line(None, None, state)  # parse the last line stored in prev_line buffer

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

        return codestr


class Scss(object):
    def __init__(self, scss_vars=None, scss_opts=None, scss_files=None, super_selector=None, library=ALL_BUILTINS_LIBRARY, search_paths=None):
        if super_selector:
            self.super_selector = super_selector + ' '
        else:
            self.super_selector = ''
        self._scss_vars = scss_vars
        self._scss_opts = scss_opts
        self._scss_files = scss_files
        self._library = library
        self._search_paths = search_paths

        self.reset()

    def get_scss_constants(self):
        scss_vars = self.scss_vars or {}
        return dict((k, v) for k, v in scss_vars.items() if k and (not k.startswith('$') or k.startswith('$') and k[1].isupper()))

    def get_scss_vars(self):
        scss_vars = self.scss_vars or {}
        return dict((k, v) for k, v in scss_vars.items() if k and not (not k.startswith('$') or k.startswith('$') and k[1].isupper()))

    def reset(self, input_scss=None):
        # Initialize
        self.scss_vars = _default_scss_vars.copy()
        if self._scss_vars is not None:
            self.scss_vars.update(self._scss_vars)

        self.scss_opts = _default_scss_opts.copy()
        if self._scss_opts is not None:
            self.scss_opts.update(self._scss_opts)

        # Figure out search paths.  Fall back from provided explicitly to
        # defined globally to just searching the current directory
        self.search_paths = list(_default_search_paths)
        if self._search_paths is not None:
            assert not isinstance(self._search_paths, basestring), \
                "`search_paths` should be an iterable, not a string"
            self.search_paths.extend(self._search_paths)
        else:
            if config.LOAD_PATHS:
                if isinstance(config.LOAD_PATHS, basestring):
                    # Back-compat: allow comma-delimited
                    self.search_paths.extend(config.LOAD_PATHS.split(','))
                else:
                    self.search_paths.extend(config.LOAD_PATHS)

            self.search_paths.extend(self.scss_opts.get('load_paths', []))

        self.source_files = []
        self.source_file_index = {}
        if self._scss_files is not None:
            for name, contents in self._scss_files.iteritems():
                if name in self.source_file_index:
                    raise KeyError("Duplicate filename %r" % name)
                source_file = SourceFile(name, contents)
                self.source_files.append(source_file)
                self.source_file_index[name] = source_file

        self.rules = []

    #@profile
    #@print_timing(2)
    def Compilation(self, scss_string=None, scss_file=None, super_selector=None, filename=None, is_sass=None, line_numbers=True):
        if super_selector:
            self.super_selector = super_selector + ' '
        self.reset()

        source_file = None
        if scss_string is not None:
            source_file = SourceFile.from_string(scss_string, filename, is_sass, line_numbers)
        elif scss_file is not None:
            source_file = SourceFile.from_filename(scss_file, filename, is_sass, line_numbers)

        if source_file is not None:
            # Clear the existing list of files
            self.source_files = []
            self.source_file_index = dict()

            self.source_files.append(source_file)
            self.source_file_index[source_file.filename] = source_file

        # Compile
        from scss.rule import Namespace
        namespace = Namespace(variables=self.scss_vars, functions=self._library)

        children = deque()
        for source_file in self.source_files:
            rule = SassRule(
                source_file=source_file,

                unparsed_contents=source_file.contents,
                namespace=namespace,
                options=self.scss_opts,
            )
            children.append(rule)

        # this will manage rule: child objects inside of a node
        self.parse_children(children)

        # this will manage @extends
        self.parse_extends()

        # this will manage the order of the rules
        self.manage_order()

        rules_by_file, css_files = self.parse_properties()

        all_rules = 0
        all_selectors = 0
        exceeded = ''
        final_cont = ''
        files = len(css_files)
        for source_file in css_files:
            rules = rules_by_file[source_file]
            fcont, total_rules, total_selectors = self.create_css(rules)
            all_rules += total_rules
            all_selectors += total_selectors
            if not exceeded and all_selectors > 4095:
                exceeded = " (IE exceeded!)"
                log.error("Maximum number of supported selectors in Internet Explorer (4095) exceeded!")
            if files > 1 and self.scss_opts.get('debug_info', False):
                if source_file.is_string:
                    final_cont += "/* %s %s generated add up to a total of %s %s accumulated%s */\n" % (
                        total_selectors,
                        'selector' if total_selectors == 1 else 'selectors',
                        all_selectors,
                        'selector' if all_selectors == 1 else 'selectors',
                        exceeded)
                else:
                    final_cont += "/* %s %s generated from '%s' add up to a total of %s %s accumulated%s */\n" % (
                        total_selectors,
                        'selector' if total_selectors == 1 else 'selectors',
                        source_file.filename,
                        all_selectors,
                        'selector' if all_selectors == 1 else 'selectors',
                        exceeded)
            final_cont += fcont

        final_cont = self.post_process(final_cont)

        return final_cont

    compile = Compilation

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

    def parse_selectors(self, raw_selectors):
        """
        Parses out the old xCSS "foo extends bar" syntax.

        Returns a 2-tuple: a set of selectors, and a set of extended selectors.
        """
        # Fixe tabs and spaces in selectors
        raw_selectors = _spaces_re.sub(' ', raw_selectors)

        parents = set()
        if ' extends ' in raw_selectors:
            selectors = set()
            for key in raw_selectors.split(','):
                child, _, parent = key.partition(' extends ')
                child = child.strip()
                parent = parent.strip()
                selectors.add(child)
                parents.update(s.strip() for s in parent.split('&'))
        else:
            selectors = set(s.strip() for s in raw_selectors.split(','))

        selectors.discard('')
        parents.discard('')

        return selectors, parents

    @print_timing(3)
    def parse_children(self, children):
        while children:
            rule = children.popleft()

            # manage children or expand children:
            new_children = deque()
            self.manage_children(rule, new_children, None)
            children.extendleft(new_children)

            self.rules.append(rule)

    @print_timing(4)
    def manage_children(self, rule, p_children, scope):
        # A rule that has already returned should not end up here
        assert rule.retval is None

        calculator = Calculator(rule.namespace)

        for c_lineno, c_property, c_codestr in locate_blocks(rule.unparsed_contents):
            block = UnparsedBlock(rule, c_lineno, c_property, c_codestr)

            if block.is_atrule:
                code = block.directive
                code = code.lower()
                if code == '@warn':
                    value = calculator.calculate(block.argument)
                    log.warn(dequote(to_str(value)))
                elif code == '@print':
                    value = calculator.calculate(block.argument)
                    print >>sys.stderr, dequote(to_str(value))
                elif code == '@raw':
                    value = calculator.calculate(block.argument)
                    print >>sys.stderr, repr(value)
                elif code == '@dump_context':
                    log.info(repr(rule.context))
                elif code == '@dump_options':
                    log.info(repr(rule.options))
                elif code == '@debug':
                    setting = block.argument.strip()
                    if setting.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
                        setting = 1
                    elif setting.lower() in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
                        setting = 0
                    config.DEBUG = setting
                    log.info("Debug mode is %s", 'On' if config.DEBUG else 'Off')
                elif code == '@option':
                    self._settle_options(rule, p_children, scope, block)
                elif code == '@content':
                    self._do_content(rule, p_children, scope, block)
                elif code == '@import':
                    self._do_import(rule, p_children, scope, block)
                elif code == '@extend':
                    selectors = calculator.apply_vars(block.argument)
                    rule.extends_selectors.update(p.strip() for p in selectors.replace(',', '&').split('&'))
                    rule.extends_selectors.discard('')
                elif code == '@return':
                    ret = calculator.calculate(block.argument)
                    rule.retval = ret
                    return
                elif code == '@include':
                    self._do_include(rule, p_children, scope, block)
                elif code in ('@mixin', '@function'):
                    self._do_functions(rule, p_children, scope, block)
                elif code in ('@if', '@else if'):
                    self._do_if(rule, p_children, scope, block)
                elif code == '@else':
                    self._do_else(rule, p_children, scope, block)
                elif code == '@for':
                    self._do_for(rule, p_children, scope, block)
                elif code == '@each':
                    self._do_each(rule, p_children, scope, block)
                # elif code == '@while':
                #     self._do_while(rule, p_children, scope, block)
                elif code in ('@variables', '@vars'):
                    self._get_variables(rule, p_children, scope, block)
                elif block.unparsed_contents is None:
                    rule.properties.append((block.prop, None))
                elif scope is None:  # needs to have no scope to crawl down the nested rules
                    self._nest_rules(rule, p_children, scope, block)
            ####################################################################
            # Properties
            elif block.unparsed_contents is None:
                self._get_properties(rule, p_children, scope, block)
            # Nested properties
            elif block.is_scope:
                if block.header.unscoped_value:
                    # Possibly deal with default unscoped value
                    self._get_properties(rule, p_children, scope, block)

                rule.unparsed_contents = block.unparsed_contents
                subscope = (scope or '') + block.header.scope + '-'
                self.manage_children(rule, p_children, subscope)
            ####################################################################
            # Nested rules
            elif scope is None:  # needs to have no scope to crawl down the nested rules
                self._nest_rules(rule, p_children, scope, block)

    @print_timing(10)
    def _settle_options(self, rule, p_children, scope, block):
        for option in block.argument.split(','):
            option, value = (option.split(':', 1) + [''])[:2]
            option = option.strip().lower()
            value = value.strip()
            if option:
                if value.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
                    value = 1
                elif value.lower() in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
                    value = 0
                rule.options[option.replace('-', '_')] = value

    @print_timing(10)
    def _do_functions(self, rule, p_children, scope, block):
        """
        Implements @mixin and @function
        """
        if not block.argument:
            raise SyntaxError("%s requires a function name (%s)" % (block.directive, rule.file_and_line))

        funct, params, _ = block.argument.partition('(')
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
                    calculator = Calculator(rule.namespace)
                    defaults[param] = calculator.parse_expression(default)
        mixin = [list(new_params), defaults, block.unparsed_contents]
        if block.directive == '@function':
            def _call(mixin):
                def __call(namespace, *args, **kwargs):
                    m_params = mixin[0]
                    m_vars = namespace.derive()
                    m_codestr = mixin[2]
                    calculator = Calculator(m_vars)
                    for key, value in mixin[1].items():
                        m_vars.set_variable(key, value.evaluate(calculator))
                    for i, a in enumerate(args):
                        m_vars.set_variable(m_params[i], a)
                    for k, v in kwargs.items():
                        m_vars.set_variable('$' + k, v)

                    _rule = SassRule(
                        # TODO correct?  relevant?  seems the function should
                        # consider itself as existing where it was defined, not
                        # called?
                        source_file=rule.source_file,

                        # TODO
                        unparsed_contents=m_codestr,
                        #context=m_vars,
                        options=rule.options.copy(),
                        lineno=block.lineno,

                        # R
                        #ancestry=R.ancestry,
                        #extends_selectors=R.extends_selectors,

                        namespace=m_vars,
                    )
                    self.manage_children(_rule, p_children, scope)
                    ret = _rule.retval
                    if ret is None:
                        ret = Null()
                    return ret
                return __call
            _mixin = _call(mixin)
            _mixin.mixin = mixin
            mixin = _mixin

        if block.directive == '@mixin':
            add = rule.namespace.set_mixin
        elif block.directive == '@function':
            add = rule.namespace.set_function

        # Register the mixin for every possible arity it takes
        while len(new_params):
            add(funct, len(new_params), mixin)
            param = new_params.pop()
            if param not in defaults:
                break
        if not new_params:
            add(funct, 0, mixin)

    @print_timing(10)
    def _do_include(self, rule, p_children, scope, block):
        """
        Implements @include, for @mixins
        """
        funct, params, _ = block.argument.partition('(')
        calculator = Calculator(rule.namespace)
        funct = calculator.do_glob_math(funct)
        funct = normalize_var(funct.strip())
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
        try:
            mixin = rule.namespace.mixin(funct, num_args)
        except KeyError:
            try:
                # Fallback to single parameter
                # TODO don't do this, once ... works
                mixin = rule.namespace.mixin(funct, 1)
                if all(map(lambda o: isinstance(o, int), new_params.keys())):
                    new_params = {0: ', '.join(new_params.values())}
            except KeyError:
                log.error("Required mixin not found: %s:%d (%s)", funct, num_args, rule.file_and_line, extra={'stack': True})
                return

        m_params = mixin[0]
        m_vars = rule.namespace.derive()
        for key, value in mixin[1].items():
            m_vars.set_variable(key, value.evaluate(calculator))
        m_codestr = mixin[2]
        for varname, value in new_params.items():
            try:
                m_param = m_params[varname]
            except (IndexError, KeyError, TypeError):
                m_param = varname
            value = calculator.calculate(value)
            m_vars.set_variable(m_param, value)
        for p in m_params:
            if p not in new_params and isinstance(m_vars.variable(p), basestring):
                value = calculator.calculate(m_vars.variable(p))
                m_vars.set_variable(p, value)

        _rule = rule.copy()
        _rule.unparsed_contents = m_codestr
        _rule.namespace = m_vars
        _rule.lineno = block.lineno

        _rule.options['@content'] = block.unparsed_contents
        self.manage_children(_rule, p_children, scope)

    @print_timing(10)
    def _do_content(self, rule, p_children, scope, block):
        """
        Implements @content
        """
        if '@content' not in rule.options:
            log.error("Content string not found for @content (%s)", rule.file_and_line)
        rule.unparsed_contents = rule.options.pop('@content', '')
        self.manage_children(rule, p_children, scope)

    @print_timing(10)
    def _do_import(self, rule, p_children, scope, block):
        """
        Implements @import
        Load and import mixins and functions and rules
        """
        # Protect against going to prohibited places...
        if any(scary_token in block.argument for scary_token in ('..', '://', 'url(')):
            rule.properties.append((block.prop, None))
            return

        full_filename = None
        i_codestr = None
        names = block.argument.split(',')
        for name in names:
            name = dequote(name.strip())
            if '@import ' + name in rule.options:
                # If already imported in this scope, skip
                continue

            unsupported = []
            load_paths = []
            filename = os.path.basename(name)
            dirname = os.path.dirname(name)

            try:
                i_codestr = self.source_file_index[name]
            except KeyError:
                i_codestr = None

                for path in self.search_paths:
                    for basepath in ['.', rule.source_file.parent_dir]:
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
                    i_codestr = self._do_magic_import(rule, p_children, scope, block)
                if i_codestr is not None:
                    source_file = SourceFile(full_filename, i_codestr, parent_dir=os.path.dirname(full_filename))
                    self.source_files.append(source_file)
                    self.source_file_index[name] = source_file
            if i_codestr is None:
                load_paths = load_paths and "\nLoad paths:\n\t%s" % "\n\t".join(load_paths) or ''
                unsupported = unsupported and "\nPossible matches (for unsupported file format SASS):\n\t%s" % "\n\t".join(unsupported) or ''
                log.warn("File to import not found or unreadable: '%s' (%s)%s%s", filename, rule.file_and_line, load_paths, unsupported)
            else:
                _rule = SassRule(
                    source_file=source_file,
                    lineno=block.lineno,
                    unparsed_contents=source_file.contents,

                    # rule
                    #dependent_rules
                    options=rule.options,
                    properties=rule.properties,
                    extends_selectors=rule.extends_selectors,
                    ancestry=rule.ancestry,
                    namespace=rule.namespace,
                )
                self.manage_children(_rule, p_children, scope)
                rule.options['@import ' + name] = True

    @print_timing(10)
    def _do_magic_import(self, rule, p_children, scope, block):
        """
        Implements @import for sprite-maps
        Imports magic sprite map directories
        """
        if callable(config.STATIC_ROOT):
            files = sorted(config.STATIC_ROOT(block.argument))
        else:
            glob_path = os.path.join(config.STATIC_ROOT, block.argument)
            files = glob.glob(glob_path)
            files = sorted((file[len(config.STATIC_ROOT):], None) for file in files)

        if not files:
            return

        # Build magic context
        map_name = os.path.normpath(os.path.dirname(block.argument)).replace('\\', '_').replace('/', '_')
        kwargs = {}

        calculator = Calculator(rule.namespace)

        def setdefault(var, val):
            _var = '$' + map_name + '-' + var
            if _var in rule.context:
                kwargs[var] = calculator.interpolate(rule.context[_var], rule, self._library)
            else:
                rule.context[_var] = val
                kwargs[var] = calculator.interpolate(val, rule, self._library)
            return rule.context[_var]

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
        rule.context['$' + map_name + '-' + 'sprites'] = sprite_map(block.argument, **kwargs)
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
    def _do_if(self, rule, p_children, scope, block):
        """
        Implements @if and @else if
        """
        # "@if" indicates whether any kind of `if` since the last `@else` has
        # succeeded, in which case `@else if` should be skipped
        if block.directive != '@if':
            if '@if' not in rule.options:
                raise SyntaxError("@else with no @if (%s)" % (rule.file_and_line,))
            if rule.options['@if']:
                # Last @if succeeded; stop here
                return

        calculator = Calculator(rule.namespace)
        condition = calculator.calculate(block.argument)
        if condition:
            rule.unparsed_contents = block.unparsed_contents
            self.manage_children(rule, p_children, scope)
        rule.options['@if'] = condition

    @print_timing(10)
    def _do_else(self, rule, p_children, scope, block):
        """
        Implements @else
        """
        if '@if' not in rule.options:
            log.error("@else with no @if (%s)", rule.file_and_line)
        val = rule.options.pop('@if', True)
        if not val:
            rule.unparsed_contents = block.unparsed_contents
            self.manage_children(rule, p_children, scope)

    @print_timing(10)
    def _do_for(self, rule, p_children, scope, block):
        """
        Implements @for
        """
        var, _, name = block.argument.partition(' from ')
        frm, _, through = name.partition(' through ')
        if not through:
            frm, _, through = frm.partition(' to ')
        calculator = Calculator(rule.namespace)
        frm = calculator.calculate(frm)
        through = calculator.calculate(through)
        try:
            frm = int(float(frm))
            through = int(float(through))
        except ValueError:
            return

        if frm > through:
            frm, through = through, frm
            rev = reversed
        else:
            rev = lambda x: x
        var = var.strip()
        var = calculator.do_glob_math(var)
        var = normalize_var(var)

        for i in rev(range(frm, through + 1)):
            rule.unparsed_contents = block.unparsed_contents
            rule.namespace.set_variable(var, str(i))
            self.manage_children(rule, p_children, scope)

    @print_timing(10)
    def _do_each(self, rule, p_children, scope, block):
        """
        Implements @each
        """
        var, _, name = block.argument.partition(' in ')
        calculator = Calculator(rule.namespace)
        name = calculator.calculate(name)
        if not name:
            return

        name = ListValue(name)
        var = var.strip()
        var = calculator.do_glob_math(var)
        var = normalize_var(var)

        for n, v in name.items():
            v = to_str(v)
            inner_rule = rule.copy()
            inner_rule.namespace = inner_rule.namespace.derive()
            inner_rule.unparsed_contents = block.unparsed_contents
            inner_rule.namespace.set_variable(var, v)
            if not isinstance(n, int):
                inner_rule.namespace.set_variable(n, v)
            self.manage_children(inner_rule, p_children, scope)

    # @print_timing(10)
    # def _do_while(self, rule, p_children, scope, block):
    #     THIS DOES NOT WORK AS MODIFICATION OF INNER VARIABLES ARE NOT KNOWN AT THIS POINT!!
    #     """
    #     Implements @while
    #     """
    #     first_val = None
    #     while True:
    #         val = self.calculator.calculate(block.argument, rule, rule.context, rule.options)
    #         val = bool(False if not val or isinstance(val, basestring) and (val in ('0', 'false', 'undefined') or _variable_re.match(val)) else val)
    #         if first_val is None:
    #             first_val = val
    #         if not val:
    #             break
    #         rule.unparsed_contents = block.unparsed_contents
    #         self.manage_children(rule, p_children, scope)
    #     rule.options['@if'] = first_val

    @print_timing(10)
    def _get_variables(self, rule, p_children, scope, block):
        """
        Implements @variables and @vars
        """
        _rule = rule.copy()
        _rule.unparsed_contents = block.unparsed_contents
        _rule.namespace = rule.namespace
        _rule.properties = {}
        self.manage_children(_rule, p_children, scope)
        for name, value in _rule.properties.items():
            rule.namespace.set_variable(name, value)

    @print_timing(10)
    def _get_properties(self, rule, p_children, scope, block):
        """
        Implements properties and variables extraction and assignment
        """
        prop, value = (_prop_split_re.split(block.prop, 1) + [None])[:2]
        try:
            is_var = (block.prop[len(prop)] == '=')
        except IndexError:
            is_var = False
        calculator = Calculator(rule.namespace)
        prop = prop.strip()
        prop = calculator.do_glob_math(prop)
        if not prop:
            return

        # Parse the value and determine whether it's a default assignment
        is_default = False
        if value is not None:
            value = value.strip()
            if prop.startswith('$'):
                value, subs = re.subn(r'(?i)\s+!default\Z', '', value)
                if subs:
                    is_default = True

            value = calculator.calculate(value)

        _prop = (scope or '') + prop
        if is_var or prop.startswith('$') and value is not None:
            _prop = normalize_var(_prop)
            try:
                existing_value = rule.namespace.variable(_prop)
            except KeyError:
                existing_value = None

            is_defined = existing_value is not None and not existing_value.is_null
            if is_default and is_defined:
                pass
            else:
                if is_defined and prop.startswith('$') and prop[1].isupper():
                    log.warn("Constant %r redefined", prop)

                rule.namespace.set_variable(_prop, value)
        else:
            _prop = calculator.apply_vars(_prop)
            rule.properties.append((_prop, to_str(value) if value is not None else None))

    @print_timing(10)
    def _nest_rules(self, rule, p_children, scope, block):
        """
        Implements Nested CSS rules
        """
        if block.is_atrule:
            new_ancestry = list(rule.ancestry)
            if block.directive == '@media' and rule.ancestry:
                for i, header in reversed(list(enumerate(new_ancestry))):
                    if header.is_selector:
                        continue
                    elif header.directive == '@media':
                        from scss.rule import BlockAtRuleHeader
                        new_ancestry[i] = BlockAtRuleHeader(
                            '@media',
                            "%s and %s" % (header.argument, block.argument))
                        break
                    else:
                        new_ancestry.insert(i, block.header)
                else:
                    new_ancestry.insert(0, block.header)
            else:
                new_ancestry.append(block.header)

            new_rule = SassRule(
                source_file=rule.source_file,
                lineno=block.lineno,
                unparsed_contents=block.unparsed_contents,

                #dependent_rules
                options=rule.options.copy(),
                #properties
                #extends_selectors
                ancestry=new_ancestry,

                namespace=rule.namespace.derive(),
            )

            p_children.appendleft(new_rule)

            return

        calculator = Calculator(rule.namespace)
        raw_selectors = calculator.apply_vars(block.prop)
        c_selectors, c_parents = self.parse_selectors(raw_selectors)

        p_selectors = rule.selectors
        if not p_selectors:
            # If no parents, pretend there's a single dummy parent selector
            # so the loop below runs once
            # XXX this is grody man and leaks down through all over the place
            p_selectors = frozenset(('',))

        better_selectors = set()
        for c_selector in c_selectors:
            for p_selector in p_selectors:
                if c_selector == 'self':
                    # xCSS extension: "self" means to hoist to the parent
                    better_selectors.add(p_selector)
                elif '&' in c_selector:  # Parent References
                    better_selectors.add(c_selector.replace('&', p_selector))
                elif p_selector:
                    better_selectors.add(p_selector + ' ' + c_selector)
                else:
                    better_selectors.add(c_selector)

        # Merge ancestry
        from scss.rule import BlockSelectorHeader
        selector_header = BlockSelectorHeader(better_selectors)
        if rule.ancestry and rule.ancestry[-1].is_selector:
            new_ancestry = rule.ancestry[:-1] + [selector_header]
        else:
            new_ancestry = rule.ancestry + [selector_header]

        _rule = SassRule(
            source_file=rule.source_file,
            lineno=block.lineno,
            unparsed_contents=block.unparsed_contents,

            #dependent_rules
            options=rule.options.copy(),
            #properties
            extends_selectors=c_parents,
            ancestry=new_ancestry,

            namespace=rule.namespace.derive(),
        )

        p_children.appendleft(_rule)

    @print_timing(4)
    def link_with_parents(self, grouped_rules, parent, c_selectors, c_rules):
        """
        Link with a parent for the current child rule.
        If parents found, returns a list of parent rules to the child
        """
        parent_found = None
        for (p_selectors, p_extends), p_rules in grouped_rules.items():
            new_selectors = set()
            found = False

            # Finds all the parent selectors and parent selectors with another
            # bind selectors behind. For example, if `.specialClass` extends `.baseClass`,
            # and there is a `.baseClass` selector, the extension should create
            # `.specialClass` for that rule, but if there's also a `.baseClass a`
            # it also should create `.specialClass a`
            for p_selector in p_selectors:
                if parent not in p_selector:
                    continue

                # get the new child selector to add (same as the parent selector but with the child name)
                # since selectors can be together, separated with # or . (i.e. something.parent) check that too:
                for c_selector in c_selectors:
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

            new_selectors = frozenset(new_selectors)
            if new_selectors:
                # Re-include parents
                new_selectors |= p_selectors

                # rename node:
                if new_selectors != p_selectors:
                    del grouped_rules[p_selectors, p_extends]
                    new_key = new_selectors, p_extends
                    grouped_rules[new_key].extend(p_rules)

                deps = set()
                # save child dependencies:
                for c_rule in c_rules or []:
                    assert c_rule.selectors == c_selectors
                    deps.add(c_rule.position)

                for p_rule in p_rules:
                    p_rule.selectors = new_selectors  # re-set the SELECTORS for the rules
                    p_rule.dependent_rules.update(deps)  # position is the "index" of the object

        return parent_found

    @print_timing(3)
    def parse_extends(self):
        """
        For each part, create the inheritance parts from the @extends
        """
        # First group rules by a tuple of (selectors, @extends)
        pos = 0
        grouped_rules = defaultdict(list)
        for rule in self.rules:
            pos += 1
            rule.position = pos

            key = rule.selectors, frozenset(rule.extends_selectors)
            grouped_rules[key].append(rule)

        # To be able to manage multiple extends, you need to
        # destroy the actual node and create many nodes that have
        # mono extend. The first one gets all the css rules
        for (selectors, parents), rules in grouped_rules.items():
            if len(parents) <= 1:
                continue

            del grouped_rules[selectors, parents]
            for parent in parents:
                new_key = selectors, frozenset((parent,))
                grouped_rules[new_key].extend(rules)
                rules = []  # further rules extending other parents will be empty

        cnt = 0
        parents_left = True
        while parents_left and cnt < 10:
            cnt += 1
            parents_left = False
            for key in grouped_rules.keys():
                if key not in grouped_rules:
                    # Nodes might have been renamed while linking parents...
                    continue

                selectors, orig_parents = key
                if not orig_parents:
                    continue

                parent, = orig_parents
                parents_left = True

                rules = grouped_rules.pop(key)
                new_key = selectors, frozenset()
                grouped_rules[new_key].extend(rules)

                parents = self.link_with_parents(grouped_rules, parent, selectors, rules)

                if parents is None:
                    log.warn("Parent rule not found: %s", parent)
                    continue

                # from the parent, inherit the context and the options:
                from scss.rule import Namespace
                parent_namespaces = [parent.namespace for parent in parents]
                new_options = {}
                for parent in parents:
                    new_options.update(parent.options)
                for rule in rules:
                    rule.namespace = Namespace.derive_from(
                        rule.namespace, *parent_namespaces)
                    _new_options = new_options.copy()
                    _new_options.update(rule.options)
                    rule.options = _new_options

    @print_timing(3)
    def manage_order(self):
        # order rules according with their dependencies
        for rule in self.rules:
            assert rule.position is not None

            rule.dependent_rules.add(rule.position + 1)
            # This moves the rules just above the topmost dependency during the sorted() below:
            rule.position = min(rule.dependent_rules)
        self.rules.sort(key=lambda o: o.position)

    @print_timing(3)
    def parse_properties(self):
        css_files = []
        seen_files = set()
        rules_by_file = {}

        for rule in self.rules:
            assert rule.position is not None
            if not rule.properties:
                continue

            source_file = rule.source_file
            rules_by_file.setdefault(source_file, []).append(rule)

            if source_file not in seen_files:
                seen_files.add(source_file)
                css_files.append(source_file)

        return rules_by_file, css_files

    @print_timing(3)
    def create_css(self, rules):
        """
        Generate the final CSS string
        """
        compress = self.scss_opts.get('compress', True)
        if compress:
            sc, sp, tb, nl = False, '', '', ''
        else:
            sc, sp, tb, nl = True, ' ', '  ', '\n'

        return self._create_css(rules, sc, sp, tb, nl, not compress and self.scss_opts.get('debug_info', False))

    def _create_css(self, rules, sc=True, sp=' ', tb='  ', nl='\n', debug_info=False):
        skip_selectors = False

        old_ancestry = []

        textwrap.TextWrapper.wordsep_re = re.compile(r'(?<=,)(\s*)')
        if hasattr(textwrap.TextWrapper, 'wordsep_simple_re'):
            wrap = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
        else:
            wrap = textwrap.TextWrapper(break_long_words=False)
        wrap = wrap.wrap

        total_rules = 0
        total_selectors = 0

        result = ''
        for rule in rules:
            # TODO this is wrong; what about, say, @imports
            if rule.is_empty:
                continue

            ancestry = rule.ancestry

            first_mismatch = 0
            for i, (old_header, new_header) in enumerate(zip(old_ancestry, ancestry)):
                if old_header != new_header:
                    first_mismatch = i
                    break

            # Close blocks and outdent as necessary
            for i in range(len(old_ancestry), first_mismatch, -1):
                result += tb * (i - 1) + '}' + nl

            # Open new blocks as necessary
            for i in range(first_mismatch, len(ancestry)):
                if debug_info:
                    if not rule.source_file.is_string:
                        filename = rule.source_file.filename
                        lineno = str(rule.lineno)
                        if debug_info == 'comments':
                            result += '/* file: %s, line: %s */' % (filename, lineno) + nl
                        else:
                            filename = _escape_chars_re.sub(r'\\\1', filename)
                            result += "@media -sass-debug-info{filename{font-family:file\:\/\/%s}line{font-family:\\00003%s}}" % (filename, lineno) + nl

                if ancestry[i].is_selector:
                    header = ancestry[i].render(sep=',' + sp, super_selector=self.super_selector)
                    if nl:
                        header = nl.join(wrap(header))
                else:
                    header = ancestry[i].render()
                result += tb * i + header + sp + '{' + nl

                total_rules += 1
                if ancestry[i].is_selector:
                    total_selectors += 1

            old_ancestry = ancestry

            if not skip_selectors:
                result += self._print_properties(rule.properties, sc, sp, tb * len(ancestry), nl, wrap)

        if not sc and result and result[-1] == ';':
            result = result[:-1]

        for i in reversed(range(len(old_ancestry))):
            result += tb * i + '}' + nl

        return (result, total_rules, total_selectors)

    def _print_properties(self, properties, sc=True, sp=' ', _tb='', nl='\n', wrap=None):
        if wrap is None:
            textwrap.TextWrapper.wordsep_re = re.compile(r'(?<=,)(\s*)')
            if hasattr(textwrap.TextWrapper, 'wordsep_simple_re'):
                wrap = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
            else:
                wrap = textwrap.TextWrapper(break_long_words=False)
            wrap = wrap.wrap

        result = ''
        for name, value in properties:
            if value is not None:
                if nl:
                    value = (nl + _tb + _tb).join(wrap(value))
                prop = name + ':' + sp + value
            else:
                prop = name

            result += _tb + prop + ';' + nl
        return result

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
