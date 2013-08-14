from __future__ import absolute_import
from __future__ import print_function

from functools import partial
import logging
import operator
import re

import six

import scss
import scss.config as config
from scss.cssdefs import COLOR_NAMES, is_builtin_css_function, _expr_glob_re, _interpolate_re, _variable_re
from scss.errors import SassError, SassEvaluationError, SassParseError
from scss.rule import Namespace
from scss.types import Boolean, Color, List, Map, Null, Number, ParserValue, String, Undefined, Value
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


from ometa.runtime import EOFError, OMetaBase, expected
import string
HEXDIGITS = frozenset(string.hexdigits)
WHITESPACE = frozenset(' \n\r\t\f')
LETTERISH = frozenset(string.letters + '-_')
class GrammarBase(OMetaBase):
    def rule_ws(self):
        s, e = self.rule_ows()
        if not s:
            raise e.withMessage(expected("whitespace"))

        return s, e

    def rule_ows(self):
        ret = []
        while True:
            try:
                c, e = self.input.head()
            except EOFError as exc:
                e = exc
                break

            if c in WHITESPACE:
                ret.append(c)
                self.input = self.input.tail()
            else:
                break

        return ''.join(ret), e

    def rule_hex(self):
        x, e = self.rule_anything()
        if x in HEXDIGITS:
            return x, e
        else:
            raise e.withMessage(expected("hex digit"))

    def rule_letterish(self):
        x, e = self.rule_anything()
        if x in LETTERISH:
            return x, e
        else:
            raise e.withMessage(expected("letter or underscore or hyphen"))

_grammar = None
def get_grammar():
    global _grammar
    if _grammar:
        return _grammar

    from parsley import wrapGrammar
    from ometa.grammar import loadGrammar
    grammar = loadGrammar(scss, 'expression', globals(), superclass=GrammarBase)
    _grammar = wrapGrammar(grammar)
    return _grammar

    import parsley
    import os.path
    with open(os.path.dirname(__file__) + '/expression.parsley') as f:
        grammar = parsley.makeGrammar(f.read(), globals())

    _grammar = grammar
    return grammar


class Calculator(object):
    """Expression evaluator."""

    ast_cache = {}

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

        #better_expr_str = self.do_glob_math(better_expr_str)

        better_expr_str = self.evaluate_expression(better_expr_str, divide=divide)

        if better_expr_str is None:
            better_expr_str = String.unquoted(self.apply_vars(_base_str))

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
        try:
            ast = self.parse_expression(expr)
        except SassError:
            if config.DEBUG:
                raise
            else:
                return None

        try:
            return ast.evaluate(self, divide=divide)
        except Exception as e:
            raise SassEvaluationError(e, expression=expr)

    def parse_expression(self, expr, target='goal'):
        if not isinstance(expr, six.string_types):
            raise TypeError("Expected string, got %r" % (expr,))

        key = (target, expr)
        if key in self.ast_cache:
            return self.ast_cache[key]

        grammar = get_grammar()
        print("parsing", target, ":", repr(expr))
        try:
            if False:
                print("got from original grammar:", end='')
                parser = SassExpression(SassExpressionScanner(expr))
                ast = P.goal()

            else:
                print("got from new grammar:     ", end='')
                parser = grammar(expr)
                if target == 'goal':
                    target = 'expression'

            ast = getattr(parser, target)()
            print(repr(ast))
        except SyntaxError as e:
            raise SassParseError(e, expression=expr, expression_pos=parser._char_pos)

        self.ast_cache[key] = ast
        return ast


# ------------------------------------------------------------------------------
# Expression classes -- the AST resulting from a parse

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
        operands = [operand.evaluate(calculator, divide=True) for operand in self.operands]
        return Boolean(any(operands))


class AllOp(Expression):
    def __repr__(self):
        return '<%s(*%s)>' % (self.__class__.__name__, repr(self.operands))

    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, calculator, divide=False):
        operands = [operand.evaluate(calculator, divide=True) for operand in self.operands]
        return Boolean(all(operands))


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
        argspec = list(argspec_node.iter_call_argspec())
        argspec_len = len(argspec)

        # Turn the pairs of arg tuples into *args and **kwargs
        # TODO unclear whether this is correct -- how does arg, kwarg, arg
        # work?
        args = []
        kwargs = {}
        evald_argpairs = []
        for var, expr in argspec_node.iter_call_argspec():
            value = expr.evaluate(calculator, divide=True)
            evald_argpairs.append((var, value))
            if var is None:
                args.append(value)
            else:
                kwargs[var.lstrip('$').replace('-', '_')] = value

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
                if kwargs:
                    raise
                # DEVIATION: Fall back to single parameter
                funct = calculator.namespace.function(func_name, 1)
                args = [args]
            except KeyError:
                if not is_builtin_css_function(func_name):
                    log.error("Function not found: %s:%s", func_name, argspec_len, extra={'stack': True})
                    raise
        if funct:
            ret = funct(*args, **kwargs)
            if not isinstance(ret, Value):
                raise TypeError("Expected Sass type as return value, got %r" % (ret,))
            return ret

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


