from __future__ import absolute_import

from functools import partial
import logging
import operator
import re

import scss.config as config
from scss.cssdefs import is_builtin_css_function, _expr_glob_re, _interpolate_re, _units, _variable_re
from scss.types import BooleanValue, ColorValue, ListValue, NumberValue, ParserValue, QuotedStringValue, StringValue
from scss.util import dequote, normalize_var, to_str

################################################################################
# Load C acceleration modules
Scanner = None
try:
    from scss._speedups import NoMoreTokens, Scanner
except ImportError:
    from scss._native import NoMoreTokens, Scanner

log = logging.getLogger(__name__)

ast_cache = {}


class Calculator(object):
    """Expression evaluator."""

    def __init__(self, library):
        # TODO the library should really be part of the rule
        self.library = library

    def _calculate_expr(self, rule, context, options):
        def __calculate_expr(result):
            _group0 = result.group(1)
            _base_str = _group0
            better_expr_str = eval_expr(_base_str, rule, self.library)

            if better_expr_str is None:
                better_expr_str = self.apply_vars(_base_str, rule, context, options)
            else:
                better_expr_str = dequote(str(better_expr_str))

            return better_expr_str
        return __calculate_expr

    def do_glob_math(self, cont, rule, context=None, options=None):
        """Performs #{}-interpolation.  The result is always treated as a fixed
        syntactic unit and will not be re-evaluated.
        """
        # TODO this should really accept and/or parse an *expression* and
        # return a type  :|
        cont = str(cont)
        if '#{' not in cont:
            return cont
        cont = _expr_glob_re.sub(self._calculate_expr(rule, context, options), cont)
        return cont

    def apply_vars(self, cont, rule, context=None, options=None):
        if context is not None and isinstance(cont, basestring) and '$' in cont:
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
                        # TODO this used to test for _dequote
                        if m.group(1):
                            v = dequote(v)
                    elif v is not None:
                        v = to_str(v)
                    else:
                        v = m.group(0)
                    return v

                cont = _interpolate_re.sub(_av, cont)
        if options is not None:
            # ...apply math:
            cont = self.do_glob_math(cont, rule, context, options)
        return cont

    def calculate(self, _base_str, rule, context=None, options=None):
        better_expr_str = _base_str

        rule = rule.copy()
        rule.context = context
        rule.options = options

        better_expr_str = self.do_glob_math(better_expr_str, rule, context, options)

        better_expr_str = eval_expr(better_expr_str, rule, self.library, True)

        if better_expr_str is None:
            better_expr_str = self.apply_vars(_base_str, rule, context, options)

        return better_expr_str


def interpolate(var, rule, library):
    value = rule.context.get(normalize_var(var), var)
    if var != value and isinstance(value, basestring):
        _vi = eval_expr(value, rule, library, True)
        if _vi is not None:
            value = _vi
    return value


def eval_expr(expr, rule, library, raw=False):
    # print >>sys.stderr, '>>',expr,'<<'
    results = None

    if not isinstance(expr, basestring):
        results = expr

    if results is None:
        if _variable_re.match(expr):
            expr = normalize_var(expr)
        if expr in rule.context:
            chkd = {}
            while expr in rule.context and expr not in chkd:
                chkd[expr] = 1
                _expr = rule.context[expr]
                if _expr == expr:
                    break
                expr = _expr
        if not isinstance(expr, basestring):
            results = expr

    ast = None
    if results is None:
        if expr in ast_cache:
            ast = ast_cache[expr]
            results = ast.evaluate(rule, library)
        else:
            try:
                P = CalculatorParser(CalculatorScanner())
                P.reset(expr)
                ast = P.goal()
            except SyntaxError:
                if config.DEBUG:
                    raise
            except Exception, e:
                log.exception("Exception raised: %s in `%s' (%s)", e, expr, rule.file_and_line)
                if config.DEBUG:
                    raise
            else:
                ast_cache[expr] = ast

                results = ast.evaluate(rule, library)

    if not raw and results is not None:
        results = to_str(results)

    # print >>sys.stderr, repr(expr),'==',results,'=='
    return results


# ------------------------------------------------------------------------------
# Expression classes -- the AST resulting from a parse

class Expression(object):
    def __repr__(self):
        return repr(self.__dict__)

    def evaluate(self, rule, library):
        raise NotImplementedError

