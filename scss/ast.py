"""Syntax tree for parsed Sass expressions.

The overall structure for a Sass file uses a different kind of AST; have a look
at :mod:`scss.blockast`.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from functools import partial
import logging
import operator

import six

from scss.cssdefs import COLOR_NAMES
from scss.cssdefs import is_builtin_css_function
from scss.types import Boolean
from scss.types import Color
from scss.types import List
from scss.types import Map
from scss.types import Null
from scss.types import String
from scss.types import Undefined
from scss.types import Value
from scss.util import normalize_var


log = logging.getLogger(__name__)


class Expression(object):
    def __repr__(self):
        return '<%s()>' % (self.__class__.__name__)

    def evaluate(self, calculator, divide=False):
        """Evaluate this AST node, and return a Sass value.

        `divide` indicates whether a descendant node representing a division
        should be forcibly treated as a division.  See the commentary in
        `BinaryOp`.
        """
        raise NotImplementedError


class Parentheses(Expression):
    """An expression of the form `(foo)`.

    Only exists to force a slash to be interpreted as division when contained
    within parentheses.
    """
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.contents))

    def __init__(self, contents):
        self.contents = contents

    def evaluate(self, calculator, divide=False):
        return self.contents.evaluate(calculator, divide=True)


class UnaryOp(Expression):
    def __repr__(self):
        return '<%s(%s, %s)>' % (self.__class__.__name__, repr(self.op), repr(self.operand))

    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def evaluate(self, calculator, divide=False):
        return self.op(self.operand.evaluate(calculator, divide=True))


class BinaryOp(Expression):
    def __repr__(self):
        return '<%s(%s, %s, %s)>' % (self.__class__.__name__, repr(self.op), repr(self.left), repr(self.right))

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, calculator, divide=False):
        left = self.left.evaluate(calculator, divide=True)
        right = self.right.evaluate(calculator, divide=True)

        # Special handling of division: treat it as a literal slash if both
        # operands are literals, there are parentheses, or this is part of a
        # bigger expression.
        # The first condition is covered by the type check.  The other two are
        # covered by the `divide` argument: other nodes that perform arithmetic
        # will pass in True, indicating that this should always be a division.
        if (
            self.op is operator.truediv
            and not divide
            and isinstance(self.left, Literal)
            and isinstance(self.right, Literal)
        ):
            return String(left.render() + ' / ' + right.render(), quotes=None)

        return self.op(left, right)


class AnyOp(Expression):
    def __repr__(self):
        return '<%s(*%s)>' % (self.__class__.__name__, repr(self.op), repr(self.operands))

    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, calculator, divide=False):
        for operand in self.operands:
            value = operand.evaluate(calculator, divide=True)
            if value:
                return value
        return value


class AllOp(Expression):
    def __repr__(self):
        return '<%s(*%s)>' % (self.__class__.__name__, repr(self.operands))

    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, calculator, divide=False):
        for operand in self.operands:
            value = operand.evaluate(calculator, divide=True)
            if not value:
                return value
        return value


class NotOp(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.operand))

    def __init__(self, operand):
        self.operand = operand

    def evaluate(self, calculator, divide=False):
        operand = self.operand.evaluate(calculator, divide=True)
        return Boolean(not(operand))


class CallOp(Expression):
    def __repr__(self):
        return '<%s(%s, %s)>' % (self.__class__.__name__, repr(self.func_name), repr(self.argspec))

    def __init__(self, func_name, argspec):
        self.func_name = func_name
        self.argspec = argspec

    def evaluate(self, calculator, divide=False):
        # TODO bake this into the context and options "dicts", plus library
        func_name = normalize_var(self.func_name)

        argspec_node = self.argspec

        # Turn the pairs of arg tuples into *args and **kwargs
        # TODO unclear whether this is correct -- how does arg, kwarg, arg
        # work?
        args, kwargs = argspec_node.evaluate_call_args(calculator)
        argspec_len = len(args) + len(kwargs)

        # Translate variable names to Python identifiers
        # TODO what about duplicate kw names?  should this happen in argspec?
        # how does that affect mixins?
        kwargs = dict(
            (key.lstrip('$').replace('-', '_'), value)
            for key, value in kwargs.items())

        # TODO merge this with the library
        funct = None
        try:
            funct = calculator.namespace.function(func_name, argspec_len)
            # @functions take a ns as first arg.  TODO: Python functions possibly
            # should too
            if getattr(funct, '__name__', None) == '__call':
                funct = partial(funct, calculator.namespace)
        except KeyError:
            try:
                # DEVIATION: Fall back to single parameter
                funct = calculator.namespace.function(func_name, 1)
                args = [List(args, use_comma=True)]
            except KeyError:
                if not is_builtin_css_function(func_name):
                    log.error("Function not found: %s:%s", func_name, argspec_len, extra={'stack': True})

        if funct:
            ret = funct(*args, **kwargs)
            if not isinstance(ret, Value):
                raise TypeError("Expected Sass type as return value, got %r" % (ret,))
            return ret

        # No matching function found, so render the computed values as a CSS
        # function call.  Slurpy arguments are expanded and named arguments are
        # unsupported.
        if kwargs:
            raise TypeError("The CSS function %s doesn't support keyword arguments." % (func_name,))

        # TODO another candidate for a "function call" sass type
        rendered_args = [arg.render() for arg in args]

        return String(
            "%s(%s)" % (func_name, ", ".join(rendered_args)),
            quotes=None)


# TODO this class should delegate the unescaping to the type, rather than
# burying it in the parser
class Interpolation(Expression):
    """A string that may contain any number of interpolations:

        foo#{...}bar#{...}baz
    """
    def __init__(self, parts, quotes=None, type=String, **kwargs):
        self.parts = parts
        self.quotes = quotes
        self.type = type
        self.kwargs = kwargs

    @classmethod
    def maybe(cls, parts, quotes=None, type=String, **kwargs):
        """Returns an interpolation if there are multiple parts, otherwise a
        plain Literal.  This keeps the AST somewhat simpler, but also is the
        only way `Literal.from_bareword` gets called.
        """
        if len(parts) > 1:
            return cls(parts, quotes=quotes, type=type, **kwargs)

        if quotes is None and type is String:
            return Literal.from_bareword(parts[0])

        return Literal(type(parts[0], quotes=quotes, **kwargs))

    def _render_interpolated(self, value):
        """Return the result of interpolating `value`, which is slightly
        different than just rendering it, since it's an intermediate thing.
        """
        # Strings are taken literally
        if isinstance(value, String):
            return value.value

        # Lists are joined recursively
        if isinstance(value, List):
            # TODO Ruby /immediately/ respects `compress` here -- need to
            # inspect the compilation for whether to pass it in (probably in
            # other places too)
            return value.delimiter().join(
                self._render_interpolated(item) for item in value)
        else:
            # TODO like here
            return value.render()

    def evaluate(self, calculator, divide=False):
        result = []
        for i, part in enumerate(self.parts):
            if i % 2 == 0:
                # First part and other odd parts are literal string
                result.append(part)
            else:
                # Interspersed (even) parts are nodes
                value = part.evaluate(calculator, divide)
                result.append(self._render_interpolated(value))

        return self.type(''.join(result), quotes=self.quotes, **self.kwargs)



class Literal(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.value))

    def __init__(self, value):
        self.value = value

    @classmethod
    def from_bareword(cls, word):
        if word in COLOR_NAMES:
            value = Color.from_name(word)
        elif word == 'null':
            value = Null()
        elif word == 'undefined':
            value = Undefined()
        elif word == 'true':
            value = Boolean(True)
        elif word == 'false':
            value = Boolean(False)
        else:
            value = String(word, quotes=None)

        return cls(value)

    def evaluate(self, calculator, divide=False):
        if (isinstance(self.value, Undefined) and
                calculator.undefined_variables_fatal):
            raise SyntaxError("Undefined literal.")

        return self.value


class Variable(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.name))

    def __init__(self, name):
        self.name = name

    def evaluate(self, calculator, divide=False):
        try:
            value = calculator.namespace.variable(self.name)
        except KeyError:
            if calculator.undefined_variables_fatal:
                raise SyntaxError("Undefined variable: '%s'." % self.name)
            else:
                log.error("Undefined variable '%s'", self.name, extra={'stack': True})
                return Undefined()
        else:
            if isinstance(value, six.string_types):
                log.warn(
                    "Expected a Sass type for the value of {0}, "
                    "but found a string expression: {1!r}"
                    .format(self.name, value)
                )
                evald = calculator.evaluate_expression(value)
                if evald is not None:
                    return evald
            return value


class ListLiteral(Expression):
    def __repr__(self):
        return '<%s(%s, comma=%s)>' % (self.__class__.__name__, repr(self.items), repr(self.comma))

    def __init__(self, items, comma=True):
        self.items = items
        self.comma = comma

    def evaluate(self, calculator, divide=False):
        items = [item.evaluate(calculator, divide=divide) for item in self.items]

        # Whether this is a "plain" literal matters for null removal: nulls are
        # left alone if this is a completely vanilla CSS property
        is_literal = True
        if divide:
            # TODO sort of overloading "divide" here...  rename i think
            is_literal = False
        elif not all(isinstance(item, Literal) for item in self.items):
            is_literal = False

        return List(items, use_comma=self.comma, is_literal=is_literal)


class MapLiteral(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.pairs))

    def __init__(self, pairs):
        self.pairs = tuple((var, value) for var, value in pairs if value is not None)

    def evaluate(self, calculator, divide=False):
        scss_pairs = []
        for key, value in self.pairs:
            scss_pairs.append((
                key.evaluate(calculator),
                value.evaluate(calculator),
            ))

        return Map(scss_pairs)


class ArgspecLiteral(Expression):
    """Contains pairs of argument names and values, as parsed from a function
    definition or function call.

    Note that the semantics are somewhat ambiguous.  Consider parsing:

        $foo, $bar: 3

    If this appeared in a function call, $foo would refer to a value; if it
    appeared in a function definition, $foo would refer to an existing
    variable.  This it's up to the caller to use the right iteration function.
    """
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.argpairs))

    def __init__(self, argpairs, slurp=None):
        # argpairs is a list of 2-tuples, parsed as though this were a function
        # call, so (variable name as string or None, default value as AST
        # node).
        # slurp is the name of a variable to receive slurpy arguments.
        self.argpairs = tuple(argpairs)
        if slurp is all:
            # DEVIATION: special syntax to allow injecting arbitrary arguments
            # from the caller to the callee
            self.inject = True
            self.slurp = None
        elif slurp:
            self.inject = False
            self.slurp = Variable(slurp)
        else:
            self.inject = False
            self.slurp = None

    def iter_list_argspec(self):
        yield None, ListLiteral(zip(*self.argpairs)[1])

    def iter_def_argspec(self):
        """Interpreting this literal as a function definition, yields pairs of
        (variable name as a string, default value as an AST node or None).
        """
        started_kwargs = False
        seen_vars = set()

        for var, value in self.argpairs:
            if var is None:
                # value is actually the name
                var = value
                value = None

                if started_kwargs:
                    raise SyntaxError(
                        "Required argument %r must precede optional arguments"
                        % (var.name,))

            else:
                started_kwargs = True

            if not isinstance(var, Variable):
                raise SyntaxError("Expected variable name, got %r" % (var,))

            if var.name in seen_vars:
                raise SyntaxError("Duplicate argument %r" % (var.name,))
            seen_vars.add(var.name)

            yield var.name, value

    def evaluate_call_args(self, calculator):
        """Interpreting this literal as a function call, return a 2-tuple of
        ``(args, kwargs)``.
        """
        args = []
        kwargs = {}
        for var_node, value_node in self.argpairs:
            value = value_node.evaluate(calculator, divide=True)
            if var_node is None:
                # Positional
                args.append(value)
            else:
                # Named
                if not isinstance(var_node, Variable):
                    raise SyntaxError("Expected variable name, got %r" % (var_node,))
                kwargs[var_node.name] = value

        # Slurpy arguments go on the end of the args
        if self.slurp:
            args.extend(self.slurp.evaluate(calculator, divide=True))

        return args, kwargs
