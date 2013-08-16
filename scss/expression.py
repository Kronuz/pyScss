from __future__ import absolute_import

from functools import partial
import logging
import operator
import re

import six

import scss.config as config
from scss.cssdefs import COLOR_NAMES, is_builtin_css_function, _expr_glob_re, _interpolate_re, _variable_re
from scss.rule import Namespace
from scss.types import BooleanValue, ColorValue, ListValue, Map, Null, NumberValue, ParserValue, String, Undefined
from scss.util import dequote, normalize_var

################################################################################
# Load C acceleration modules
Scanner = None
try:
    from scss._speedups import NoMoreTokens, Scanner
except ImportError:
    from scss._native import NoMoreTokens, Scanner

log = logging.getLogger(__name__)

FATAL_UNDEFINED = True
ast_cache = {}


class Calculator(object):
    """Expression evaluator."""

    def __init__(self, namespace=None):
        if namespace is None:
            self.namespace = Namespace()
        else:
            self.namespace = namespace

    def _pound_substitute(self, result):
        expr = result.group(1)
        value = self.evaluate_expression(expr)

        if value is None:
            return self.apply_vars(expr)
        elif value.is_null:
            return ""
        else:
            return dequote(value.render())

    def do_glob_math(self, cont):
        """Performs #{}-interpolation.  The result is always treated as a fixed
        syntactic unit and will not be re-evaluated.
        """
        # TODO this should really accept and/or parse an *expression* and
        # return a type  :|
        cont = str(cont)
        if '#{' not in cont:
            return cont
        cont = _expr_glob_re.sub(self._pound_substitute, cont)
        return cont

    def apply_vars(self, cont):
        if isinstance(cont, six.string_types) and '$' in cont:
            try:
                # Optimization: the full cont is a variable in the context,
                cont = self.namespace.variable(cont)
            except KeyError:
                # Interpolate variables:
                def _av(m):
                    v = None
                    n = m.group(2)
                    try:
                        v = self.namespace.variable(n)
                    except KeyError:
                        if FATAL_UNDEFINED:
                            raise
                        else:
                            log.error("Undefined variable '%s'", n, extra={'stack': True})
                            return n
                    else:
                        if v:
                            if not isinstance(v, six.string_types):
                                v = v.render()
                            # TODO this used to test for _dequote
                            if m.group(1):
                                v = dequote(v)
                        else:
                            v = m.group(0)
                        return v

                cont = _interpolate_re.sub(_av, cont)
        # XXX what?: if options is not None:
        # ...apply math:
        cont = self.do_glob_math(cont)
        return cont

    def calculate(self, _base_str, divide=False):
        better_expr_str = _base_str

        better_expr_str = self.do_glob_math(better_expr_str)

        better_expr_str = self.evaluate_expression(better_expr_str, divide=divide)

        if better_expr_str is None:
            better_expr_str = self.apply_vars(_base_str)

        return better_expr_str

    # TODO only used by magic-import...?
    def interpolate(self, var):
        value = self.namespace.variable(var)
        if var != value and isinstance(value, six.string_types):
            _vi = self.evaluate_expression(value)
            if _vi is not None:
                value = _vi
        return value

    def evaluate_expression(self, expr, divide=False):
        if not isinstance(expr, six.string_types):
            raise TypeError("Expected string, got %r" % (expr,))

        if expr in ast_cache:
            ast = ast_cache[expr]

        elif _variable_re.match(expr):
            # Short-circuit for variable names
            ast = Variable(expr)

        else:
            try:
                parser = SassExpression(SassExpressionScanner(expr))
                ast = parser.goal()
            except SyntaxError:
                if config.DEBUG:
                    raise
                return None
            except Exception:
                # TODO hoist me up since the rule is gone
                #log.exception("Exception raised: %s in `%s' (%s)", e, expr, rule.file_and_line)
                if config.DEBUG:
                    raise
                return None
            else:
                ast_cache[expr] = ast

        return ast.evaluate(self, divide=divide)

    def parse_expression(self, expr, target='goal'):
        if expr in ast_cache:
            return ast_cache[expr]

        parser = SassExpression(SassExpressionScanner(expr))
        ast = getattr(parser, target)()

        if target == 'goal':
            ast_cache[expr] = ast

        return ast


# ------------------------------------------------------------------------------
# Expression classes -- the AST resulting from a parse