class UnaryOp(Expression):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def evaluate(self, rule, library):
        return self.op(self.operand.evaluate(rule, library))

class BinaryOp(Expression):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, rule, library):
        left = self.left.evaluate(rule, library)
        right = self.right.evaluate(rule, library)
        return self.op(left, right)

class AnyOp(Expression):
    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, rule, library):
        operands = [operand.evaluate(rule, library) for operand in self.operands]
        return any(operands)

class AllOp(Expression):
    def __init__(self, *operands):
        self.operands = operands

    def evaluate(self, rule, library):
        operands = [operand.evaluate(rule, library) for operand in self.operands]
        return all(operands)

class NotOp(Expression):
    def __init__(self, operand):
        self.operand = operand

    def evaluate(self, rule, library):
        return not(self.operand.evaluate(rule, library))

class CallOp(Expression):
    def __init__(self, func_name, argspec):
        self.func_name = func_name
        self.argspec = argspec

    def evaluate(self, rule, library):
        # TODO bake this into the context and options "dicts", plus library
        name = normalize_var(self.func_name)

        # Turn the pairs of arg tuples into *args and **kwargs
        # TODO unclear whether this is correct -- how does arg, kwarg, arg
        # work?
        args = []
        kwargs = {}
        evald_argpairs = []
        for var, expr in self.argspec.argpairs:
            value = expr.evaluate(rule, library)
            evald_argpairs.append((var, value))

            if var is None:
                args.append(value)
            else:
                kwargs[ var.lstrip('$').replace('-', '_') ] = value

        num_args = len(self.argspec.argpairs)

        # First look for a custom in-sass function
        option_name = "@function %s:%d" % (name, num_args)
        func = rule.options.get(option_name)
        # @functions take a rule as first arg.  TODO: Python functions possibly
        # should too
        if func is not None:
            func = partial(func, rule)

        try:
            # If that fails, check for Python implementations
            if func is None:
                func = library.lookup(name, num_args)
        except KeyError:
            if not is_builtin_css_function(name):
                # TODO log.warn, log.error, warning, exception?
                log.warn("no such function")

            rendered_args = []
            for var, value in evald_argpairs:
                rendered_value = to_str(value)
                if var is None:
                    rendered_args.append(rendered_value)
                else:
                    rendered_args.append("%s: %s" % (var, rendered_value))

            return StringValue("%s(%s)" % (name, ", ".join(rendered_args)))
        else:
            return func(*args, **kwargs)

class Literal(Expression):
    def __init__(self, value):
        self.value = value

    def evaluate(self, rule, library):
        return self.value

class Variable(Expression):
    def __init__(self, name):
        self.name = name

    def evaluate(self, rule, library):
        var = normalize_var(self.name)
        if var in rule.context:
            # TODO this should be a real value, not a flattened basestring
            value = rule.context[var]
            if isinstance(value, basestring):
                evald = eval_expr(value, rule, library, True)
                if evald is not None:
                    return evald
            return value
        else:
            # TODO well, no.
            return var

class ListLiteral(Expression):
    def __init__(self, items, comma=True):
        self.items = items
        self.comma = comma

    def evaluate(self, rule, library):
        items = [item.evaluate(rule, library) for item in self.items]
        return ListValue(items, separator="," if self.comma else "")

class ArgspecLiteral(Expression):
    def __init__(self, argpairs):
        self.argpairs = argpairs






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
class CalculatorScanner(Scanner):
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


