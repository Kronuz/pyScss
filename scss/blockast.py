from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import logging

try:
    from collections import OrderedDict
except ImportError:
    # Backport
    from ordereddict import OrderedDict

from scss.errors import SassParseError
from scss.expression import Calculator
from scss.namespace import Namespace
from scss.types import List
from scss.types import Null
from scss.types import Arglist
from scss.types import String
from scss.types import Undefined
from scss.util import normalize_var  # TODO put in...  namespace maybe?


log = logging.getLogger(__name__)


# TODO currently none of these know where they come from; whoops?

class Node(object):
    is_block = False
    """Whether this node is a block, i.e. has children."""

    def __repr__(self):
        return "<{0} {1!r}>".format(
            type(self).__name__,
            repr(self.__dict__)[:100],
        )

    def add_child(self, node):
        raise RuntimeError("Only blocks can have children")

    def evaluate(self, namespace):
        raise NotImplementedError


class Declaration(Node):
    pass


class Assignment(Declaration):
    def __init__(self, name, value_expression):
        self.name = name
        self.value_expression = value_expression

    @classmethod
    def parse(cls, name, value):
        # TODO pull off !default, !global
        # TODO interp-parse the name?  is that a thing?

        # TODO this is a bit naughty, but uses no state except the ast_cache --
        # which should maybe be in the Compiler anyway...?
        value_expression = Calculator().parse_expression(value)

        return cls(name, value_expression)

    def evaluate(self, compilation):
        value = self.value_expression.evaluate(compilation.current_calculator)
        compilation.current_namespace.set_variable(self.name, value)


class CSSDeclaration(Declaration):
    def __init__(self, prop_expression, value_expression):
        self.prop_expression = prop_expression
        self.value_expression = value_expression

    @classmethod
    def parse(cls, prop, value):
        # TODO this is a bit naughty, but uses no state except the ast_cache --
        # which should maybe be in the Compiler anyway...?
        prop_expression = Calculator().parse_interpolations(prop)
        value_expression = Calculator().parse_expression(value)

        return cls(prop_expression, value_expression)

    def evaluate(self, compilation):
        prop = self.prop_expression.evaluate(compilation.current_calculator)
        value = self.value_expression.evaluate(compilation.current_calculator)
        # TODO this is where source maps would need to get their info
        compilation.add_declaration(prop.value, value)


class _AtRuleMixin(object):

    is_atrule = True

    directive = None
    """The name of the at-rule, including the @."""

    argument = None
    """Any text between the at-rule and the opening brace."""
    # TODO should this be parsed?  can't be for unknown rules...

    def __init__(self, directive, argument):
        super(_AtRuleMixin, self).__init__()
        self.directive = directive
        self.argument = argument

    def __repr__(self):
        return "<%s %r %r>" % (type(self).__name__, self.directive, self.argument)

    def render(self):
        if self.argument:
            return "%s %s" % (self.directive, self.argument)
        else:
            return self.directive

    def evaluate(*args):
        log.warn("Not yet implemented")


class AtRule(_AtRuleMixin, Node):
    """An at-rule with no children, e.g. ``@import``."""


class Block(Node):
    """Base class for a block -- an arbitrary header followed by a list of
    children delimited with curly braces.
    """
    is_block = True

    def __init__(self):
        self.children = []

    def add_child(self, node):
        self.children.append(node)


class SelectorBlock(Block):
    """A regular CSS-like block, with selectors for the header and a list of
    zero or more declarations.  This is the most likely kind of node to end up
    as CSS output.
    """
    is_selector = True

    def __init__(self, selector_string):
        super(SelectorBlock, self).__init__()
        # NOTE: This can't really be parsed as a selector yet, since it might
        # have interpolations that alter the selector parsing.
        # TODO eager-parse if there's no #{ in it?
        self.selector_string = selector_string

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, self.selector_string)

    def evaluate(self, compilation):
        # TODO parse earlier; need a rule that ONLY looks for interps
        plain_selector_string = compilation.current_calculator.do_glob_math(self.selector_string)
        from .selector import Selector
        selector = Selector.parse_many(plain_selector_string)
        with compilation.nest_selector(selector):
            # TODO un-recurse
            for child in self.children:
                child.evaluate(compilation)


