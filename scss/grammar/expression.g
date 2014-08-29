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
from scss.types import Number
from scss.types import String
from scss.types import Url
from scss.util import dequote

from scss.grammar import Parser
from scss.grammar import Scanner


%%
parser SassExpression:
    ignore: "[ \r\t\n]+"
    token LPAR: "\\(|\\["
    token RPAR: "\\)|\\]"
    token END: "$"
    token MUL: "[*]"
    token DIV: "/"
    token ADD: "[+]"
    token SUB: "-\s"
    token SIGN: "-(?![a-zA-Z_])"
    token AND: "(?<![-\w])and(?![-\w])"
    token OR: "(?<![-\w])or(?![-\w])"
    token NOT: "(?<![-\w])not(?![-\w])"
    token NE: "!="
    token INV: "!"
    token EQ: "=="
    token LE: "<="
    token GE: ">="
    token LT: "<"
    token GT: ">"
    token DOTDOTDOT: '[.]{3}'
    token SINGLE_QUOTE: "'"
    token DOUBLE_QUOTE: '"'
    # Don't allow quotes or # unless they're escaped (or the # is alone)
    token SINGLE_STRING_GUTS: '([^\'\\\\#]|[\\\\].|#(?![{]))*'
    token DOUBLE_STRING_GUTS: "([^\"\\\\#]|[\\\\].|#(?![{]))*"
    token KWSTR: "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'(?=\s*:)"
    token STR: "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"
    token KWQSTR: '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"(?=\s*:)'
    token QSTR: '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"'
    token UNITS: "(?<!\s)(?:[a-zA-Z]+|%)(?![-\w])"
    token KWNUM: "(?:\d+(?:\.\d*)?|\.\d+)(?=\s*:)"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token KWCOLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])(?=\s*:)"
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token KWVAR: "\$[-a-zA-Z0-9_]+(?=\s*:)"
    token SLURPYVAR: "\$[-a-zA-Z0-9_]+(?=[.][.][.])"
    token VAR: "\$[-a-zA-Z0-9_]+"
    token FNCT: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\()"
    token KWID: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\s*:)"
    # TODO Ruby is a bit more flexible here, for example allowing 1#{2}px
    token BAREWORD: "[-a-zA-Z_][-a-zA-Z0-9_]*"
    token BANG_IMPORTANT: "!important"

    token INTERP_START: "#[{]"
    token INTERP_END: "[}]"
    token INTERP_ANYTHING: "([^#]|#(?![{]))*"
    # http://dev.w3.org/csswg/css-syntax-3/#consume-a-url-token0
    # Bare URLs may not contain quotes, parentheses, or unprintables.  Quoted
    # URLs may, of course, contain whatever they like.
    # TODO reify escapes, for this and for strings
    # FIXME: Also, URLs may not contain $ as it breaks urls with variables?
    token BAREURL: "(?:[\\\\].|[^#$'\"()\\x00-\\x08\\x0b\\x0e-\\x1f\\x7f]|#(?![{]))*"

    # Goals:
    rule goal:          expr_lst END                {{ return expr_lst }}

    rule goal_argspec:  argspec END                 {{ return argspec }}

    # Arguments:
    # TODO should support multiple slurpies, and enforce (probably not in the
    # parser) that positional args come first
    rule argspec:
        [
            argspec_items           {{ args, slurpy = argspec_items }}
                                    {{ return ArgspecLiteral(args, slurp=slurpy) }}
        ]                           {{ return ArgspecLiteral([]) }}
        | SLURPYVAR DOTDOTDOT       {{ return ArgspecLiteral([], slurp=SLURPYVAR) }}
        | DOTDOTDOT                 {{ return ArgspecLiteral([], slurp=all) }}

    rule argspec_items:
                                    {{ slurpy = None }}
        argspec_item                {{ args = [argspec_item] }}
        [ "," [
            SLURPYVAR DOTDOTDOT     {{ slurpy = SLURPYVAR }}
            | DOTDOTDOT             {{ slurpy = all }}
            | argspec_items         {{ more_args, slurpy = argspec_items }}
                                    {{ args.extend(more_args) }}
        ] ]                         {{ return args, slurpy }}

    rule argspec_item:
        KWVAR ":" expr_slst         {{ return (Variable(KWVAR), expr_slst) }}
        | expr_slst                 {{ return (None, expr_slst) }}


    # Maps:
    rule expr_map:
        map_item                    {{ pairs = [map_item] }}
        (
            ","                     {{ map_item = (None, None) }}
            [ map_item ]            {{ pairs.append(map_item) }}
        )*                          {{ return MapLiteral(pairs) }}

    rule map_item:
        kwatom ":" expr_slst        {{ return (kwatom, expr_slst) }}


    # Lists:
    rule expr_lst:
        expr_slst                   {{ v = [expr_slst] }}
        (
            ","
            expr_slst               {{ v.append(expr_slst) }}
        )*                          {{ return ListLiteral(v) if len(v) > 1 else v[0] }}


    # Expressions:
    rule expr_slst:
        or_expr                     {{ v = [or_expr] }}
        (
            or_expr                 {{ v.append(or_expr) }}
        )*                          {{ return ListLiteral(v, comma=False) if len(v) > 1 else v[0] }}

    rule or_expr:
        and_expr                    {{ v = and_expr }}
        (
            OR and_expr             {{ v = AnyOp(v, and_expr) }}
        )*                          {{ return v }}

    rule and_expr:
        not_expr                    {{ v = not_expr }}
        (
            AND not_expr            {{ v = AllOp(v, not_expr) }}
        )*                          {{ return v }}

    rule not_expr:
        comparison                  {{ return comparison }}
        | NOT not_expr              {{ return NotOp(not_expr) }}

    rule comparison:
        a_expr                      {{ v = a_expr }}
        (
            LT a_expr               {{ v = BinaryOp(operator.lt, v, a_expr) }}
            | GT a_expr             {{ v = BinaryOp(operator.gt, v, a_expr) }}
            | LE a_expr             {{ v = BinaryOp(operator.le, v, a_expr) }}
            | GE a_expr             {{ v = BinaryOp(operator.ge, v, a_expr) }}
            | EQ a_expr             {{ v = BinaryOp(operator.eq, v, a_expr) }}
            | NE a_expr             {{ v = BinaryOp(operator.ne, v, a_expr) }}
        )*                          {{ return v }}

    rule a_expr:
        m_expr                      {{ v = m_expr }}
        (
            ADD m_expr              {{ v = BinaryOp(operator.add, v, m_expr) }}
            | SUB m_expr            {{ v = BinaryOp(operator.sub, v, m_expr) }}
        )*                          {{ return v }}

    rule m_expr:
        u_expr                      {{ v = u_expr }}
        (
            MUL u_expr              {{ v = BinaryOp(operator.mul, v, u_expr) }}
            | DIV u_expr            {{ v = BinaryOp(operator.truediv, v, u_expr) }}
        )*                          {{ return v }}

    rule u_expr:
        SIGN u_expr                 {{ return UnaryOp(operator.neg, u_expr) }}
        | ADD u_expr                {{ return UnaryOp(operator.pos, u_expr) }}
        | atom                      {{ return atom }}

    rule atom:
        LPAR (
                                    {{ v = ListLiteral([], comma=False) }}
            | expr_map              {{ v = expr_map }}
            | expr_lst              {{ v = expr_lst }}
        ) RPAR                      {{ return Parentheses(v) }}
        # Special functions.  Note that these technically overlap with the
        # regular function rule, which makes this not quite LL -- but they're
        # different tokens so yapps can't tell, and it resolves the conflict by
        # picking the first one.
        | "url" LPAR interpolated_url RPAR
                                    {{ print("url!"); return interpolated_url }}
        | FNCT LPAR argspec RPAR    {{ return CallOp(FNCT, argspec) }}
        | BANG_IMPORTANT            {{ return Literal(String(BANG_IMPORTANT, quotes=None)) }}
        | interpolated_bareword     {{ return Interpolation.maybe(interpolated_bareword) }}
        | NUM                       {{ UNITS = None }}
            [ UNITS ]               {{ return Literal(Number(float(NUM), unit=UNITS)) }}
        | interpolated_string       {{ return interpolated_string }}
        | COLOR                     {{ return Literal(Color.from_hex(COLOR, literal=True)) }}
        | VAR                       {{ return Variable(VAR) }}

    # TODO none of these things respect interpolation -- would love to not need
    # to repeat all the rules
    rule kwatom:
        # nothing
        | KWID                      {{ return Literal.from_bareword(KWID) }}
        | KWNUM                     {{ UNITS = None }}
            [ UNITS ]               {{ return Literal(Number(float(KWNUM), unit=UNITS)) }}
        | KWSTR                     {{ return Literal(String(dequote(KWSTR), quotes="'")) }}
        | KWQSTR                    {{ return Literal(String(dequote(KWQSTR), quotes='"')) }}
        | KWCOLOR                   {{ return Literal(Color.from_hex(KWCOLOR, literal=True)) }}
        | KWVAR                     {{ return Variable(KWVAR) }}

    # -------------------------------------------------------------------------
    # Interpolation, which is a right mess, because it depends very heavily on
    # context -- what other characters are allowed, and when do we stop?
    # Thankfully these rules all look pretty similar: there's a delimiter, a
    # literal, and some number of interpolations and trailing literals.
    rule interpolation:
        INTERP_START
        expr_lst
        INTERP_END                  {{ return expr_lst }}

    rule interpolated_url:
        # Note: This rule DOES NOT include the url(...) delimiters
        interpolated_bare_url
            {{ return Interpolation.maybe(interpolated_bare_url, type=Url, quotes=None) }}
        | interpolated_string_single
            {{ return Interpolation.maybe(interpolated_string_single, type=Url, quotes="'") }}
        | interpolated_string_double
            {{ return Interpolation.maybe(interpolated_string_double, type=Url, quotes='"') }}

    rule interpolated_bare_url:
        BAREURL                     {{ parts = [unescape(BAREURL)] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            BAREURL                 {{ parts.append(unescape(BAREURL)) }}
        )*                          {{ return parts }}

    rule interpolated_string:
        interpolated_string_single
            {{ return Interpolation.maybe(interpolated_string_single, quotes="'") }}
        | interpolated_string_double
            {{ return Interpolation.maybe(interpolated_string_double, quotes='"') }}

    rule interpolated_string_single:
        SINGLE_QUOTE
        SINGLE_STRING_GUTS          {{ parts = [unescape(SINGLE_STRING_GUTS)] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            SINGLE_STRING_GUTS      {{ parts.append(unescape(SINGLE_STRING_GUTS)) }}
        )*
        SINGLE_QUOTE                {{ return parts }}
        
    rule interpolated_string_double:
        DOUBLE_QUOTE
        DOUBLE_STRING_GUTS          {{ parts = [unescape(DOUBLE_STRING_GUTS)] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            DOUBLE_STRING_GUTS      {{ parts.append(unescape(DOUBLE_STRING_GUTS)) }}
        )*
        DOUBLE_QUOTE                {{ return parts }}
        
    rule interpolated_bareword:
        # Again, a bareword has a fairly limited set of allowed characters
        BAREWORD                    {{ parts = [unescape(BAREWORD)] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            BAREWORD                {{ parts.append(unescape(BAREWORD)) }}
        )*                          {{ return parts }}


    rule goal_interpolated_anything:
        # This isn't part of the grammar, but rather a separate goal, used for
        # text that might contain interpolations but should not be parsed
        # outside of them -- e.g., selector strings.
        INTERP_ANYTHING             {{ parts = [INTERP_ANYTHING] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            INTERP_ANYTHING         {{ parts.append(INTERP_ANYTHING) }}
        )*
        END                         {{ return Interpolation.maybe(parts) }}

%%
