# python yapps2.py grammar.g grammar.py

################################################################################
## Grammar compiled using Yapps:

import re
from string import *
from yappsrt import *


class SassExpressionScanner(Scanner):
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
        ('UNITS', '(?<!\\s)(?:[a-zA-Z]+|%)(?![-\\w])'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
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
        v = expr_lst
        END = self._scan('END')
        return v

    def expr(self):
        and_expr = self.and_expr()
        v = and_expr
        while self._peek(self.expr_rsts) == 'OR':
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
        _token_ = self._peek(self.not_expr_rsts)
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
            expr_lst = self.expr_lst()
            RPAR = self._scan('RPAR')
            return Parentheses(expr_lst)
        elif _token_ == 'ID':
            ID = self._scan('ID')
            return Literal(parse_bareword(ID))
        elif _token_ == 'BANG_IMPORTANT':
            BANG_IMPORTANT = self._scan('BANG_IMPORTANT')
            return Literal(String(BANG_IMPORTANT, quotes=None))
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            v = ArgspecLiteral([])
            LPAR = self._scan('LPAR')
            if self._peek(self.atom_rsts) != 'RPAR':
                expr_lst = self.expr_lst()
                v = expr_lst
            RPAR = self._scan('RPAR')
            return CallOp(FNCT, v)
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            if self._peek(self.atom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
                return Literal(NumberValue(float(NUM), unit=UNITS.lower()))
            return Literal(NumberValue(float(NUM)))
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

    def expr_lst(self):
        expr_item = self.expr_item()
        v = [expr_item]
        while self._peek(self.expr_lst_rsts) == 'COMMA':
            COMMA = self._scan('COMMA')
            expr_item = self.expr_item()
            v.append(expr_item)
        return ListLiteral(v) if len(v) > 1 else v[0]

    def expr_item(self):
        var = None
        if self._peek(self.expr_item_rsts) == 'VAR':
            VAR = self._scan('VAR')
            if self._peek(self.expr_item_rsts_) == '":"':
                self._scan('":"')
                var = VAR
            else: self._rewind()
        expr_slst = self.expr_slst()
        return (var, expr_slst)

    def expr_slst(self):
        expr = self.expr()
        v = [expr]
        while self._peek(self.expr_slst_rsts) not in self.expr_lst_rsts:
            expr = self.expr()
            v.append(expr)
        return ListLiteral(v, comma=False) if len(v) > 1 else v[0]

    m_expr_chks = set(['MUL', 'DIV'])
    comparison_rsts = set(['LPAR', 'QSTR', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'ADD', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'GE', 'NOT', 'OR'])
    atom_rsts = set(['LPAR', 'BANG_IMPORTANT', 'COLOR', 'QSTR', 'SIGN', 'NOT', 'ADD', 'NUM', 'FNCT', 'STR', 'VAR', 'RPAR', 'ID'])
    u_expr_chks = set(['LPAR', 'COLOR', 'QSTR', 'NUM', 'FNCT', 'STR', 'VAR', 'BANG_IMPORTANT', 'ID'])
    m_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR'])
    expr_lst_rsts = set(['END', 'COMMA', 'RPAR'])
    and_expr_rsts = set(['AND', 'LPAR', 'RPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR'])
    u_expr_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'ADD', 'NUM', 'FNCT', 'STR', 'VAR', 'BANG_IMPORTANT', 'ID'])
    expr_rsts = set(['LPAR', 'RPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'ID', 'BANG_IMPORTANT', 'OR'])
    expr_item_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'NOT', 'ADD', 'NUM', 'FNCT', 'STR', 'VAR', 'BANG_IMPORTANT', 'ID'])
    not_expr_rsts = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID'])
    atom_rsts_ = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'VAR', 'MUL', 'DIV', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'UNITS', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    a_expr_chks = set(['ADD', 'SUB'])
    a_expr_rsts = set(['LPAR', 'SUB', 'QSTR', 'RPAR', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'COMMA', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'STR', 'VAR', 'EQ', 'ID', 'AND', 'ADD', 'NOT', 'OR'])
    expr_item_rsts_ = set(['LPAR', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', '":"', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID', 'FNCT'])
    expr_slst_rsts = set(['LPAR', 'RPAR', 'END', 'COLOR', 'QSTR', 'SIGN', 'VAR', 'ADD', 'NUM', 'COMMA', 'FNCT', 'STR', 'NOT', 'BANG_IMPORTANT', 'ID'])


### Grammar ends.
################################################################################