class AtRuleBlock(_AtRuleMixin, Block):
    """An at-rule followed by a block, e.g. ``@media``."""


class ScopeBlock(Block):
    """A block that looks like ``background: { color: white; }``.  This is
    Sass shorthand for setting multiple properties with a common prefix.
    """
    is_scope = True

    def __init__(self, scope, unscoped_value):
        super(ScopeBlock, self).__init__()
        self.scope = scope

        if unscoped_value:
            self.unscoped_value = unscoped_value
        else:
            self.unscoped_value = None

    def add_child(self, node):
        # TODO pretty sure you can't, say, nest a scope block inside a scope
        # block
        super(ScopeBlock, self).add_child(node)


class FileBlock(Block):
    """Special block representing the entire contents of a file.  ONLY has
    children; there's no header.
    """

    # TODO can only contain blocks

    def evaluate(self, compilation):
        for child in self.children:
            child.evaluate(compilation)


class AtEachBlock(AtRuleBlock):
    directive = '@each'

    def __init__(self, variable_names, expression, unpack):
        # TODO fix parent to not assign to directive/argument and use super
        # here
        Block.__init__(self)

        self.variable_names = variable_names
        self.expression = expression
        self.unpack = unpack

    @classmethod
    def parse(cls, argument):
        # TODO this is flaky; need a real grammar rule here
        varstring, _, valuestring = argument.partition(' in ')
        # TODO this is a bit naughty, but uses no state except the ast_cache --
        # which should maybe be in the Compiler anyway...?
        expression = Calculator().parse_expression(valuestring)

        variable_names = [
            # TODO broke support for #{} inside the var name
            normalize_var(var.strip())
            # TODO use list parsing here
            for var in varstring.split(",")
        ]

        # `@each $foo, in $bar` unpacks, but `@each $foo in $bar` does not!
        unpack = len(variable_names) > 1
        if not variable_names[-1]:
            variable_names.pop()

        return cls(variable_names, expression, unpack)

    def evaluate(self, compilation):
        # TODO with compilation.new_scope() as namespace:
        namespace = compilation.current_namespace

        # TODO compilation.calculator?  or change calculator to namespace?
        calc = Calculator(namespace)
        values = self.expression.evaluate(calc)
        # TODO is the from_maybe necessary here?  doesn't Value do __iter__?
        for values in List.from_maybe(values):
            if self.unpack:
                values = List.from_maybe(values)
                for i, variable_name in enumerate(self.variable_names):
                    if i >= len(values):
                        value = Null()
                    else:
                        value = values[i]
                    namespace.set_variable(variable_name, value)
            else:
                namespace.set_variable(self.variable_names[0], values)

            # TODO i would love to get this recursion out of here -- clever use
            # of yield?
            for child in self.children:
                child.evaluate(compilation)


