from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import logging

from scss.expression import Calculator
from scss.types import List
from scss.types import Null
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