class Expression(object):
    def __repr__(self):
        return repr(self.__dict__)

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
    def __init__(self, contents):
        self.contents = contents

    def evaluate(self, calculator, divide=False):
        return self.contents.evaluate(calculator, divide=True)


class UnaryOp(Expression):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def evaluate(self, calculator, divide=False):
        return self.op(self.operand.evaluate(calculator, divide=True))


class BinaryOp(Expression):
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
    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, calculator, divide=False):
        operands = [operand.evaluate(calculator, divide=True) for operand in self.operands]
        return BooleanValue(any(operands))


class AllOp(Expression):
    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, calculator, divide=False):
        operands = [operand.evaluate(calculator, divide=True) for operand in self.operands]
        return BooleanValue(all(operands))


class NotOp(Expression):
    def __init__(self, operand):
        self.operand = operand

    def evaluate(self, calculator, divide=False):
        operand = self.operand.evaluate(calculator, divide=True)
        return BooleanValue(not(operand))


class CallOp(Expression):
    def __init__(self, func_name, argspec):
        self.func_name = func_name
        self.argspec = argspec

    def evaluate(self, calculator, divide=False):
        # TODO bake this into the context and options "dicts", plus library
        func_name = normalize_var(self.func_name)

        # Turn the pairs of arg tuples into *args and **kwargs
        # TODO unclear whether this is correct -- how does arg, kwarg, arg
        # work?
        args = []
        kwargs = {}
        evald_argpairs = []
        for var, expr in self.argspec.iter_call_argspec():
            value = expr.evaluate(calculator, divide=True)
            evald_argpairs.append((var, value))

            if var is None:
                args.append(value)
            else:
                kwargs[var.lstrip('$').replace('-', '_')] = value

        num_args = len(self.argspec.argpairs)

        # TODO merge this with the library
        try:
            func = calculator.namespace.function(func_name, num_args)
            # @functions take a ns as first arg.  TODO: Python functions possibly
            # should too
            if getattr(func, '__name__', None) == '__call':
                func = partial(func, calculator.namespace)
        except KeyError:
            if not is_builtin_css_function(func_name):
                log.error("Function not found: %s:%s", func_name, num_args, extra={'stack': True})

            rendered_args = []
            for var, value in evald_argpairs:
                rendered_value = value.render()
                if var is None:
                    rendered_args.append(rendered_value)
                else:
                    rendered_args.append("%s: %s" % (var, rendered_value))

            return String(
                u"%s(%s)" % (func_name, u", ".join(rendered_args)),
                quotes=None)
        else:
            return func(*args, **kwargs)


class Literal(Expression):
    def __init__(self, value):
        self.value = value

    def evaluate(self, calculator, divide=False):
        return self.value


class Variable(Expression):
    def __init__(self, name):
        self.name = name

    def evaluate(self, calculator, divide=False):
        try:
            value = calculator.namespace.variable(self.name)
        except KeyError:
            if FATAL_UNDEFINED:
                raise
            else:
                log.error("Undefined variable '%s'", self.name, extra={'stack': True})
                return Undefined()
        else:
            if isinstance(value, six.string_types):
                evald = calculator.evaluate_expression(value)
                if evald is not None:
                    return evald
            return value


class ListLiteral(Expression):
    def __init__(self, items, comma=True):
        self.items = items
        self.comma = comma

    def evaluate(self, calculator, divide=False):
        items = [item.evaluate(calculator, divide=divide) for item in self.items]
        return ListValue(items, separator="," if self.comma else "")