# TODO make @-rules support both with and without blocks with the same class,
# so this can be gotten rid of
class AtIncludeBlock(AtRule):
    def __init__(self, mixin_name, argspec):
        self.mixin_name = mixin_name
        self.argspec = argspec

    @classmethod
    def parse(cls, argument):
        # TODO basically copy/pasted from @mixin
        try:
            callop = Calculator().parse_expression(
                argument, 'goal_function_call_opt_parens')
        except SassParseError:
            # TODO exc.when("trying to parse a mixin inclusion")
            raise

        # Unpack the CallOp
        mixin_name = callop.function_name
        argspec = callop.argspec

        return cls(mixin_name, argspec)

    def evaluate(self, compilation):
        caller_namespace = compilation.current_namespace
        caller_calculator = compilation._make_calculator(caller_namespace)

        # Render the passed arguments, using the caller's namespace
        args, kwargs = self.argspec.evaluate_call_args(caller_calculator)

        argc = len(args) + len(kwargs)
        try:
            mixin = caller_namespace.mixin(self.mixin_name, argc)
        except KeyError:
            try:
                # TODO should really get rid of this; ... works now
                # Fallback to single parameter:
                mixin = caller_namespace.mixin(self.mixin_name, 1)
            except KeyError:
                # TODO track source line/file
                # TODO hang on this should be fatal
                log.error("Mixin not found: %s:%d (%s)", self.mixin_name, argc, "lol idk", extra={'stack': True})
                return
            else:
                args = [List(args, use_comma=True)]
                # TODO what happens to kwargs?

        # TODO source_file = mixin[0]
        # TODO lineno = mixin[1]

        # Put the arguments in their own namespace, and let the mixin derive
        # from it
        local_namespace = Namespace()
        self._populate_namespace_from_call(
            compilation, local_namespace, mixin.argspec, args, kwargs)

        namespaces = [local_namespace]
        if self.argspec.inject and mixin.argspec.inject:
            # DEVIATION: Pass the ENTIRE local namespace to the mixin (yikes)
            namespaces.append(compilation.current_namespace)

        mixin.evaluate(compilation, namespaces)

        # TODO the old SassRule defined from_source_etc here
        # TODO _rule.options['@content'] = block.unparsed_contents

    def _populate_namespace_from_call(self, compilation, namespace, argspec, args, kwargs):
        """Populate a temporary @mixin namespace with the arguments passed to
        an @include.
        """
        # Mutation protection
        args = list(args)
        kwargs = OrderedDict(kwargs)

        calculator = compilation._make_calculator(namespace)

        # Populate the mixin/function's namespace with its arguments
        for var_name, node in argspec.iter_def_argspec():
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
                value = node.evaluate(calculator, divide=True)
            else:
                # TODO this should raise
                # TODO in the meantime, warn_undefined(...)
                value = Undefined()

            namespace.set_variable(var_name, value, local_only=True)

        if argspec.slurp:
            # Slurpy var gets whatever is left
            # TODO should preserve the order of extra kwargs
            sass_kwargs = []
            for key, value in kwargs.items():
                sass_kwargs.append((String(key[1:]), value))
            namespace.set_variable(
                argspec.slurp.name,
                Arglist(args, sass_kwargs))
            args = []
            kwargs = {}
        elif argspec.inject:
            # Callee namespace gets all the extra kwargs whether declared or
            # not
            for var_name, value in kwargs.items():
                namespace.set_variable(var_name, value, local_only=True)
            kwargs = {}

        # TODO would be nice to say where the mixin/function came from
        # TODO generally need more testing of error cases
        # TODO
        name = "This mixin"
        if kwargs:
            raise NameError("%s has no such argument %s" % (name, kwargs.keys()[0]))

        if args:
            raise NameError("%s received extra arguments: %r" % (name, args))

        # TODO import_key = mixin[5]
        # TODO pristine_callee_namespace = mixin[3]
        # TODO pristine_callee_namespace.use_import(import_key)
        return namespace


class Mixin(object):
    """Binds a parsed @mixin block to the runtime namespace it was defined in.
    """
    def __init__(self, mixin, namespace):
        self.mixin = mixin
        self.namespace = namespace

    @property
    def argspec(self):
        return self.mixin.argspec

    def evaluate(self, compilation, namespaces):
        local_namespace = Namespace.derive_from(
            self.namespace, *namespaces)

        with compilation.push_namespace(local_namespace):
            for child in self.mixin.children:
                child.evaluate(compilation)


class AtMixinBlock(AtRuleBlock):
    directive = '@mixin'

    def __init__(self, mixin_name, argspec):
        # TODO fix parent to not assign to directive/argument and use super
        # here
        Block.__init__(self)

        self.mixin_name = mixin_name
        self.argspec = argspec

    @classmethod
    def parse(cls, argument):
        # TODO the original _get_funct_def applied interpolations here before
        # parsing anything; not sure that's right, but kronuz might rely on it?
        try:
            callop = Calculator().parse_expression(
                argument, 'goal_function_call_opt_parens')
        except SassParseError:
            # TODO exc.when("trying to parse a mixin definition")
            raise

        # Unpack the CallOp
        mixin_name = callop.function_name
        argspec = callop.argspec

        return cls(mixin_name, argspec)

    def evaluate(self, compilation):
        # Evaluating a @mixin just means making it exist; we already have its
        # AST!
        namespace = compilation.current_namespace
        mixin = Mixin(self, namespace)
        for arity in self.argspec.iter_def_arities():
            namespace.set_mixin(self.mixin_name, arity, mixin)
