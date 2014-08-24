from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from collections import defaultdict
from enum import Enum
import glob
from itertools import product
import logging
import os.path
import re
import sys
import warnings

import six

import scss.config as config
from scss.cssdefs import _spaces_re
from scss.cssdefs import _escape_chars_re
from scss.cssdefs import _prop_split_re
from scss.errors import SassError
from scss.expression import Calculator
from scss.functions import ALL_BUILTINS_LIBRARY
from scss.functions.compass.sprites import sprite_map
from scss.rule import BlockAtRuleHeader
from scss.rule import Namespace
from scss.rule import RuleAncestry
from scss.rule import SassRule
from scss.rule import UnparsedBlock
from scss.selector import Selector
from scss.source import SourceFile
from scss.types import Number
from scss.types import Boolean
from scss.types import String
from scss.types import List
from scss.types import Null
from scss.types import Undefined
from scss.types import Url
from scss.util import dequote
from scss.util import normalize_var  # TODO put in...  namespace maybe?

try:
    # Use C version if available
    from scss._speedups import locate_blocks
except ImportError:
    from scss._native import locate_blocks


# TODO should mention logging for the programmatic interface in the
# documentation
log = logging.getLogger(__name__)


# TODO produce this
# TODO is this a Library (can't define values), a Namespace (lot of
# semi-private functionality, no support for magic imports), or an Extension
# (doesn't exist yet)?
DEFAULT_NAMESPACE = Namespace(functions=ALL_BUILTINS_LIBRARY)


_default_rule_re = re.compile(r'(?i)\s+!default\Z')
_xcss_extends_re = re.compile(r'\s+extends\s+')


class OutputStyle(Enum):
    nested = ()
    compact = ()
    compressed = ()
    expanded = ()

    legacy = ()  # ???


class SassDeprecationWarning(UserWarning):
    # Note: DO NOT inherit from DeprecationWarning; it's turned off by default
    # in 2.7 and later!
    pass


def warn_deprecated(rule, message):
    warnings.warn(
        "{0} (at {1})".format(message, rule.file_and_line),
        SassDeprecationWarning,
        stacklevel=2,
    )


class Compiler(object):
    """A Sass compiler.  Stores settings and knows how to fire off a
    compilation.  Main entry point into compiling Sass.
    """
    def __init__(
            self, root='', search_path=('',),
            namespace=DEFAULT_NAMESPACE, output_style='nested',
            generate_source_map=False,
            live_errors=False, warn_unused_imports=False,
            super_selector='',
        ):
        """Configure a compiler.

        :param root: Directory to treat as the "project root".  Search paths
            and some custom extensions (e.g. Compass) are relative to this
            directory.  Defaults to the current directory.
        :param search_path: List of paths to search for ``@import``s, relative
            to ``root``.  Absolute and parent paths are allowed here, but
            ``@import`` will refuse to load files that aren't in one of the
            directories here.  Defaults to only the root.
        :param namespace: Global namespace to inject into compiled Sass.  See
            the Namespace documentation for details.
        :type namespace: :class:`Namespace`
        """
        # normpath() will (textually) eliminate any use of ..
        self.root = os.path.normpath(os.path.abspath(root))
        self.search_path = tuple(
            os.path.normpath(os.path.join(self.root, path))
            for path in search_path
        )

        self.namespace = namespace
        self.output_style = output_style
        self.generate_source_map = generate_source_map
        self.live_errors = live_errors
        self.warn_unused_imports = warn_unused_imports
        self.super_selector = super_selector

        self.calculator = Calculator()

    def make_compilation(self):
        return Compilation(self)

    def call_and_catch_errors(self, f, *args, **kwargs):
        """Call the given function with the given arguments.  If it succeeds,
        return its return value.  If it raises a :class:`scss.errors.SassError`
        and `live_errors` is turned on, return CSS containing a traceback and
        error message.
        """
        try:
            return f(*args, **kwargs)
        except SassError as e:
            if self.live_errors:
                # TODO should this setting also capture and display warnings?
                return e.to_css()
            else:
                raise

    def compile(self):
        compilation = self.make_compilation()
        return self.call_and_catch_errors(compilation.run)


