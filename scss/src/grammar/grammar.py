# python yapps2.py grammar.g grammar.py


_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
_inv = lambda s: s
ParserValue = lambda s: s
NumberValue = lambda s: float(s)
StringValue = lambda s: s
QuotedStringValue = lambda s: s
BooleanValue = lambda s: bool(s)
ColorValue = lambda s: s
class ListValue():
    def __init__(self, v):
        if isinstance(v, self.__class__):
            self.v = v
        else:
            self.v = {0: v}
    def first(self):
        return self.v[0]
    def __len__(self):
        return len(self.v)


def _reorder_list(lst):
    return dict((i if isinstance(k, int) else k, v) for i, (k, v) in enumerate(sorted(lst.items())))


def interpolate(v, R):
    return v


def call(fn, args, R, function=True):
    print 'call: ', fn, args
    return args

################################################################################
#'(?<!\\s)(?:' + '|'.join(_units) + ')(?![-\\w])'
## Grammar compiled using Yapps:

import re
from string import *
from yappsrt import *


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
        ('UNITS', '(?<!\\s)(?:px|cm|mm|hz|%)(?![-\\w])'),
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
            v = v or and_test
        return v

    def and_test(self, R):
        not_test = self.not_test(R)
        v = not_test
        while self._peek(self.and_test_rsts) == 'AND':
            AND = self._scan('AND')
            not_test = self.not_test(R)
            v = v and not_test
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
                    v = not not_test
                else:  # == 'INV'
                    INV = self._scan('INV')
                    not_test = self.not_test(R)
                    v = _inv('!', not_test)
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
                v = v < a_expr
            elif _token_ == 'GT':
                GT = self._scan('GT')
                a_expr = self.a_expr(R)
                v = v > a_expr
            elif _token_ == 'LE':
                LE = self._scan('LE')
                a_expr = self.a_expr(R)
                v = v <= a_expr
            elif _token_ == 'GE':
                GE = self._scan('GE')
                a_expr = self.a_expr(R)
                v = v >= a_expr
            elif _token_ == 'EQ':
                EQ = self._scan('EQ')
                a_expr = self.a_expr(R)
                v = v == a_expr
            else:  # == 'NE'
                NE = self._scan('NE')
                a_expr = self.a_expr(R)
                v = v != a_expr
        return v

    def a_expr(self, R):
        m_expr = self.m_expr(R)
        v = m_expr
        while self._peek(self.a_expr_rsts) in self.a_expr_chks:
            _token_ = self._peek(self.a_expr_chks)
            if _token_ == 'ADD':
                ADD = self._scan('ADD')
                m_expr = self.m_expr(R)
                v = v + m_expr
            else:  # == 'SUB'
                SUB = self._scan('SUB')
                m_expr = self.m_expr(R)
                v = v - m_expr
        return v

    def m_expr(self, R):
        u_expr = self.u_expr(R)
        v = u_expr
        while self._peek(self.m_expr_rsts) in self.m_expr_chks:
            _token_ = self._peek(self.m_expr_chks)
            if _token_ == 'MUL':
                MUL = self._scan('MUL')
                u_expr = self.u_expr(R)
                v = v * u_expr
            else:  # == 'DIV'
                DIV = self._scan('DIV')
                u_expr = self.u_expr(R)
                v = v / u_expr
        return v

    def u_expr(self, R):
        _token_ = self._peek(self.u_expr_rsts)
        if _token_ == 'SIGN':
            SIGN = self._scan('SIGN')
            u_expr = self.u_expr(R)
            return _inv('-', u_expr)
        elif _token_ == 'ADD':
            ADD = self._scan('ADD')
            u_expr = self.u_expr(R)
            return u_expr
        else:  # in self.u_expr_chks
            atom = self.atom(R)
            v = atom
            if self._peek(self.u_expr_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
                v = call(UNITS, ListValue(ParserValue({0: v, 1: UNITS})), R, False)
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
            return call(FNCT, v, R)
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
            return interpolate(VAR, R)

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

### Grammar ends.
################################################################################

P = Calculator(CalculatorScanner())


def parse(rule, text, *args):
    P.reset(text)
    return wrap_error_reporter(P, rule, *args)


if __name__ == '__main__':
    while True:
        try:
            s = raw_input('>>> ')
        except EOFError:
            break
        if not s.strip():
            break
        print parse('goal', s, None)
    print 'Bye.'