class Literal(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.value))

    def __init__(self, value):
        self.value = value

    def evaluate(self, calculator, divide=False):
        return self.value


class FunctionLiteral(Expression):
    def __init__(self, name, value_node):
        self.name = name
        self.value_node = value_node

    def evaluate(self, calculator, divide=False):
        value = self.value_node.evaluate(calculator)
        return String(u"%s(%s)" % (self.name, value.render()), quotes=None)


class Variable(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.name))

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
    def __repr__(self):
        return '<%s(%s, comma=%s)>' % (self.__class__.__name__, repr(self.items), repr(self.comma))

    def __init__(self, items, comma=True):
        self.items = items
        self.comma = comma

    def evaluate(self, calculator, divide=False):
        items = [item.evaluate(calculator, divide=divide) for item in self.items]
        return List(items, separator="," if self.comma else "")


class MapLiteral(Expression):
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.pairs))

    def __init__(self, pairs):
        self.pairs = tuple((var, value) for var, value in pairs if value is not None)

    def evaluate(self, calculator, divide=False):
        # TODO unclear here whether the keys should be bare tokens or Literals;
        # depends how the syntax works!
        scss_pairs = []
        for name, value in self.pairs:
            scss_pairs.append((
                name.name if isinstance(name, Variable) else name.value,
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

    def __init__(self, argpairs):
        # argpairs is a list of 2-tuples, parsed as though this were a function
        # call, so (variable name as string or None, default value as AST
        # node).
        while argpairs and argpairs[-1] == (None, None):
            argpairs = argpairs[:-1]
        self.argpairs = tuple((var, Literal(Undefined()) if value is None else value) for var, value in argpairs)

    def iter_list_argspec(self):
        yield None, ListLiteral(zip(*self.argpairs)[1])

    def iter_def_argspec(self):
        """Interpreting this literal as a function definition, yields pairs of
        (variable name as a string, default value as an AST node or None).
        """
        for var, value in self.argpairs:
            if var is None:
                # value is actually the name
                var = value
                value = Literal(Undefined())

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


class Interpolation(Expression):
    def __init__(self, left, expr, right, quotes):
        self.left = left
        self.expr = expr
        self.right = right
        self.quotes = quotes

    def evaluate(self, calculator, divide=False):
        left_scss = self.left.evaluate(calculator)
        if not isinstance(left_scss, String):
            raise TypeError("Expected left side of interpolation to be String, got %r" % (left,))
        left = left_scss.value

        right_scss = self.right.evaluate(calculator)
        if not isinstance(right_scss, String):
            raise TypeError("Expected right side of interpolation to be String, got %r" % (left,))
        right = right_scss.value

        expr = self.expr.evaluate(calculator)
        if isinstance(expr, String):
            middle = expr.value
        else:
            middle = expr.render()

        return String(left + middle + right, quotes=self.quotes)


def parse_bareword(word):
    if word in COLOR_NAMES:
        return Color.from_name(word)
    elif word == 'null':
        return Null()
    elif word == 'undefined':
        return Undefined()
    elif word == 'true':
        return Boolean(True)
    elif word == 'false':
        return Boolean(False)
    else:
        return String(word, quotes=None)


class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._pos = 0
        self._char_pos = 0

    def reset(self, input):
        self._scanner.reset(input)
        self._pos = 0
        self._char_pos = 0

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
        self._char_pos = tok[0]
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
        ('LINTERP', '#[{]'),
        ('RINTERP', '[}]'),
        ('SQUOT', "'"),
        ('DQUOT', '"'),
        ('SQCHAR', "([^'#]|#(?![{]))*"),
        ('DQCHAR', '([^"#]|#(?![{]))*'),
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
        while self._peek(self.expr_lst_rsts) == '","':
            self._scan('","')
            expr_slst = self.expr_slst()
            v.append(expr_slst)
        return ListLiteral(v) if len(v) > 1 else v[0]

    def expr_slst(self):
        or_expr = self.or_expr()
        v = [or_expr]
        while self._peek(self.expr_slst_rsts) not in self.expr_lst_rsts:
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
                v = expr_lst
            RPAR = self._scan('RPAR')
            return Parentheses(v)
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
            return Literal(Number(float(NUM), unit=UNITS))
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return Literal(Color(ParserValue(COLOR)))
        elif _token_ == 'SQUOT':
            SQUOT = self._scan('SQUOT')
            SQCHAR = self._scan('SQCHAR')
            v = Literal(String(SQCHAR, quotes="'"))
            while self._peek(self.atom_rsts___) == 'LINTERP':
                LINTERP = self._scan('LINTERP')
                expr_lst = self.expr_lst()
                RINTERP = self._scan('RINTERP')
                SQCHAR = self._scan('SQCHAR')
                v = Interpolation(v, expr_lst, Literal(String(SQCHAR, quotes="'")), quotes="'")
            SQUOT = self._scan('SQUOT')
            return v
        elif _token_ == 'DQUOT':
            DQUOT = self._scan('DQUOT')
            DQCHAR = self._scan('DQCHAR')
            v = Literal(String(DQCHAR, quotes='"'))
            while self._peek(self.atom_rsts____) == 'LINTERP':
                LINTERP = self._scan('LINTERP')
                expr_lst = self.expr_lst()
                RINTERP = self._scan('RINTERP')
                DQCHAR = self._scan('DQCHAR')
                v = Interpolation(v, expr_lst, Literal(String(DQCHAR, quotes='"')), quotes='"')
            DQUOT = self._scan('DQUOT')
            return v
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
            return Literal(Number(float(KWNUM), unit=UNITS))
        elif _token_ == 'KWSTR':
            KWSTR = self._scan('KWSTR')
            return Literal(String(KWSTR[1:-1], quotes="'"))
        elif _token_ == 'KWQSTR':
            KWQSTR = self._scan('KWQSTR')
            return Literal(String(KWQSTR[1:-1], quotes='"'))
        elif _token_ == 'KWCOLOR':
            KWCOLOR = self._scan('KWCOLOR')
            return Literal(Color(ParserValue(KWCOLOR)))
        else:  # == 'KWVAR'
            KWVAR = self._scan('KWVAR')
            return Variable(KWVAR)

    atom_rsts____ = set(['LINTERP', 'DQUOT'])
    u_expr_chks = set(['LPAR', 'COLOR', 'SQUOT', 'DQUOT', 'NUM', 'FNCT', 'VAR', 'BANG_IMPORTANT', 'ID'])
    m_expr_rsts = set(['LPAR', 'SUB', 'SQUOT', 'DQUOT', 'RPAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'RINTERP', 'SIGN', 'GE', 'FNCT', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    expr_map_rsts = set(['RPAR', '","'])
    expr_lst_rsts = set(['RPAR', 'RINTERP', 'END', '","'])
    kwatom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'KWCOLOR', '":"', 'KWNUM'])
    argspec_item_chks = set(['LPAR', 'COLOR', 'SQUOT', 'DQUOT', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'ID'])
    a_expr_chks = set(['ADD', 'SUB'])
    expr_slst_rsts = set(['LPAR', 'END', 'COLOR', 'SQUOT', 'DQUOT', 'RINTERP', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'ID', '","'])
    a_expr_rsts = set(['LPAR', 'SUB', 'SQUOT', 'DQUOT', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'RINTERP', 'SIGN', 'GE', 'FNCT', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    or_expr_rsts = set(['LPAR', 'END', 'COLOR', 'SQUOT', 'DQUOT', 'RINTERP', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR', '","'])
    argspec_item_rsts = set(['KWVAR', 'LPAR', 'COLOR', 'SQUOT', 'DQUOT', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'ID'])
    atom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'BANG_IMPORTANT', 'LPAR', 'COLOR', 'SQUOT', 'KWQSTR', 'DQUOT', 'SIGN', 'KWCOLOR', 'VAR', 'ADD', 'NUM', '":"', 'NOT', 'KWNUM', 'ID', 'FNCT'])
    comparison_rsts = set(['LPAR', 'SQUOT', 'DQUOT', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'RINTERP', 'SIGN', 'ADD', 'FNCT', 'VAR', 'EQ', 'ID', 'AND', 'GE', 'NOT', 'OR', '","'])
    atom_rsts_ = set(['KWVAR', 'LPAR', 'BANG_IMPORTANT', 'END', 'COLOR', 'SQUOT', 'DQUOT', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'RPAR', 'ID'])
    expr_map_rsts_ = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'RPAR', 'KWCOLOR', '":"', 'KWNUM', '","'])
    u_expr_rsts = set(['LPAR', 'COLOR', 'SQUOT', 'DQUOT', 'SIGN', 'ADD', 'NUM', 'FNCT', 'VAR', 'BANG_IMPORTANT', 'ID'])
    atom_chks = set(['END', 'RPAR'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    atom_rsts__ = set(['LPAR', 'SUB', 'SQUOT', 'DQUOT', 'RPAR', 'VAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'GT', 'END', 'RINTERP', 'SIGN', 'GE', 'FNCT', 'UNITS', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR', '","'])
    m_expr_chks = set(['MUL', 'DIV'])
    kwatom_rsts_ = set(['UNITS', '":"'])
    atom_rsts___ = set(['LINTERP', 'SQUOT'])
    argspec_rsts = set(['RPAR', 'END', '","'])
    and_expr_rsts = set(['AND', 'LPAR', 'END', 'COLOR', 'SQUOT', 'DQUOT', 'RINTERP', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR', '","'])
    argspec_rsts_ = set(['KWVAR', 'LPAR', 'BANG_IMPORTANT', 'END', 'COLOR', 'SQUOT', 'DQUOT', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'RPAR', 'ID', '","'])


### Grammar ends.
################################################################################

__all__ = ('Calculator',)
