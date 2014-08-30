"""Grammar for parsing Sass expressions."""
# This is a GENERATED FILE -- DO NOT EDIT DIRECTLY!
# Edit scss/grammar/expression.g, then run:
#
#     python2 yapps2.py scss/grammar/expression.g
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

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
from scss.types import Function
from scss.types import Number
from scss.types import String
from scss.types import Url
from scss.util import dequote

from scss.grammar import Parser
from scss.grammar import Scanner



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
        ('DOTDOTDOT', '[.]{3}'),
        ('SINGLE_QUOTE', "'"),
        ('DOUBLE_QUOTE', '"'),
        ('SINGLE_STRING_GUTS', "([^'\\\\#]|[\\\\].|#(?![{]))*"),
        ('DOUBLE_STRING_GUTS', '([^"\\\\#]|[\\\\].|#(?![{]))*'),
        ('STR', "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"),
        ('QSTR', '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"'),
        ('UNITS', '(?<!\\s)(?:[a-zA-Z]+|%)(?![-\\w])'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('KWVAR', '\\$[-a-zA-Z0-9_]+(?=\\s*:)'),
        ('SLURPYVAR', '\\$[-a-zA-Z0-9_]+(?=[.][.][.])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('LITERAL_FUNCTION', '(calc|expression|progid:[\\w.]+)(?=[(])'),
        ('URL_FUNCTION', 'url(?=[(])'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('BAREWORD', '[-a-zA-Z_][-a-zA-Z0-9_]*'),
        ('BANG_IMPORTANT', '!important'),
        ('INTERP_START', '#[{]'),
        ('INTERP_END', '[}]'),
        ('INTERP_ANYTHING', '([^#]|#(?![{]))*'),
        ('INTERP_NO_PARENS', '([^#()]|#(?![{]))*'),
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

    def expr_map_or_list(self):
        expr_slst = self.expr_slst()
        first = expr_slst
        _token_ = self._peek(self.expr_map_or_list_rsts)
        if _token_ == '":"':
            self._scan('":"')
            expr_slst = self.expr_slst()
            pairs = [(first, expr_slst)]
            while self._peek(self.expr_map_or_list_rsts_) == '","':
                self._scan('","')
                map_item = None, None
                if self._peek(self.expr_map_or_list_rsts__) not in self.expr_map_or_list_rsts_:
                    map_item = self.map_item()
                pairs.append(map_item)
            return MapLiteral(pairs)
        else:  # in self.expr_map_or_list_rsts_
            items = [first]; use_list = False
            while self._peek(self.expr_map_or_list_rsts_) == '","':
                self._scan('","')
                use_list = True
                expr_slst = self.expr_slst()
                items.append(expr_slst)
            return ListLiteral(items) if use_list else items[0]

    def map_item(self):
        atom = self.atom()
        self._scan('":"')
        expr_slst = self.expr_slst()
        return (atom, expr_slst)

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
        while self._peek(self.expr_slst_rsts) not in self.expr_slst_chks:
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
            else:  # in self.argspec_item_chks
                expr_map_or_list = self.expr_map_or_list()
                v = expr_map_or_list
            RPAR = self._scan('RPAR')
            return Parentheses(v)
        elif _token_ == 'URL_FUNCTION':
            URL_FUNCTION = self._scan('URL_FUNCTION')
            LPAR = self._scan('LPAR')
            interpolated_url = self.interpolated_url()
            RPAR = self._scan('RPAR')
            return interpolated_url
        elif _token_ == 'LITERAL_FUNCTION':
            LITERAL_FUNCTION = self._scan('LITERAL_FUNCTION')
            LPAR = self._scan('LPAR')
            interpolated_function = self.interpolated_function()
            RPAR = self._scan('RPAR')
            return Interpolation.maybe(interpolated_function, type=Function, function_name=LITERAL_FUNCTION)
        elif _token_ == 'FNCT':
            FNCT = self._scan('FNCT')
            LPAR = self._scan('LPAR')
            argspec = self.argspec()
            RPAR = self._scan('RPAR')
            return CallOp(FNCT, argspec)
        elif _token_ == 'BANG_IMPORTANT':
            BANG_IMPORTANT = self._scan('BANG_IMPORTANT')
            return Literal(String(BANG_IMPORTANT, quotes=None))
        elif _token_ in self.atom_chks:
            interpolated_bareword = self.interpolated_bareword()
            return Interpolation.maybe(interpolated_bareword)
        elif _token_ == 'NUM':
            NUM = self._scan('NUM')
            UNITS = None
            if self._peek(self.atom_rsts_) == 'UNITS':
                UNITS = self._scan('UNITS')
            return Literal(Number(float(NUM), unit=UNITS))
        elif _token_ not in self.atom_chks_:
            interpolated_string = self.interpolated_string()
            return interpolated_string
        elif _token_ == 'COLOR':
            COLOR = self._scan('COLOR')
            return Literal(Color.from_hex(COLOR, literal=True))
        else:  # == 'VAR'
            VAR = self._scan('VAR')
            return Variable(VAR)

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
        parts = [BAREURL]
        while self._peek(self.interpolated_bare_url_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            BAREURL = self._scan('BAREURL')
            parts.append(BAREURL)
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
        _token_ = self._peek(self.atom_chks)
        if _token_ == 'BAREWORD':
            BAREWORD = self._scan('BAREWORD')
            parts = [BAREWORD]
        else:  # == 'INTERP_START'
            interpolation = self.interpolation()
            parts = ['', interpolation]
            BAREWORD = ''
            if self._peek(self.interpolated_bareword_rsts) == 'BAREWORD':
                BAREWORD = self._scan('BAREWORD')
            parts.append(BAREWORD)
        while self._peek(self.interpolated_bareword_rsts_) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            BAREWORD = ''
            if self._peek(self.interpolated_bareword_rsts) == 'BAREWORD':
                BAREWORD = self._scan('BAREWORD')
            parts.append(BAREWORD)
        return parts

    def interpolated_function(self):
        interpolated_function_parens = self.interpolated_function_parens()
        parts = interpolated_function_parens
        while self._peek(self.interpolated_bare_url_rsts) == 'INTERP_START':
            interpolation = self.interpolation()
            parts.append(interpolation)
            interpolated_function_parens = self.interpolated_function_parens()
            parts.extend(interpolated_function_parens)
        return parts

    def interpolated_function_parens(self):
        INTERP_NO_PARENS = self._scan('INTERP_NO_PARENS')
        parts = [INTERP_NO_PARENS]
        while self._peek(self.interpolated_function_parens_rsts) == 'LPAR':
            LPAR = self._scan('LPAR')
            interpolated_function = self.interpolated_function()
            parts = parts[:-1] + [parts[-1] + LPAR + interpolated_function[0]] + interpolated_function[0:]
            RPAR = self._scan('RPAR')
            INTERP_NO_PARENS = self._scan('INTERP_NO_PARENS')
            parts[-1] += RPAR + INTERP_NO_PARENS
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

    atom_chks_ = set(['COLOR', 'VAR'])
    expr_map_or_list_rsts__ = set(['LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'RPAR', 'VAR', 'NUM', 'FNCT', 'LITERAL_FUNCTION', 'BANG_IMPORTANT', 'SINGLE_QUOTE', '","'])
    u_expr_chks = set(['LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'VAR', 'NUM', 'FNCT', 'LITERAL_FUNCTION', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    m_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'LITERAL_FUNCTION', 'GT', 'END', 'SIGN', 'BAREWORD', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    argspec_items_rsts = set(['RPAR', 'END', '","'])
    expr_slst_chks = set(['INTERP_END', 'RPAR', 'END', '":"', '","'])
    expr_lst_rsts = set(['INTERP_END', 'END', '","'])
    expr_map_or_list_rsts = set(['RPAR', '":"', '","'])
    argspec_item_chks = set(['LPAR', 'DOUBLE_QUOTE', 'VAR', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    a_expr_chks = set(['ADD', 'SUB'])
    interpolated_function_parens_rsts = set(['LPAR', 'RPAR', 'INTERP_START'])
    expr_slst_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'VAR', 'END', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'FNCT', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'RPAR', '":"', 'NOT', 'INTERP_END', 'BANG_IMPORTANT', 'SINGLE_QUOTE', '","'])
    interpolated_bareword_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'BAREWORD', 'GT', 'END', 'SIGN', 'LITERAL_FUNCTION', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    or_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'VAR', 'END', 'SINGLE_QUOTE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'FNCT', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'RPAR', '":"', 'NOT', 'INTERP_END', 'BANG_IMPORTANT', 'OR', '","'])
    argspec_chks_ = set(['END', 'RPAR'])
    interpolated_string_single_rsts = set(['SINGLE_QUOTE', 'INTERP_START'])
    interpolated_bareword_rsts_ = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'LITERAL_FUNCTION', 'GT', 'END', 'SIGN', 'BAREWORD', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    and_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'RPAR', 'INTERP_END', 'BANG_IMPORTANT', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NUM', '":"', 'BAREWORD', 'END', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'FNCT', 'VAR', 'AND', 'OR', 'NOT', 'SINGLE_QUOTE', '","'])
    comparison_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'RPAR', 'INTERP_END', 'BANG_IMPORTANT', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'LITERAL_FUNCTION', 'GT', 'END', 'SIGN', 'BAREWORD', 'ADD', 'FNCT', 'VAR', 'EQ', 'AND', 'GE', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    argspec_chks = set(['DOTDOTDOT', 'SLURPYVAR'])
    atom_rsts_ = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'VAR', 'MUL', 'INTERP_END', 'BANG_IMPORTANT', 'DIV', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'LITERAL_FUNCTION', 'GT', 'END', 'SIGN', 'BAREWORD', 'GE', 'FNCT', 'UNITS', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    interpolated_string_double_rsts = set(['DOUBLE_QUOTE', 'INTERP_START'])
    expr_map_or_list_rsts_ = set(['RPAR', '","'])
    u_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'BAREWORD', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'SIGN', 'VAR', 'ADD', 'NUM', 'FNCT', 'LITERAL_FUNCTION', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    atom_chks = set(['BAREWORD', 'INTERP_START'])
    interpolated_url_rsts = set(['DOUBLE_QUOTE', 'BAREURL', 'SINGLE_QUOTE'])
    comparison_chks = set(['GT', 'GE', 'NE', 'LT', 'LE', 'EQ'])
    argspec_items_rsts_ = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'VAR', 'END', 'SLURPYVAR', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'DOTDOTDOT', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'RPAR', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    a_expr_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'SUB', 'RPAR', 'INTERP_END', 'BANG_IMPORTANT', 'LE', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'NE', 'LT', 'NUM', '":"', 'LITERAL_FUNCTION', 'GT', 'END', 'SIGN', 'BAREWORD', 'GE', 'FNCT', 'VAR', 'EQ', 'AND', 'ADD', 'SINGLE_QUOTE', 'NOT', 'OR', '","'])
    interpolated_string_rsts = set(['DOUBLE_QUOTE', 'SINGLE_QUOTE'])
    m_expr_chks = set(['MUL', 'DIV'])
    goal_interpolated_anything_rsts = set(['END', 'INTERP_START'])
    interpolated_bare_url_rsts = set(['RPAR', 'INTERP_START'])
    argspec_items_chks = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'VAR', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    argspec_rsts = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'BANG_IMPORTANT', 'END', 'SLURPYVAR', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'DOTDOTDOT', 'RPAR', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'VAR', 'FNCT', 'NOT', 'SIGN', 'SINGLE_QUOTE'])
    atom_rsts = set(['LPAR', 'DOUBLE_QUOTE', 'BANG_IMPORTANT', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'VAR', 'FNCT', 'NOT', 'RPAR', 'SINGLE_QUOTE'])
    argspec_items_rsts__ = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'VAR', 'SLURPYVAR', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'DOTDOTDOT', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'FNCT', 'NOT', 'BANG_IMPORTANT', 'SINGLE_QUOTE'])
    argspec_rsts_ = set(['KWVAR', 'LPAR', 'DOUBLE_QUOTE', 'BANG_IMPORTANT', 'END', 'URL_FUNCTION', 'INTERP_START', 'COLOR', 'BAREWORD', 'SIGN', 'LITERAL_FUNCTION', 'ADD', 'NUM', 'VAR', 'FNCT', 'NOT', 'RPAR', 'SINGLE_QUOTE'])


