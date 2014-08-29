"""Grammar for parsing Sass expressions."""
# This is a GENERATED FILE -- DO NOT EDIT DIRECTLY!
# Edit scss/grammar/expression.g, then run:
#
#     python2 yapps2.py scss/grammar/expression.g

import operator
import re

from scss.ast import Parentheses
from scss.ast import UnaryOp
from scss.ast import BinaryOp
from scss.ast import AnyOp
from scss.ast import AllOp
from scss.ast import NotOp
from scss.ast import CallOp
from scss.ast import Interpolation
from scss.ast import Literal
from scss.ast import Variable
from scss.ast import ListLiteral
from scss.ast import MapLiteral
from scss.ast import ArgspecLiteral
from scss.cssdefs import unescape
from scss.types import Color
from scss.types import Number
from scss.types import String
from scss.types import Url
from scss.util import dequote

from scss.grammar import Parser
from scss.grammar import Scanner



class SassExpressionScanner(Scanner):
    patterns = None
    _patterns = [
        ('"url"', 'url'),
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
        ('DOTDOTDOT', '[.]{3}'),
        ('SINGLE_QUOTE', "'"),
        ('DOUBLE_QUOTE', '"'),
        ('SINGLE_STRING_GUTS', "([^'\\\\#]|[\\\\].|#(?![{]))*"),
        ('DOUBLE_STRING_GUTS', '([^"\\\\#]|[\\\\].|#(?![{]))*'),
        ('KWSTR', "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'(?=\\s*:)"),
        ('STR', "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"),
        ('KWQSTR', '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"(?=\\s*:)'),
        ('QSTR', '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"'),
        ('UNITS', '(?<!\\s)(?:[a-zA-Z]+|%)(?![-\\w])'),
        ('KWNUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?=\\s*:)'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('KWCOLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])(?=\\s*:)'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('KWVAR', '\\$[-a-zA-Z0-9_]+(?=\\s*:)'),
        ('SLURPYVAR', '\\$[-a-zA-Z0-9_]+(?=[.][.][.])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('KWID', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\s*:)'),
        ('BAREWORD', '[-a-zA-Z_][-a-zA-Z0-9_]*'),
        ('BANG_IMPORTANT', '!important'),
        ('INTERP_START', '#[{]'),
        ('INTERP_END', '[}]'),
        ('INTERP_ANYTHING', '([^#]|#(?![{]))*'),
        ('BAREURL', '(?:[\\\\].|[^#$\'"()\\x00-\\x08\\x0b\\x0e-\\x1f\\x7f]|#(?![{]))*'),
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
        _token_ = self._peek(self.argspec_rsts)
        if _token_ not in self.argspec_chks:
            if self._peek(self.argspec_rsts_) not in self.argspec_chks_:
                argspec_items = self.argspec_items()
                args, slurpy = argspec_items
                return ArgspecLiteral(args, slurp=slurpy)
            return ArgspecLiteral([])
        elif _token_ == 'SLURPYVAR':
            SLURPYVAR = self._scan('SLURPYVAR')
            DOTDOTDOT = self._scan('DOTDOTDOT')
            return ArgspecLiteral([], slurp=SLURPYVAR)
        else:  # == 'DOTDOTDOT'
            DOTDOTDOT = self._scan('DOTDOTDOT')
            return ArgspecLiteral([], slurp=all)

    def argspec_items(self):
        slurpy = None
        argspec_item = self.argspec_item()
        args = [argspec_item]
        if self._peek(self.argspec_items_rsts) == '","':
            self._scan('","')
            if self._peek(self.argspec_items_rsts_) not in self.argspec_chks_:
                _token_ = self._peek(self.argspec_items_rsts__)
                if _token_ == 'SLURPYVAR':
                    SLURPYVAR = self._scan('SLURPYVAR')
                    DOTDOTDOT = self._scan('DOTDOTDOT')
                    slurpy = SLURPYVAR
                elif _token_ == 'DOTDOTDOT':
                    DOTDOTDOT = self._scan('DOTDOTDOT')
                    slurpy = all
                else:  # in self.argspec_items_chks
                    argspec_items = self.argspec_items()
                    more_args, slurpy = argspec_items
                    args.extend(more_args)
        return args, slurpy

    def argspec_item(self):
        _token_ = self._peek(self.argspec_items_chks)
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
            if _token_ == 'RPAR':
                v = ListLiteral([], comma=False)
            elif _token_ not in self.argspec_item_chks:
                expr_map = self.expr_map()
                v = expr_map
            else:  # in self.argspec_item_chks
                expr_lst = self.expr_lst()
                v = expr_lst
            RPAR = self._scan('RPAR')
            return Parentheses(v)
        elif _token_ == '"url"':
            self._scan('"url"')
            LPAR = self._scan('LPAR')
            interpolated_url = self.interpolated_url()
            RPAR = self._scan('RPAR')
            print("url!"); return interpolated_url
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            LPAR = self._scan('LPAR')
            argspec = self.argspec()
            RPAR = self._scan('RPAR')
            return CallOp(FNCT, argspec)
        elif _token_ == 'BANG_IMPORTANT':
            BANG_IMPORTANT = self._scan('BANG_IMPORTANT')
            return Literal(String(BANG_IMPORTANT, quotes=None))
        elif _token_ == 'BAREWORD':
            interpolated_bareword = self.interpolated_bareword()
            return Interpolation.maybe(interpolated_bareword)
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            UNITS = None
            if self._peek(self.atom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
            return Literal(Number(float(NUM), unit=UNITS))
        elif _token_ not in self.atom_chks:
            interpolated_string = self.interpolated_string()
            return interpolated_string
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return Literal(Color.from_hex(COLOR, literal=True))
        else:  # == 'VAR'
            VAR = self._scan('VAR')
            return Variable(VAR)

    def kwatom(self):
        _token_ = self._peek(self.kwatom_rsts)
        if _token_ == '":"':
            pass
        elif _token_ == 'KWID':
            KWID = self._scan('KWID')
            return Literal.from_bareword(KWID)
        elif _token_ == 'KWNUM':
            KWNUM = self._scan('KWNUM')
            UNITS = None
            if self._peek(self.kwatom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
            return Literal(Number(float(KWNUM), unit=UNITS))
        elif _token_ == 'KWSTR':
            KWSTR = self._scan('KWSTR')
            return Literal(String(dequote(KWSTR), quotes="'"))
        elif _token_ == 'KWQSTR':
            KWQSTR = self._scan('KWQSTR')
            return Literal(String(dequote(KWQSTR), quotes='"'))
        elif _token_ == 'KWCOLOR':
            KWCOLOR = self._scan('KWCOLOR')
            return Literal(Color.from_hex(KWCOLOR, literal=True))
        else:  # == 'KWVAR'
            KWVAR = self._scan('KWVAR')
            return Variable(KWVAR)

    def interpolation(self):
        INTERP_START = self._scan('INTERP_START')
        expr_lst = self.expr_lst()
        INTERP_END = self._scan('INTERP_END')
        return expr_lst

    def interpolated_url(self):
        _token_ = self._peek(self.interpolated_url_rsts)
        if _token_ == 'BAREURL':
            interpolated_bare_url = self.interpolated_bare_url()
            return Interpolation.maybe(interpolated_bare_url, type=Url, quotes=None)
        elif _token_ == 'SINGLE_QUOTE':
            interpolated_string_single = self.interpolated_string_single()
            return Interpolation.maybe(interpolated_string_single, type=Url, quotes="'")
        else:  # == 'DOUBLE_QUOTE'
            interpolated_string_double = self.interpolated_string_double()
            return Interpolation.maybe(interpolated_string_double, type=Url, quotes='"')

    def interpolated_bare_url(self):
        BAREURL = self._scan('BAREURL')
        parts = [unescape(BAREURL)]
        while self._peek(self.interpolated_bare_url_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            BAREURL = self._scan('BAREURL')
            parts.append(unescape(BAREURL))
        return parts

    def interpolated_string(self):
        _token_ = self._peek(self.interpolated_string_rsts)
        if _token_ == 'SINGLE_QUOTE':
            interpolated_string_single = self.interpolated_string_single()
            return Interpolation.maybe(interpolated_string_single, quotes="'")
        else:  # == 'DOUBLE_QUOTE'
            interpolated_string_double = self.interpolated_string_double()
            return Interpolation.maybe(interpolated_string_double, quotes='"')

    def interpolated_string_single(self):
        SINGLE_QUOTE = self._scan('SINGLE_QUOTE')
        SINGLE_STRING_GUTS = self._scan('SINGLE_STRING_GUTS')
        parts = [unescape(SINGLE_STRING_GUTS)]
        while self._peek(self.interpolated_string_single_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            SINGLE_STRING_GUTS = self._scan('SINGLE_STRING_GUTS')
            parts.append(unescape(SINGLE_STRING_GUTS))
        SINGLE_QUOTE = self._scan('SINGLE_QUOTE')
        return parts

    def interpolated_string_double(self):
        DOUBLE_QUOTE = self._scan('DOUBLE_QUOTE')
        DOUBLE_STRING_GUTS = self._scan('DOUBLE_STRING_GUTS')
        parts = [unescape(DOUBLE_STRING_GUTS)]
        while self._peek(self.interpolated_string_double_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            DOUBLE_STRING_GUTS = self._scan('DOUBLE_STRING_GUTS')
            parts.append(unescape(DOUBLE_STRING_GUTS))
        DOUBLE_QUOTE = self._scan('DOUBLE_QUOTE')
        return parts

    def interpolated_bareword(self):
        BAREWORD = self._scan('BAREWORD')
        parts = [unescape(BAREWORD)]
        while self._peek(self.interpolated_bareword_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            BAREWORD = self._scan('BAREWORD')
            parts.append(unescape(BAREWORD))
        return parts

    def goal_interpolated_anything(self):
        INTERP_ANYTHING = self._scan('INTERP_ANYTHING')
        parts = [INTERP_ANYTHING]
        while self._peek(self.goal_interpolated_anything_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            INTERP_ANYTHING = self._scan('INTERP_ANYTHING')
            parts.append(INTERP_ANYTHING)
        END = self._scan('END')
        return Interpolation.maybe(parts)

    u_expr_chks = set(['"url"', 'LPAR', 'DOUBLE_QUOTE', 'COLOR', 'BAREWORD', 'NUM', 'FNCT', 'VAR', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    m_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'BAREWORD', '"url"', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    argspec_items_rsts = set(['RPAR', 'END', '","'])
    expr_map_rsts = set(['RPAR', '","'])
    argspec_items_rsts__ = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'SLURPYVAR', 'COLOR', 'DOTDOTDOT', 'SIGN', 'VAR', 'ADD', 'NUM', '"url"', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    kwatom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'KWCOLOR', '":"', 'KWNUM'])
    argspec_item_chks = set(['"url"', 'LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'COLOR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    a_expr_chks = set(['ADD', 'SUB'])
    expr_slst_rsts = set(['"url"', 'LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'END', 'COLOR', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'INTERP_END', 'BANG_IMPORTANT', 'SINGLE_QUOTE', '","'])
    interpolated_bareword_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', 'BAREWORD', '"url"', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    or_expr_rsts = set(['"url"', 'LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'END', 'SINGLE_QUOTE', 'COLOR', 'SIGN', 'VAR', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'INTERP_END', 'BANG_IMPORTANT', 'OR', '","'])
    interpolated_url_rsts = set(['DOUBLE_QUOTE', 'BAREURL', 'SINGLE_QUOTE'])
    interpolated_string_single_rsts = set(['SINGLE_QUOTE', 'INTERP_START'])
    and_expr_rsts = set(['AND', 'LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'END', 'SINGLE_QUOTE', 'COLOR', 'RPAR', 'SIGN', 'VAR', 'ADD', 'NUM', '"url"', 'FNCT', 'NOT', 'INTERP_END', 'BANG_IMPORTANT', 'OR', '","'])
    comparison_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'RPAR', 'INTERP_END', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'BAREWORD', '"url"', 'GT', 'END', 'SIGN', 'ADD', 'FNCT', 'VAR', 'EQ', 'AND', 'GE', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    argspec_chks = set(['DOTDOTDOT', 'SLURPYVAR'])
    atom_rsts_ = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'VAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'BAREWORD', '"url"', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'UNITS', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    interpolated_string_double_rsts = set(['DOUBLE_QUOTE', 'INTERP_START'])
    expr_map_rsts_ = set(['KWVAR', 'KWID', 'KWSTR', 'KWQSTR', 'RPAR', 'KWCOLOR', '":"', 'KWNUM', '","'])
    u_expr_rsts = set(['"url"', 'LPAR', 'DOUBLE_QUOTE', 'COLOR', 'SIGN', 'BAREWORD', 'ADD', 'NUM', 'FNCT', 'VAR', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    atom_chks = set(['COLOR', 'VAR'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    argspec_items_rsts_ = set(['KWVAR', 'LPAR', 'RPAR', 'BAREWORD', 'END', 'SLURPYVAR', 'COLOR', 'DOTDOTDOT', 'DOUBLE_QUOTE', 'SIGN', 'VAR', 'ADD', 'NUM', '"url"', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    a_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'INTERP_END', 'BANG_IMPORTANT', 'LE', 'COLOR', 'NE', 'LT', 'NUM', 'BAREWORD', '"url"', 'GT', 'END', 'SIGN', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    interpolated_string_rsts = set(['DOUBLE_QUOTE', 'SINGLE_QUOTE'])
    m_expr_chks = set(['MUL', 'DIV'])
    kwatom_rsts_ = set(['UNITS', '":"'])
    goal_interpolated_anything_rsts = set(['END', 'INTERP_START'])
    interpolated_bare_url_rsts = set(['RPAR', 'INTERP_START'])
    expr_lst_rsts = set(['INTERP_END', 'RPAR', 'END', '","'])
    argspec_items_chks = set(['KWVAR', '"url"', 'DOUBLE_QUOTE', 'BAREWORD', 'LPAR', 'COLOR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    argspec_rsts = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'BANG_IMPORTANT', 'END', 'SLURPYVAR', 'COLOR', 'BAREWORD', 'DOTDOTDOT', 'RPAR', 'VAR', 'ADD', 'NUM', '"url"', 'FNCT', 'NOT', 'SIGN', 'SINGLE_QUOTE'])
    atom_rsts = set(['KWVAR', 'KWID', 'KWSTR', 'BANG_IMPORTANT', 'LPAR', 'COLOR', 'BAREWORD', 'KWQSTR', 'SIGN', 'DOUBLE_QUOTE', 'RPAR', 'KWCOLOR', 'VAR', 'ADD', 'NUM', '"url"', '":"', 'NOT', 'KWNUM', 'SINGLE_QUOTE', 'FNCT'])
    argspec_chks_ = set(['END', 'RPAR'])
    argspec_rsts_ = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'BANG_IMPORTANT', 'END', 'COLOR', 'BAREWORD', 'SIGN', 'VAR', 'ADD', 'NUM', '"url"', 'FNCT', 'NOT', 'RPAR', 'SINGLE_QUOTE'])


