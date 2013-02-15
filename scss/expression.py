from __future__ import absolute_import

import logging
import re

import scss.config as config
from scss.cssdefs import _css_functions_re, _units
from scss.parseutil import _inv
from scss.rule import CONTEXT, OPTIONS, INDEX, LINENO
from scss.types import BooleanValue, ColorValue, ListValue, NumberValue, ParserValue, QuotedStringValue, StringValue
from scss.util import normalize_var, to_str

################################################################################
# Load C acceleration modules
Scanner = None
try:
    from scss._speedups import NoMoreTokens, Scanner
except ImportError:
    from scss._native import NoMoreTokens, Scanner

log = logging.getLogger(__name__)

# TODO redefined from __init__
_variable_re = re.compile('^\\$[-a-zA-Z0-9_]+$')
_undefined_re = re.compile('^(?:\\$[-a-zA-Z0-9_]+|undefined)$')


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

__all__ = ('interpolate', 'call', 'eval_expr', 'Calculator')