class CalculatorParser(Parser):
    def goal(self):
        expr_lst = self.expr_lst()
        v = expr_lst
        END = self._scan('END')
        return v

    def expr(self):
        and_test = self.and_test()
        v = and_test
        while self._peek(self.expr_rsts) == 'OR':
            OR = self._scan('OR')
            and_test = self.and_test()
            v = AnyOp(v, and_test)
        return v

    def and_test(self):
        not_test = self.not_test()
        v = not_test
        while self._peek(self.and_test_rsts) == 'AND':
            AND = self._scan('AND')
            not_test = self.not_test()
            v = AllOp(v, not_test)
        return v

    def not_test(self):
        _token_ = self._peek(self.not_test_rsts)
        if _token_ != 'NOT':
            comparison = self.comparison()
            return comparison
        else:  # == 'NOT'
            NOT = self._scan('NOT')
            not_test = self.not_test()
            return NotOp(not_test)

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
                v = BinaryOp(operator.div, v, u_expr)
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
            expr_lst = self.expr_lst()
            RPAR = self._scan('RPAR')
            return expr_lst
        elif _token_ == 'ID':
            ID = self._scan('ID')
            return Literal(StringValue(ID))
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            v = ArgspecLiteral([])
            LPAR = self._scan('LPAR')
            if self._peek(self.atom_rsts) != 'RPAR':
                argspec = self.argspec()
                v = argspec
            RPAR = self._scan('RPAR')
            return CallOp(FNCT, v)
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            if self._peek(self.atom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
                return Literal(NumberValue(float(NUM), type=UNITS))
            return Literal(NumberValue(float(NUM)))
        elif _token_ == 'STR':
            STR = self._scan('STR')
            return Literal(StringValue(ParserValue(STR)))
        elif _token_ == 'QSTR':
            QSTR = self._scan('QSTR')
            return Literal(QuotedStringValue(ParserValue(QSTR)))
        elif _token_ == 'BOOL':
            BOOL = self._scan('BOOL')
            return Literal(BooleanValue(ParserValue(BOOL)))
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return Literal(ColorValue(ParserValue(COLOR)))
        else:  # == 'VAR'
            VAR = self._scan('VAR')
            return Variable(VAR)

    def argspec(self):
        argspec_item = self.argspec_item()
        v = [argspec_item]
        while self._peek(self.argspec_rsts) == 'COMMA':
            COMMA = self._scan('COMMA')
            argspec_item = self.argspec_item()
            v.append(argspec_item)
        return ArgspecLiteral(v)

    def argspec_item(self):
        var = None
        if self._peek(self.argspec_item_rsts) == 'VAR':
            VAR = self._scan('VAR')
            if self._peek(self.argspec_item_rsts_) == '":"':
                self._scan('":"')
                var = VAR
            else: self._rewind()
        expr_slst = self.expr_slst()
        return (var, expr_slst)

    def expr_lst(self):
        expr_slst = self.expr_slst()
        v = [expr_slst]
        while self._peek(self.expr_lst_rsts) == 'COMMA':
            COMMA = self._scan('COMMA')
            expr_slst = self.expr_slst()
            v.append(expr_slst)
        return ListLiteral(v) if len(v) > 1 else v[0]

    def expr_slst(self):
        expr = self.expr()
        v = [expr]
        while self._peek(self.expr_slst_rsts) not in self.expr_lst_rsts:
            expr = self.expr()
            v.append(expr)
        return ListLiteral(v, comma=False) if len(v) > 1 else v[0]

    m_expr_chks = set(['MUL', 'DIV'])
    comparison_rsts = set(['LPAR', 'QSTR', 'RPAR', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'ADD', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'GE', 'BOOL', 'NOT', 'OR'])
    u_expr_chks = set(['LPAR', 'COLOR', 'QSTR', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    m_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'MUL', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'BOOL', 'NOT', 'OR'])
    argspec_item_rsts_ = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'BOOL', '":"', 'STR', 'NOT', 'ID', 'FNCT'])
    expr_lst_rsts = set(['END', 'COMMA', 'RPAR'])
    and_test_rsts = set(['AND', 'LPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'ID', 'RPAR', 'OR'])
    atom_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'NOT', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'RPAR', 'ID'])
    u_expr_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    expr_rsts = set(['LPAR', 'END', 'COLOR', 'QSTR', 'RPAR', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'ID', 'SIGN', 'OR'])
    argspec_item_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'NOT', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'VAR', 'ID'])
    argspec_rsts = set(['COMMA', 'RPAR'])
    not_test_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'BOOL', 'FNCT', 'STR', 'NOT', 'ID'])
    atom_rsts_ = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'VAR', 'MUL', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'UNITS', 'EQ', 'ID', 'AND', 'ADD', 'BOOL', 'NOT', 'OR'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    a_expr_chks = set(['ADD', 'SUB'])
    a_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'BOOL', 'NOT', 'OR'])
    expr_slst_rsts = set(['LPAR', 'END', 'COLOR', 'QSTR', 'RPAR', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BOOL', 'SIGN', 'ID'])


    expr_lst_rsts_ = None

### Grammar ends.
################################################################################

__all__ = ('interpolate', 'eval_expr', 'Calculator')