class Compilation(object):
    """A single run of a compiler."""
    def __init__(self, compiler):
        self.compiler = compiler

        # TODO this needs a write barrier, so assignment can't overwrite what's
        # in the original namespace
        self.root_namespace = compiler.namespace

        self.sources = []
        self.source_index = {}
        self.dependency_map = defaultdict(frozenset)
        self.rules = []

    def add_source(self, source):
        if source.path in self.source_index:
            raise KeyError("Duplicate source %r" % source.path)
        self.sources.append(source)
        self.source_index[source.path] = source

    def run(self):
        # this will compile and manage rule: child objects inside of a node
        self.parse_children()

        # this will manage @extends
        self.apply_extends()

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
            # TODO i would love for the output of this function to be something
            # useful for producing stats, so this stuff can live on the Scss
            # class only
            if not exceeded and all_selectors > 4095:
                exceeded = " (IE exceeded!)"
                log.error("Maximum number of supported selectors in Internet Explorer (4095) exceeded!")
            if files > 1 and self.compiler.generate_source_map:
                if not source_file.is_real_file:
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
                        source_file.path,
                        all_selectors,
                        'selector' if all_selectors == 1 else 'selectors',
                        exceeded)
            final_cont += fcont

        return final_cont

    def parse_selectors(self, raw_selectors):
        """
        Parses out the old xCSS "foo extends bar" syntax.

        Returns a 2-tuple: a set of selectors, and a set of extended selectors.
        """
        # Fix tabs and spaces in selectors
        raw_selectors = _spaces_re.sub(' ', raw_selectors)

        parts = _xcss_extends_re.split(raw_selectors, 1)  # handle old xCSS extends
        if len(parts) > 1:
            unparsed_selectors, unsplit_parents = parts
            # Multiple `extends` are delimited by `&`
            unparsed_parents = unsplit_parents.split('&')
        else:
            unparsed_selectors, = parts
            unparsed_parents = ()

        selectors = Selector.parse_many(unparsed_selectors)
        parents = [Selector.parse_one(parent) for parent in unparsed_parents]

        return selectors, parents

    # @print_timing(3)
    def parse_children(self, scope=None):
        children = []
        root_namespace = self.root_namespace
        for source_file in self.sources:
            rule = SassRule(
                source_file=source_file,

                unparsed_contents=source_file.contents,
                namespace=root_namespace,
            )
            self.rules.append(rule)
            children.append(rule)

        for rule in children:
            self.manage_children(rule, scope)

        self._warn_unused_imports(self.rules[0])

    def _warn_unused_imports(self, rule):
        if not rule.legacy_compiler_options.get(
                'warn_unused', self.compiler.warn_unused_imports):
            return

        for name, file_and_line in rule.namespace.unused_imports():
            log.warn("Unused @import: '%s' (%s)", name, file_and_line)

    # @print_timing(4)
    def manage_children(self, rule, scope):
        try:
            self._manage_children_impl(rule, scope)
        except SassReturn:
            raise
        except SassError as e:
            e.add_rule(rule)
            raise
        except Exception as e:
            raise SassError(e, rule=rule)

    def _manage_children_impl(self, rule, scope):
        calculator = Calculator(rule.namespace)

        for c_lineno, c_property, c_codestr in locate_blocks(rule.unparsed_contents):
            block = UnparsedBlock(rule, c_lineno, c_property, c_codestr)

            ####################################################################
            # At (@) blocks
            if block.is_atrule:
                code = block.directive
                code = '_at_' + code.lower().replace(' ', '_')[1:]
                try:
                    method = getattr(self, code)
                except AttributeError:
                    if block.unparsed_contents is None:
                        rule.properties.append((block.prop, None))
                    elif scope is None:  # needs to have no scope to crawl down the nested rules
                        self._nest_at_rules(rule, scope, block)
                else:
                    method(calculator, rule, scope, block)

            ####################################################################
            # Properties
            elif block.unparsed_contents is None:
                self._get_properties(rule, scope, block)

            # Nested properties
            elif block.is_scope:
                if block.header.unscoped_value:
                    # Possibly deal with default unscoped value
                    self._get_properties(rule, scope, block)

                rule.unparsed_contents = block.unparsed_contents
                subscope = (scope or '') + block.header.scope + '-'
                self.manage_children(rule, subscope)

            ####################################################################
            # Nested rules
            elif scope is None:  # needs to have no scope to crawl down the nested rules
                self._nest_rules(rule, scope, block)

    def _at_warn(self, calculator, rule, scope, block):
        """
        Implements @warn
        """
        value = calculator.calculate(block.argument)
        log.warn(repr(value))

    def _at_print(self, calculator, rule, scope, block):
        """
        Implements @print
        """
        value = calculator.calculate(block.argument)
        sys.stderr.write("%s\n" % value)

    def _at_raw(self, calculator, rule, scope, block):
        """
        Implements @raw
        """
        value = calculator.calculate(block.argument)
        sys.stderr.write("%s\n" % repr(value))

    def _at_dump_context(self, calculator, rule, scope, block):
        """
        Implements @dump_context
        """
        sys.stderr.write("%s\n" % repr(rule.namespace._variables))

    def _at_dump_functions(self, calculator, rule, scope, block):
        """
        Implements @dump_functions
        """
        sys.stderr.write("%s\n" % repr(rule.namespace._functions))

    def _at_dump_mixins(self, calculator, rule, scope, block):
        """
        Implements @dump_mixins
        """
        sys.stderr.write("%s\n" % repr(rule.namespace._mixins))

    def _at_dump_imports(self, calculator, rule, scope, block):
        """
        Implements @dump_imports
        """
        sys.stderr.write("%s\n" % repr(rule.namespace._imports))

    def _at_dump_options(self, calculator, rule, scope, block):
        """
        Implements @dump_options
        """
        sys.stderr.write("%s\n" % repr(rule.options))

    def _at_debug(self, calculator, rule, scope, block):
        """
        Implements @debug
        """
        setting = block.argument.strip()
        if setting.lower() in ('1', 'true', 't', 'yes', 'y', 'on'):
            setting = True
        elif setting.lower() in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
            setting = False
        config.DEBUG = setting
        log.info("Debug mode is %s", 'On' if config.DEBUG else 'Off')

    def _at_pdb(self, calculator, rule, scope, block):
        """
        Implements @pdb
        """
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        pdb.set_trace()

    def _at_extend(self, calculator, rule, scope, block):
        """
        Implements @extend
        """
        from scss.selector import Selector
        selectors = calculator.apply_vars(block.argument)
        # XXX this no longer handles `&`, which is from xcss
        rule.extends_selectors.extend(Selector.parse_many(selectors))
        #rule.extends_selectors.update(p.strip() for p in selectors.replace(',', '&').split('&'))
        #rule.extends_selectors.discard('')

    def _at_return(self, calculator, rule, scope, block):
        """
        Implements @return
        """
        # TODO should assert this only happens within a @function
        ret = calculator.calculate(block.argument)
        raise SassReturn(ret)

    # @print_timing(10)
    def _at_option(self, calculator, rule, scope, block):
        """
        Implements @option
        """
        # TODO This only actually supports "style" (which only really makes
        # sense as the first thing in a single input file) or "warn_unused"
        # (which only makes sense at file level /at best/).  Explore either
        # replacing this with a better mechanism or dropping it entirely.
        # Note also that all rules share the same underlying legacy option
        # dict, so the rules aren't even lexically scoped like you might think,
        # and @importing a file can change the compiler!  That seems totally
        # wrong.
        for option in block.argument.split(','):
            key, colon, value = option.partition(':')
            key = key.strip().lower().replace('-', '_')
            value = value.strip().lower()

            if value in ('1', 'true', 't', 'yes', 'y', 'on'):
                value = True
            elif value in ('0', 'false', 'f', 'no', 'n', 'off', 'undefined'):
                value = False
            elif not colon:
                value = True

            if key == 'compress':
                warn_deprecated(
                    rule,
                    "The 'compress' @option is deprecated.  "
                    "Please use 'style' instead."
                )
                key = 'style'
                value = 'compressed' if value else 'legacy'

            if key in ('short_colors', 'reverse_colors'):
                warn_deprecated(
                    rule,
                    "The '{0}' @option no longer has any effect."
                    .format(key),
                )
                return
            elif key == 'style':
                try:
                    OutputStyle[value]
                except KeyError:
                    raise SassError("No such output style: {0}".format(value))
            elif key in ('warn_unused', 'control_scoping'):
                # TODO deprecate control_scoping?  or add it to compiler?
                if not isinstance(value, bool):
                    raise SassError("The '{0}' @option requires a bool, not {1!r}".format(key, value))
            else:
                raise SassError("Unknown @option: {0}".format(key))

            rule.legacy_compiler_options[key] = value

    def _get_funct_def(self, rule, calculator, argument):
        funct, lpar, argstr = argument.partition('(')
        funct = calculator.do_glob_math(funct)
        funct = normalize_var(funct.strip())
        argstr = argstr.strip()

        # Parse arguments with the argspec rule
        if lpar:
            if not argstr.endswith(')'):
                raise SyntaxError("Expected ')', found end of line for %s (%s)" % (funct, rule.file_and_line))
            argstr = argstr[:-1].strip()
        else:
            # Whoops, no parens at all.  That's like calling with no arguments.
            argstr = ''

        argstr = calculator.do_glob_math(argstr)
        argspec_node = calculator.parse_expression(argstr, target='goal_argspec')
        return funct, argspec_node

    def _populate_namespace_from_call(self, name, callee_namespace, mixin, args, kwargs):
        # Mutation protection
        args = list(args)
        kwargs = dict(kwargs)

        #m_params = mixin[0]
        #m_defaults = mixin[1]
        #m_codestr = mixin[2]
        pristine_callee_namespace = mixin[3]
        callee_argspec = mixin[4]
        import_key = mixin[5]

        callee_calculator = Calculator(callee_namespace)

        # Populate the mixin/function's namespace with its arguments
        for var_name, node in callee_argspec.iter_def_argspec():
            if args:
                # If there are positional arguments left, use the first
                value = args.pop(0)
            elif var_name in kwargs:
                # Try keyword arguments
                value = kwargs.pop(var_name)
            elif node is not None:
                # OK, there's a default argument; try that
                # DEVIATION: this allows argument defaults to refer to earlier
                # argument values
                value = node.evaluate(callee_calculator, divide=True)
            else:
                # TODO this should raise
                value = Undefined()

            callee_namespace.set_variable(var_name, value, local_only=True)

        if callee_argspec.slurp:
            # Slurpy var gets whatever is left
            callee_namespace.set_variable(
                callee_argspec.slurp.name,
                List(args, use_comma=True))
            args = []
        elif callee_argspec.inject:
            # Callee namespace gets all the extra kwargs whether declared or
            # not
            for var_name, value in kwargs.items():
                callee_namespace.set_variable(var_name, value, local_only=True)
            kwargs = {}

        # TODO would be nice to say where the mixin/function came from
        if kwargs:
            raise NameError("%s has no such argument %s" % (name, kwargs.keys()[0]))

        if args:
            raise NameError("%s received extra arguments: %r" % (name, args))

        pristine_callee_namespace.use_import(import_key)
        return callee_namespace

    # @print_timing(10)
    def _at_function(self, calculator, rule, scope, block):
        """
        Implements @mixin and @function
        """
        if not block.argument:
            raise SyntaxError("%s requires a function name (%s)" % (block.directive, rule.file_and_line))

        funct, argspec_node = self._get_funct_def(rule, calculator, block.argument)

        defaults = {}
        new_params = []

        for var_name, default in argspec_node.iter_def_argspec():
            new_params.append(var_name)
            if default is not None:
                defaults[var_name] = default

        # TODO a function or mixin is re-parsed every time it's called; there's
        # no AST for anything but expressions  :(
        mixin = [rule.source_file, block.lineno, block.unparsed_contents, rule.namespace, argspec_node, rule.source_file]
        if block.directive == '@function':
            def _call(mixin):
                def __call(namespace, *args, **kwargs):
                    source_file = mixin[0]
                    lineno = mixin[1]
                    m_codestr = mixin[2]
                    pristine_callee_namespace = mixin[3]
                    callee_namespace = pristine_callee_namespace.derive()

                    # TODO CallOp converts Sass names to Python names, so we
                    # have to convert them back to Sass names.  would be nice
                    # to avoid this back-and-forth somehow
                    kwargs = dict(
                        (normalize_var('$' + key), value)
                        for (key, value) in kwargs.items())

                    self._populate_namespace_from_call(
                        "Function {0}".format(funct),
                        callee_namespace, mixin, args, kwargs)

                    _rule = SassRule(
                        source_file=source_file,
                        lineno=lineno,
                        unparsed_contents=m_codestr,
                        namespace=callee_namespace,

                        # rule
                        import_key=rule.import_key,
                        legacy_compiler_options=rule.legacy_compiler_options,
                        options=rule.options,
                        properties=rule.properties,
                        extends_selectors=rule.extends_selectors,
                        ancestry=rule.ancestry,
                        nested=rule.nested,
                    )
                    try:
                        self.manage_children(_rule, scope)
                    except SassReturn as e:
                        return e.retval
                    else:
                        return Null()
                return __call
            _mixin = _call(mixin)
            _mixin.mixin = mixin
            mixin = _mixin

        if block.directive == '@mixin':
            add = rule.namespace.set_mixin
        elif block.directive == '@function':
            add = rule.namespace.set_function

        # Register the mixin for every possible arity it takes
        if argspec_node.slurp or argspec_node.inject:
            add(funct, None, mixin)
        else:
            while len(new_params):
                add(funct, len(new_params), mixin)
                param = new_params.pop()
                if param not in defaults:
                    break
            if not new_params:
                add(funct, 0, mixin)
    _at_mixin = _at_function

    # @print_timing(10)
    def _at_include(self, calculator, rule, scope, block):
        """
        Implements @include, for @mixins
        """
        caller_namespace = rule.namespace
        caller_calculator = Calculator(caller_namespace)
        funct, caller_argspec = self._get_funct_def(rule, caller_calculator, block.argument)

        # Render the passed arguments, using the caller's namespace
        args, kwargs = caller_argspec.evaluate_call_args(caller_calculator)

        argc = len(args) + len(kwargs)
        try:
            mixin = caller_namespace.mixin(funct, argc)
        except KeyError:
            try:
                # TODO maybe? don't do this, once '...' works
                # Fallback to single parameter:
                mixin = caller_namespace.mixin(funct, 1)
            except KeyError:
                log.error("Mixin not found: %s:%d (%s)", funct, argc, rule.file_and_line, extra={'stack': True})
                return
            else:
                args = [List(args, use_comma=True)]
                # TODO what happens to kwargs?

        source_file = mixin[0]
        lineno = mixin[1]
        m_codestr = mixin[2]
        pristine_callee_namespace = mixin[3]
        callee_argspec = mixin[4]
        if caller_argspec.inject and callee_argspec.inject:
            # DEVIATION: Pass the ENTIRE local namespace to the mixin (yikes)
            callee_namespace = Namespace.derive_from(
                caller_namespace,
                pristine_callee_namespace)
        else:
            callee_namespace = pristine_callee_namespace.derive()

        self._populate_namespace_from_call(
            "Mixin {0}".format(funct),
            callee_namespace, mixin, args, kwargs)

        _rule = SassRule(
            # These must be file and line in which the @include occurs
            source_file=rule.source_file,
            lineno=rule.lineno,

            # These must be file and line in which the @mixin was defined
            from_source_file=source_file,
            from_lineno=lineno,

            unparsed_contents=m_codestr,
            namespace=callee_namespace,

            # rule
            import_key=rule.import_key,
            legacy_compiler_options=rule.legacy_compiler_options,
            options=rule.options,
            properties=rule.properties,
            extends_selectors=rule.extends_selectors,
            ancestry=rule.ancestry,
            nested=rule.nested,
        )

        _rule.options['@content'] = block.unparsed_contents
        self.manage_children(_rule, scope)

    # @print_timing(10)
    def _at_content(self, calculator, rule, scope, block):
        """
        Implements @content
        """
        if '@content' not in rule.options:
            log.error("Content string not found for @content (%s)", rule.file_and_line)
        rule.unparsed_contents = rule.options.pop('@content', '')
        self.manage_children(rule, scope)

    # @print_timing(10)
    def _at_import(self, calculator, rule, scope, block):
        """
        Implements @import
        Load and import mixins and functions and rules
        """
        # TODO it would be neat to opt into warning that you're using
        # values/functions from a file you didn't explicitly import
        # TODO base-level directives, like @mixin or @charset, aren't allowed
        # to be @imported into a nested block
        # TODO i'm not sure we disallow them nested in the first place
        # TODO @import is disallowed within mixins, control directives
        # TODO @import doesn't take a block -- that's probably an issue with a
        # lot of our directives

        # TODO if there's any #{}-interpolation in the AST, this should become
        # a CSS import (though in practice Ruby only even evaluates it in url()
        # -- in a string it's literal!)

        sass_paths = calculator.evaluate_expression(block.argument)
        css_imports = []

        for sass_path in sass_paths:
            # These are the rules for when an @import is interpreted as a CSS
            # import:
            if (
                    # If it's a url()
                    isinstance(sass_path, Url) or
                    # If it's not a string (including `"foo" screen`, a List)
                    not isinstance(sass_path, String) or
                    # If the filename begins with an http protocol
                    sass_path.value.startswith(('http://', 'https://')) or
                    # If the filename ends with .css
                    sass_path.value.endswith('.css')):
                css_imports.append(sass_path.render(compress=False))
                continue

            # Should be left with a plain String
            name = sass_path.value

            source = None
            try:
                path = self._find_import(rule, name)
            except IOError:
                # Maybe do a special import instead
                generated_code = self._at_magic_import(
                    calculator, rule, scope, block)
                if generated_code is None:
                    raise

                source = SourceFile.from_string(generated_code)
            else:
                if path not in self.source_index:
                    self.add_source(SourceFile.from_filename(path))
                source = self.source_index[path]

            if rule.namespace.has_import(source):
                # If already imported in this scope, skip
                # TODO this might not be right -- consider if you @import a
                # file at top level, then @import it inside a selector block!
                continue

            _rule = SassRule(
                source_file=source,
                lineno=block.lineno,
                unparsed_contents=source.contents,

                # rule
                legacy_compiler_options=rule.legacy_compiler_options,
                options=rule.options,
                properties=rule.properties,
                extends_selectors=rule.extends_selectors,
                ancestry=rule.ancestry,
                namespace=rule.namespace,
            )
            rule.namespace.add_import(source, rule)
            self.manage_children(_rule, scope)

        # Create a new @import rule for each import determined to be CSS
        for import_ in css_imports:
            # TODO this seems extremely janky (surely we should create an
            # actual new Rule), but the CSS rendering doesn't understand how to
            # print rules without blocks
            rule.properties.append(('@import ' + import_, None))

    def _find_import(self, rule, name, skip=None):
        """Find the file referred to by an @import.

        Takes a name from an @import and returns an absolute path, or None.
        """
        name, ext = os.path.splitext(name)
        if ext:
            search_exts = [ext]
        else:
            search_exts = ['.scss', '.sass']

        dirname, basename = os.path.split(name)

        # Search relative to the importing file first
        search_path = [os.path.dirname(rule.source_file.path)]
        search_path.extend(self.compiler.search_path)

        for prefix, suffix in product(('_', ''), search_exts):
            filename = prefix + basename + suffix
            for directory in search_path:
                path = os.path.normpath(
                    os.path.join(directory, dirname, filename))

                if path == rule.source_file.path:
                    # Avoid self-import
                    # TODO is this what ruby does?
                    continue

                if not os.path.exists(path):
                    continue

                # Ensure that no one used .. to escape the search path
                for valid_path in self.compiler.search_path:
                    rel = os.path.relpath(path, start=valid_path)
                    if not rel.startswith('../'):
                        break
                else:
                    continue

                # All good!
                return path

        raise IOError(
            "Can't find a file to import for {0!r}\n"
            "Search path:\n{1}".format(
                name,
                ''.join("    " + dir_ + "\n" for dir_ in search_path),
            )
        )

    # @print_timing(10)
    def _at_magic_import(self, calculator, rule, scope, block):
        """
        Implements @import for sprite-maps
        Imports magic sprite map directories
        """
        # TODO check that the found file is actually under the root
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

        def setdefault(var, val):
            _var = '$' + map_name + '-' + var
            if _var in rule.context:
                kwargs[var] = calculator.interpolate(rule.context[_var], rule, self._library)
            else:
                rule.context[_var] = val
                kwargs[var] = calculator.interpolate(val, rule, self._library)
            return rule.context[_var]

        setdefault('sprite-base-class', String('.' + map_name + '-sprite', quotes=None))
        setdefault('sprite-dimensions', Boolean(False))
        position = setdefault('position', Number(0, '%'))
        spacing = setdefault('spacing', Number(0))
        repeat = setdefault('repeat', String('no-repeat', quotes=None))
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

    # @print_timing(10)
    def _at_if(self, calculator, rule, scope, block):
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

        condition = calculator.calculate(block.argument)
        if condition:
            inner_rule = rule.copy()
            inner_rule.unparsed_contents = block.unparsed_contents
            if not rule.legacy_compiler_options.get('control_scoping', config.CONTROL_SCOPING):  # TODO: maybe make this scoping mode for contol structures as the default as a default deviation
                # DEVIATION: Allow not creating a new namespace
                inner_rule.namespace = rule.namespace
            self.manage_children(inner_rule, scope)
        rule.options['@if'] = condition
    _at_else_if = _at_if

    # @print_timing(10)
    def _at_else(self, calculator, rule, scope, block):
        """
        Implements @else
        """
        if '@if' not in rule.options:
            log.error("@else with no @if (%s)", rule.file_and_line)
        val = rule.options.pop('@if', True)
        if not val:
            inner_rule = rule.copy()
            inner_rule.unparsed_contents = block.unparsed_contents
            inner_rule.namespace = rule.namespace  # DEVIATION: Commenting this line gives the Sass bahavior
            inner_rule.unparsed_contents = block.unparsed_contents
            self.manage_children(inner_rule, scope)

    # @print_timing(10)
    def _at_for(self, calculator, rule, scope, block):
        """
        Implements @for
        """
        var, _, name = block.argument.partition(' from ')
        frm, _, through = name.partition(' through ')
        if through:
            inclusive = True
        else:
            inclusive = False
            frm, _, through = frm.partition(' to ')
        frm = calculator.calculate(frm)
        through = calculator.calculate(through)
        try:
            frm = int(float(frm))
            through = int(float(through))
        except ValueError:
            return

        if frm > through:
            # DEVIATION: allow reversed '@for .. from .. through' (same as enumerate() and range())
            frm, through = through, frm
            rev = reversed
        else:
            rev = lambda x: x
        var = var.strip()
        var = calculator.do_glob_math(var)
        var = normalize_var(var)

        inner_rule = rule.copy()
        inner_rule.unparsed_contents = block.unparsed_contents
        if not rule.legacy_compiler_options.get('control_scoping', config.CONTROL_SCOPING):  # TODO: maybe make this scoping mode for contol structures as the default as a default deviation
            # DEVIATION: Allow not creating a new namespace
            inner_rule.namespace = rule.namespace

        if inclusive:
            through += 1
        for i in rev(range(frm, through)):
            inner_rule.namespace.set_variable(var, Number(i))
            self.manage_children(inner_rule, scope)

    # @print_timing(10)
    def _at_each(self, calculator, rule, scope, block):
        """
        Implements @each
        """
        varstring, _, valuestring = block.argument.partition(' in ')
        values = calculator.calculate(valuestring)
        if not values:
            return

        varlist = [
            normalize_var(calculator.do_glob_math(var.strip()))
            # TODO use list parsing here
            for var in varstring.split(",")
        ]

        # `@each $foo, in $bar` unpacks, but `@each $foo in $bar` does not!
        unpack = len(varlist) > 1
        if not varlist[-1]:
            varlist.pop()

        inner_rule = rule.copy()
        inner_rule.unparsed_contents = block.unparsed_contents
        if not rule.legacy_compiler_options.get('control_scoping', config.CONTROL_SCOPING):  # TODO: maybe make this scoping mode for contol structures as the default as a default deviation
            # DEVIATION: Allow not creating a new namespace
            inner_rule.namespace = rule.namespace

        for v in List.from_maybe(values):
            if unpack:
                v = List.from_maybe(v)
                for i, var in enumerate(varlist):
                    if i >= len(v):
                        value = Null()
                    else:
                        value = v[i]
                    inner_rule.namespace.set_variable(var, value)
            else:
                inner_rule.namespace.set_variable(varlist[0], v)
            self.manage_children(inner_rule, scope)

    # @print_timing(10)
    def _at_while(self, calculator, rule, scope, block):
        """
        Implements @while
        """
        first_condition = condition = calculator.calculate(block.argument)
        while condition:
            inner_rule = rule.copy()
            inner_rule.unparsed_contents = block.unparsed_contents
            if not rule.legacy_compiler_options.get('control_scoping', config.CONTROL_SCOPING):  # TODO: maybe make this scoping mode for contol structures as the default as a default deviation
                # DEVIATION: Allow not creating a new namespace
                inner_rule.namespace = rule.namespace
            self.manage_children(inner_rule, scope)
            condition = calculator.calculate(block.argument)
        rule.options['@if'] = first_condition

    # @print_timing(10)
    def _at_variables(self, calculator, rule, scope, block):
        """
        Implements @variables and @vars
        """
        _rule = rule.copy()
        _rule.unparsed_contents = block.unparsed_contents
        _rule.namespace = rule.namespace
        _rule.properties = {}
        self.manage_children(_rule, scope)
        for name, value in _rule.properties.items():
            rule.namespace.set_variable(name, value)
    _at_vars = _at_variables

    # @print_timing(10)
    def _get_properties(self, rule, scope, block):
        """
        Implements properties and variables extraction and assignment
        """
        prop, raw_value = (_prop_split_re.split(block.prop, 1) + [None])[:2]
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
        if raw_value is not None:
            raw_value = raw_value.strip()
            if prop.startswith('$'):
                raw_value, subs = _default_rule_re.subn('', raw_value)  # handle !default
                if subs:
                    is_default = True

        _prop = (scope or '') + prop
        if is_var or prop.startswith('$') and raw_value is not None:
            # Variable assignment
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

                # Variable assignment is an expression, so it always performs
                # real division
                value = calculator.calculate(raw_value, divide=True)
                rule.namespace.set_variable(_prop, value)
        else:
            # Regular property destined for output
            _prop = calculator.apply_vars(_prop)
            if raw_value is None:
                value = None
            else:
                value = calculator.calculate(raw_value)

            if value is None:
                pass
            elif isinstance(value, six.string_types):
                # TODO kill this branch
                pass
            else:
                style = rule.legacy_compiler_options.get(
                    'style', self.compiler.output_style)
                compress = style == 'compressed'
                value = value.render(compress=compress)

            rule.properties.append((_prop, value))

    # @print_timing(10)
    def _nest_at_rules(self, rule, scope, block):
        """
        Implements @-blocks
        """
        # TODO handle @charset, probably?
        # Interpolate the current block
        # TODO this seems like it should be done in the block header.  and more
        # generally?
        calculator = Calculator(rule.namespace)
        if block.header.argument:
            block.header.argument = calculator.apply_vars(block.header.argument)

        # TODO merge into RuleAncestry
        new_ancestry = list(rule.ancestry.headers)
        if block.directive == '@media' and new_ancestry:
            for i, header in reversed(list(enumerate(new_ancestry))):
                if header.is_selector:
                    continue
                elif header.directive == '@media':
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

        rule.descendants += 1
        new_rule = SassRule(
            source_file=rule.source_file,
            import_key=rule.import_key,
            lineno=block.lineno,
            unparsed_contents=block.unparsed_contents,

            legacy_compiler_options=rule.legacy_compiler_options,
            options=rule.options.copy(),
            #properties
            #extends_selectors
            ancestry=RuleAncestry(new_ancestry),

            namespace=rule.namespace.derive(),
            nested=rule.nested + 1,
        )
        self.rules.append(new_rule)
        rule.namespace.use_import(rule.source_file)
        self.manage_children(new_rule, scope)

        self._warn_unused_imports(new_rule)

    # @print_timing(10)
    def _nest_rules(self, rule, scope, block):
        """
        Implements Nested CSS rules
        """
        calculator = Calculator(rule.namespace)
        raw_selectors = calculator.do_glob_math(block.prop)
        # DEVIATION: ruby sass doesn't support bare variables in selectors
        raw_selectors = calculator.apply_vars(raw_selectors)
        c_selectors, c_parents = self.parse_selectors(raw_selectors)
        if c_parents:
            warn_deprecated(
                rule,
                "The XCSS 'a extends b' syntax is deprecated.  "
                "Use 'a { @extend b; }' instead."
            )

        new_ancestry = rule.ancestry.with_nested_selectors(c_selectors)

        rule.descendants += 1
        new_rule = SassRule(
            source_file=rule.source_file,
            import_key=rule.import_key,
            lineno=block.lineno,
            unparsed_contents=block.unparsed_contents,

            legacy_compiler_options=rule.legacy_compiler_options,
            options=rule.options.copy(),
            #properties
            extends_selectors=c_parents,
            ancestry=new_ancestry,

            namespace=rule.namespace.derive(),
            nested=rule.nested + 1,
        )
        self.rules.append(new_rule)
        rule.namespace.use_import(rule.source_file)
        self.manage_children(new_rule, scope)

        self._warn_unused_imports(new_rule)

    # @print_timing(3)
    def apply_extends(self):
        """Run through the given rules and translate all the pending @extends
        declarations into real selectors on parent rules.

        The list is modified in-place and also sorted in dependency order.
        """
        # Game plan: for each rule that has an @extend, add its selectors to
        # every rule that matches that @extend.
        # First, rig a way to find arbitrary selectors quickly.  Most selectors
        # revolve around elements, classes, and IDs, so parse those out and use
        # them as a rough key.  Ignore order and duplication for now.
        key_to_selectors = defaultdict(set)
        selector_to_rules = defaultdict(list)
        for rule in self.rules:
            for selector in rule.selectors:
                for key in selector.lookup_key():
                    key_to_selectors[key].add(selector)
                selector_to_rules[selector].append(rule)

        # Now go through all the rules with an @extends and find their parent
        # rules.
        for rule in self.rules:
            for selector in rule.extends_selectors:
                # This is a little dirty.  intersection isn't a class method.
                # Don't think about it too much.
                candidates = set.intersection(*(
                    key_to_selectors[key] for key in selector.lookup_key()))
                extendable_selectors = [
                    candidate for candidate in candidates
                    if candidate.is_superset_of(selector)]

                if not extendable_selectors:
                    # TODO should be fatal, unless !optional given
                    log.warn(
                        "Can't find any matching rules to extend: %s"
                        % selector.render())
                    continue

                # Armed with a set of selectors that this rule can extend, do
                # some substitution and modify the appropriate parent rules
                for extendable_selector in extendable_selectors:
                    # list() shields us from problems mutating the list within
                    # this loop, which can happen in the case of @extend loops
                    parent_rules = list(selector_to_rules[extendable_selector])
                    for parent_rule in parent_rules:
                        if parent_rule is rule:
                            # Don't extend oneself
                            continue

                        more_parent_selectors = []

                        for rule_selector in rule.selectors:
                            more_parent_selectors.extend(
                                extendable_selector.substitute(
                                    selector, rule_selector))

                        for parent in more_parent_selectors:
                            # Update indices, in case any later rules try to
                            # extend this one
                            for key in parent.lookup_key():
                                key_to_selectors[key].add(parent)
                            # TODO this could lead to duplicates?  maybe should
                            # be a set too
                            selector_to_rules[parent].append(parent_rule)

                        parent_rule.ancestry = (
                            parent_rule.ancestry.with_more_selectors(
                                more_parent_selectors))

        # Remove placeholder-only rules
        self.rules = [rule for rule in self.rules if not rule.is_pure_placeholder]

    # @print_timing(3)
    def parse_properties(self):
        css_files = []
        seen_files = set()
        rules_by_file = {}

        for rule in self.rules:
            source_file = rule.source_file
            rules_by_file.setdefault(source_file, []).append(rule)

            if rule.is_empty:
                continue

            if source_file not in seen_files:
                seen_files.add(source_file)
                css_files.append(source_file)

        return rules_by_file, css_files

    # @print_timing(3)
    def create_css(self, rules):
        """
        Generate the final CSS string
        """
        style = rules[0].legacy_compiler_options.get(
            'style', self.compiler.output_style)
        debug_info = self.compiler.generate_source_map

        if style == 'legacy':
            sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg = True, ' ', '  ', False, '', '\n', '\n', '\n', debug_info
        elif style == 'compressed':
            sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg = False, '', '', False, '', '', '', '', False
        elif style == 'compact':
            sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg = True, ' ', '', False, '\n', ' ', '\n', ' ', debug_info
        elif style == 'expanded':
            sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg = True, ' ', '  ', False, '\n', '\n', '\n', '\n', debug_info
        else:  # if style == 'nested':
            sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg = True, ' ', '  ', True, '\n', '\n', '\n', ' ', debug_info

        return self._create_css(rules, sc, sp, tb, nst, srnl, nl, rnl, lnl, dbg)

    def _textwrap(self, txt, width=70):
        if not hasattr(self, '_textwrap_wordsep_re'):
            self._textwrap_wordsep_re = re.compile(r'(?<=,)\s+')
            self._textwrap_strings_re = re.compile(r'''(["'])(?:(?!\1)[^\\]|\\.)*\1''')

        # First, remove commas from anything within strings (marking commas as \0):
        def _repl(m):
            ori = m.group(0)
            fin = ori.replace(',', '\0')
            if ori != fin:
                subs[fin] = ori
            return fin
        subs = {}
        txt = self._textwrap_strings_re.sub(_repl, txt)

        # Mark split points for word separators using (marking spaces with \1):
        txt = self._textwrap_wordsep_re.sub('\1', txt)

        # Replace all the strings back:
        for fin, ori in subs.items():
            txt = txt.replace(fin, ori)

        # Split in chunks:
        chunks = txt.split('\1')

        # Break in lines of at most long_width width appending chunks:
        ln = ''
        lines = []
        long_width = int(width * 1.2)
        for chunk in chunks:
            _ln = ln + ' ' if ln else ''
            _ln += chunk
            if len(ln) >= width or len(_ln) >= long_width:
                if ln:
                    lines.append(ln)
                _ln = chunk
            ln = _ln
        if ln:
            lines.append(ln)

        return lines

    def _create_css(self, rules, sc=True, sp=' ', tb='  ', nst=True, srnl='\n', nl='\n', rnl='\n', lnl='', debug_info=False):
        super_selector = self.compiler.super_selector
        if super_selector:
            super_selector += ' '

        skip_selectors = False

        prev_ancestry_headers = []

        total_rules = 0
        total_selectors = 0

        result = ''
        dangling_property = False
        separate = False
        nesting = current_nesting = last_nesting = -1 if nst else 0
        nesting_stack = []
        for rule in rules:
            nested = rule.nested
            if nested <= 1:
                separate = True

            if nst:
                last_nesting = current_nesting
                current_nesting = nested

                delta_nesting = current_nesting - last_nesting
                if delta_nesting > 0:
                    nesting_stack += [nesting] * delta_nesting
                elif delta_nesting < 0:
                    nesting_stack = nesting_stack[:delta_nesting]
                    nesting = nesting_stack[-1]

            if rule.is_empty:
                continue

            if nst:
                nesting += 1

            ancestry = rule.ancestry
            ancestry_len = len(ancestry)

            first_mismatch = 0
            for i, (old_header, new_header) in enumerate(zip(prev_ancestry_headers, ancestry.headers)):
                if old_header != new_header:
                    first_mismatch = i
                    break

            # When sc is False, sets of properties are printed without a
            # trailing semicolon.  If the previous block isn't being closed,
            # that trailing semicolon needs adding in to separate the last
            # property from the next rule.
            if not sc and dangling_property and first_mismatch >= len(prev_ancestry_headers):
                result += ';'

            # Close blocks and outdent as necessary
            for i in range(len(prev_ancestry_headers), first_mismatch, -1):
                result += tb * (i - 1) + '}' + rnl

            # Open new blocks as necessary
            for i in range(first_mismatch, ancestry_len):
                header = ancestry.headers[i]

                if separate:
                    if result:
                        result += srnl
                    separate = False
                if debug_info:
                    def _print_debug_info(filename, lineno):
                        if debug_info == 'comments':
                            result = tb * (i + nesting) + "/* file: %s, line: %s */" % (filename, lineno) + nl
                        else:
                            filename = _escape_chars_re.sub(r'\\\1', filename)
                            result = tb * (i + nesting) + "@media -sass-debug-info{filename{font-family:file\:\/\/%s}line{font-family:\\00003%s}}" % (filename, lineno) + nl
                        return result

                    if rule.lineno and rule.source_file:
                        result += _print_debug_info(rule.source_file.path, rule.lineno)

                    if rule.from_lineno and rule.from_source_file:
                        result += _print_debug_info(rule.from_source_file.path, rule.from_lineno)

                if header.is_selector:
                    header_string = header.render(sep=',' + sp, super_selector=super_selector)
                    if nl:
                        header_string = (nl + tb * (i + nesting)).join(self._textwrap(header_string))
                else:
                    header_string = header.render()
                result += tb * (i + nesting) + header_string + sp + '{' + nl

                total_rules += 1
                if header.is_selector:
                    total_selectors += 1

            prev_ancestry_headers = ancestry.headers
            dangling_property = False

            if not skip_selectors:
                result += self._print_properties(rule.properties, sc, sp, tb * (ancestry_len + nesting), nl, lnl)
                dangling_property = True

        # Close all remaining blocks
        for i in reversed(range(len(prev_ancestry_headers))):
            result += tb * i + '}' + rnl

        return (result, total_rules, total_selectors)

    def _print_properties(self, properties, sc=True, sp=' ', tb='', nl='\n', lnl=' '):
        result = ''
        last_prop_index = len(properties) - 1
        for i, (name, value) in enumerate(properties):
            if value is None:
                prop = name
            elif value:
                if nl:
                    value = (nl + tb + tb).join(self._textwrap(value))
                prop = name + ':' + sp + value
            else:
                # Empty string means there's supposed to be a value but it
                # evaluated to nothing; skip this
                # TODO interacts poorly with last_prop_index
                continue

            if i == last_prop_index:
                if sc:
                    result += tb + prop + ';' + lnl
                else:
                    result += tb + prop + lnl
            else:
                result += tb + prop + ';' + nl
        return result


# TODO: this should inherit from SassError, but can't, because that assumes
# it's wrapping another error.  fix this with the exception hierarchy
class SassReturn(Exception):
    """Special control-flow exception used to hop up the stack from a Sass
    function's ``@return``.
    """
    def __init__(self, retval):
        self.retval = retval
        Exception.__init__(self)

    def __str__(self):
        return "Returning {0!r}".format(self.retval)