class MapLiteral(Expression):
    def __init__(self, pairs):
        self.pairs = tuple((var, value) for var, value in pairs if value is not None)

    def evaluate(self, calculator, divide=False):
        # TODO unclear here whether the keys should be bare tokens or Literals;
        # depends how the syntax works!
        scss_pairs = []
        for key, value in self.pairs:
            scss_pairs.append((
                key.name if isinstance(key, Variable) else key.value,
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
    def __init__(self, argpairs):
        # argpairs is a list of 2-tuples, parsed as though this were a function
        # call, so (variable name as string or None, default value as AST
        # node).
        while argpairs and argpairs[-1] == (None, None):
            argpairs = argpairs[:-1]
        self.argpairs = tuple((var, Literal(Undefined()) if value is None else value) for var, value in argpairs)

    def iter_def_argspec(self):
        """Interpreting this literal as a function definition, yields pairs of
        (variable name as a string, default value as an AST node or None).
        """
        for var, value in self.argpairs:
            if var is None:
                # value is actually the name
                var = value
                value = None

            if not isinstance(var, Variable):
                raise SyntaxError("Expected variable name, got %r" % (var,))

            yield var.name, value

    def iter_call_argspec(self):
        """Interpreting this literal as a function call, yields pairs of
        (variable name as a string, default value as an AST node or None).
        """
        for var, value in self.argpairs:
            if var is None:
                yield var, value
            else:
                if not isinstance(var, Variable):
                    raise SyntaxError("Expected variable name, got %r" % (var,))
                yield var.name, value


def parse_bareword(word):
    if word in COLOR_NAMES:
        return ColorValue.from_name(word)
    elif word == 'null':
        return Null()
    elif word == 'undefined':
        return Undefined()
    elif word == 'true':
        return BooleanValue(True)
    elif word == 'false':
        return BooleanValue(False)
    else:
        return String(word, quotes=None)


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
        try:
            tok = self._scanner.token(self._pos, types)
            return tok[2]
        except SyntaxError:
            return None

    def _scan(self, type):
        """
        Returns the matched text, and moves to the next token
        """
        tok = self._scanner.token(self._pos, set([type]))
        if tok[2] != type:
            raise SyntaxError("SyntaxError[@ char %s: %s]" % (repr(tok[0]), "Trying to find " + type))
        self._pos += 1
        return tok[3]


################################################################################
## Grammar compiled using Yapps:

class SassExpressionScanner(Scanner):
    patterns = None
    _patterns = [
        ('":"', ':'),
        ('","', ','),
        ('[ \r\t\n]+', '[ \r\t\n]+'),
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
        ('KWSTR', "'[^']*'(?=\\s*:)"),
        ('STR', "'[^']*'"),
        ('KWQSTR', '"[^"]*"(?=\\s*:)'),
        ('QSTR', '"[^"]*"'),
        ('UNITS', '(?<!\\s)(?:[a-zA-Z]+|%)(?![-\\w])'),
        ('KWNUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?=\\s*:)'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('KWCOLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])(?=\\s*:)'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('KWVAR', '\\$[-a-zA-Z0-9_]+(?=\\s*:)'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('KWID', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\s*:)'),
        ('ID', '[-a-zA-Z_][-a-zA-Z0-9_]*'),
        ('BANG_IMPORTANT', '!important'),
    ]

    def __init__(self, input=None):
        if hasattr(self, 'setup_patterns'):
            self.setup_patterns(self._patterns)
        elif self.patterns is None:
            self.__class__.patterns = []
            for t, p in self._patterns:
                self.patterns.append((t, re.compile(p)))
        super(SassExpressionScanner, self).__init__(None, ['[ \r\t\n]+'], input)


class SassExpression(Parser):
    def goal(self):
        expr_lst = self.expr_lst()
        END = self._scan('END')
        return expr_lst

    def goal_argspec(self):
        argspec = self.argspec()
        END = self._scan('END')
        return argspec

    def argspec(self):
        argspec_item = self.argspec_item()
        argpairs = [argspec_item]
        while self._peek(self.argspec_rsts) == '","':
            self._scan('","')
            argspec_item = (None, None)
            if self._peek(self.argspec_rsts_) not in self.argspec_rsts:
                argspec_item = self.argspec_item()
            argpairs.append(argspec_item)
        return ArgspecLiteral(argpairs)

    def argspec_item(self):
        _token_ = self._peek(self.argspec_item_rsts)
        if _token_ == 'KWVAR':
            KWVAR = self._scan('KWVAR')
            self._scan('":"')
            expr_slst = self.expr_slst()
            return (Variable(KWVAR), expr_slst)
        else:  # in self.argspec_item_chks
            expr_slst = self.expr_slst()
            return (None, expr_slst)

    def expr_map(self):
        map_item = self.map_item()
        pairs = [map_item]
        while self._peek(self.expr_map_rsts) == '","':
            self._scan('","')
            map_item = (None, None)
            if self._peek(self.expr_map_rsts_) not in self.expr_map_rsts:
                map_item = self.map_item()
            pairs.append(map_item)
        return MapLiteral(pairs)

    def map_item(self):
        kwatom = self.kwatom()
        self._scan('":"')
        expr_slst = self.expr_slst()
        return (kwatom, expr_slst)

    def expr_lst(self):
        expr_slst = self.expr_slst()
        v = [expr_slst]
        while self._peek(self.argspec_rsts) == '","':
            self._scan('","')
            expr_slst = self.expr_slst()
            v.append(expr_slst)
        return ListLiteral(v) if len(v) > 1 else v[0]

    def expr_slst(self):
        or_expr = self.or_expr()
        v = [or_expr]
        while self._peek(self.expr_slst_rsts) not in self.argspec_rsts:
            or_expr = self.or_expr()
            v.append(or_expr)
        return ListLiteral(v, comma=False) if len(v) > 1 else v[0]

    def or_expr(self):
        and_expr = self.and_expr()
        v = and_expr
        while self._peek(self.or_expr_rsts) == 'OR':
            OR = self._scan('OR')
            and_expr = self.and_expr()
            v = AnyOp(v, and_expr)
        return v

    def and_expr(self):
        not_expr = self.not_expr()
        v = not_expr
        while self._peek(self.and_expr_rsts) == 'AND':
            AND = self._scan('AND')
            not_expr = self.not_expr()
            v = AllOp(v, not_expr)
        return v

    def not_expr(self):
        _token_ = self._peek(self.argspec_item_chks)
        if _token_ != 'NOT':
            comparison = self.comparison()
            return comparison
        else:  # == 'NOT'
            NOT = self._scan('NOT')
            not_expr = self.not_expr()
            return NotOp(not_expr)

    def comparison(self):
        a_expr = self.a_expr()
        v = a_expr
        while self._peek(self.comparison_rsts) in self.comparison_chks:
            _token_ = self._peek(self.comparison_chks)
            if _token_ == 'LT':
                LT = self._scan('LT')
                a_expr = self.a_expr()
                v = BinaryOp(operator.lt, v, a_expr)
            elif _token_ == 'GT':
                GT = self._scan('GT')
                a_expr = self.a_expr()
                v = BinaryOp(operator.gt, v, a_expr)
            elif _token_ == 'LE':
                LE = self._scan('LE')
                a_expr = self.a_expr()
                v = BinaryOp(operator.le, v, a_expr)
            elif _token_ == 'GE':
                GE = self._scan('GE')
                a_expr = self.a_expr()
                v = BinaryOp(operator.ge, v, a_expr)
            elif _token_ == 'EQ':
                EQ = self._scan('EQ')
                a_expr = self.a_expr()
                v = BinaryOp(operator.eq, v, a_expr)
            else:  # == 'NE'
                NE = self._scan('NE')
                a_expr = self.a_expr()
                v = BinaryOp(operator.ne, v, a_expr)
        return v

    def a_expr(self):
        m_expr = self.m_expr()
        v = m_expr
        while self._peek(self.a_expr_rsts) in self.a_expr_chks:
            _token_ = self._peek(self.a_expr_chks)
            if _token_ == 'ADD':
                ADD = self._scan('ADD')
                m_expr = self.m_expr()
                v = BinaryOp(operator.add, v, m_expr)
            else:  # == 'SUB'
                SUB = self._scan('SUB')
                m_expr = self.m_expr()
                v = BinaryOp(operator.sub, v, m_expr)
        return v

    def m_expr(self):
        u_expr = self.u_expr()
        v = u_expr
        while self._peek(self.m_expr_rsts) in self.m_expr_chks:
            _token_ = self._peek(self.m_expr_chks)
            if _token_ == 'MUL':
                MUL = self._scan('MUL')
                u_expr = self.u_expr()
                v = BinaryOp(operator.mul, v, u_expr)
            else:  # == 'DIV'
                DIV = self._scan('DIV')
                u_expr = self.u_expr()
                v = BinaryOp(operator.truediv, v, u_expr)
        return v

    def u_expr(self):
        _token_ = self._peek(self.u_expr_rsts)
        if _token_ == 'SIGN':
            SIGN = self._scan('SIGN')
            u_expr = self.u_expr()
            return UnaryOp(operator.neg, u_expr)
        elif _token_ == 'ADD':
            ADD = self._scan('ADD')
            u_expr = self.u_expr()
            return UnaryOp(operator.pos, u_expr)
        else:  # in self.u_expr_chks
            atom = self.atom()
            return atom

    def atom(self):
        _token_ = self._peek(self.u_expr_chks)
        if _token_ == 'LPAR':
            LPAR = self._scan('LPAR')
            _token_ = self._peek(self.atom_rsts)
            if _token_ not in self.argspec_item_chks:
                expr_map = self.expr_map()
                v = expr_map
            else:  # in self.argspec_item_chks
                expr_lst = self.expr_lst()
                v = Parentheses(expr_lst)
            RPAR = self._scan('RPAR')
            return v
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            argspec = ArgspecLiteral([])
            LPAR = self._scan('LPAR')
            if self._peek(self.atom_rsts_) not in self.atom_chks:
                argspec = self.argspec()
            RPAR = self._scan('RPAR')
            return CallOp(FNCT, argspec)
        elif _token_ == 'BANG_IMPORTANT':
            BANG_IMPORTANT = self._scan('BANG_IMPORTANT')
            return Literal(String(BANG_IMPORTANT, quotes=None))
        elif _token_ == 'ID':
            ID = self._scan('ID')
            return Literal(parse_bareword(ID))
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            UNITS = None
            if self._peek(self.atom_rsts__) == 'UNITS':
                UNITS = self._scan('UNITS')
            return Literal(NumberValue(float(NUM), unit=UNITS))
        elif _token_ == 'STR':
            STR = self._scan('STR')
            return Literal(String(STR[1:-1], quotes="'"))
        elif _token_ == 'QSTR':
            QSTR = self._scan('QSTR')
            return Literal(String(QSTR[1:-1], quotes='"'))
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return Literal(ColorValue(ParserValue(COLOR)))
        else:  # == 'VAR'
            VAR = self._scan('VAR')
            return Variable(VAR)

    def kwatom(self):
        _token_ = self._peek(self.kwatom_rsts)
        if _token_ == '":"':
            pass
        elif _token_ == 'KWID':
            KWID = self._scan('KWID')
            return Literal(parse_bareword(KWID))
        elif _token_ == 'KWNUM':
            KWNUM = self._scan('KWNUM')
            UNITS = None
            if self._peek(self.kwatom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
            return Literal(NumberValue(float(KWNUM), unit=UNITS))
        elif _token_ == 'KWSTR':
            KWSTR = self._scan('KWSTR')
            return Literal(String(KWSTR[1:-1], quotes="'"))
        elif _token_ == 'KWQSTR':
            KWQSTR = self._scan('KWQSTR')
            return Literal(String(KWQSTR[1:-1], quotes='"'))
        elif _token_ == 'KWCOLOR':
            KWCOLOR = self._scan('KWCOLOR')
            return Literal(ColorValue(ParserValue(KWCOLOR)))
        else:  # == 'KWVAR'
            KWVAR = self._scan('KWVAR')
            return Variable(KWVAR)

    u_expr_chks = set(['LPAR', 'COLOR', 'QSTR', 'NUM', 'FNCT', 'STR', 'VAR', 'BANG_IMPORTANT', 'ID'])
    m_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    expr_map_rsts = set(['RPAR', '","'])
    kwatom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'KWCOLOR', '":"', 'KWNUM'])
    argspec_item_chks = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID'])
    a_expr_chks = set(['ADD', 'SUB'])
    expr_slst_rsts = set(['LPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID', '","'])
    a_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    or_expr_rsts = set(['LPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'STR', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR', '","'])
    argspec_item_rsts = set(['KWVAR', 'LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID'])
    atom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'BANG_IMPORTANT', 'LPAR', 'COLOR', 'KWQSTR', 'SIGN', 'KWCOLOR', 'VAR', 'ADD', 'NUM', '":"', 'STR', 'NOT', 'QSTR', 'KWNUM', 'ID', 'FNCT'])
    comparison_rsts = set(['LPAR', 'QSTR', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'SIGN', 'ADD', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'GE', 'NOT', 'OR', '","'])
    atom_rsts_ = set(['KWVAR', 'LPAR', 'BANG_IMPORTANT', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'STR', 'NOT', 'RPAR', 'ID'])
    expr_map_rsts_ = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'RPAR', 'KWCOLOR', '":"', 'KWNUM', '","'])
    u_expr_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'ADD', 'NUM', 'FNCT', 'STR', 'VAR', 'BANG_IMPORTANT', 'ID'])
    atom_chks = set(['END', 'RPAR'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    atom_rsts__ = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'VAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'UNITS', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    m_expr_chks = set(['MUL', 'DIV'])
    kwatom_rsts_ = set(['UNITS', '":"'])
    argspec_rsts = set(['RPAR', 'END', '","'])
    and_expr_rsts = set(['AND', 'LPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'STR', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR', '","'])
    argspec_rsts_ = set(['KWVAR', 'LPAR', 'BANG_IMPORTANT', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'STR', 'NOT', 'RPAR', 'ID', '","'])

### Grammar ends.
################################################################################

__all__ = ('Calculator',)
