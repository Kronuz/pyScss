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
from scss.ast import FunctionLiteral
from scss.ast import AlphaFunctionLiteral
from scss.cssdefs import unescape
from scss.types import Color
from scss.types import Function
from scss.types import Number
from scss.types import String
from scss.types import Url

from scss.grammar import Parser
from scss.grammar import Scanner


%%
parser SassExpression:
    # These need to go before the ignore, so they match first, and we don't
    # lose spaces inside a string or other interpolation!
    # Don't allow quotes or # unless they're escaped (or the # is alone)
    token SINGLE_STRING_GUTS: '([^\'\\\\#]|[\\\\].|#(?![{]))*'
    token DOUBLE_STRING_GUTS: "([^\"\\\\#]|[\\\\].|#(?![{]))*"
    token INTERP_ANYTHING: "([^#]|#(?![{]))*"
    token INTERP_NO_VARS: "([^#$]|#(?![{]))*"
    token INTERP_NO_PARENS: "([^#()]|#(?![{]))*"

    # This is a stupid lookahead used for diverting url(#{...}) to its own
    # branch; otherwise it would collide with the atom rule.
    token INTERP_START_URL_HACK:  "(?=[#][{])"
    token INTERP_START: "#[{]"

    token SPACE: "[ \r\t\n]+"

    # Now we can list the ignore token and everything else.
    ignore: "[ \r\t\n]+"
    token LPAR: "\\(|\\["
    token RPAR: "\\)|\\]"
    token END: "$"
    token MUL: "[*]"
    token DIV: "/"
    token MOD: "(?<=\s)%"
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

    # Must appear before BAREWORD, so url(foo) parses as a URL
    # http://dev.w3.org/csswg/css-syntax-3/#consume-a-url-token0
    # Bare URLs may not contain quotes, parentheses, unprintables, or space.
    # TODO reify escapes, for this and for strings
    # FIXME: Also, URLs may not contain $ as it breaks urls with variables?
    token BAREURL_HEAD_HACK: "((?:[\\\\].|[^#$'\"()\\x00-\\x08\\x0b\\x0e-\\x20\\x7f]|#(?![{]))+)(?=#[{]|\s*[)])"
    token BAREURL: "(?:[\\\\].|[^#$'\"()\\x00-\\x08\\x0b\\x0e-\\x20\\x7f]|#(?![{]))+"

    token UNITS: "(?<!\s)(?:[a-zA-Z]+|%)(?![-\w])"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token KWVAR: "\$[-a-zA-Z0-9_]+(?=\s*:)"
    token SLURPYVAR: "\$[-a-zA-Z0-9_]+(?=[.][.][.])"
    token VAR: "\$[-a-zA-Z0-9_]+"

    # Cheating, to make sure these only match function names.
    # The last of these is the IE filter nonsense
    token LITERAL_FUNCTION: "(calc|expression|progid:[\w.]+)(?=[(])"
    token ALPHA_FUNCTION: "alpha(?=[(])"
    token URL_FUNCTION: "url(?=[(])"
    # This must come AFTER the above
    token FNCT: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\()"

    # TODO Ruby is a bit more flexible here, for example allowing 1#{2}px
    token BAREWORD: "(?!\d)(\\\\[0-9a-fA-F]{1,6}|\\\\.|[-a-zA-Z0-9_])+"
    token BANG_IMPORTANT: "!\s*important"

    token INTERP_END: "[}]"

    # -------------------------------------------------------------------------
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


    # Maps, which necessarily overlap with lists because LL(1):
    rule expr_map_or_list:
        expr_slst                   {{ first = expr_slst }}
        (   # Colon means this is a map
            ":"
            expr_slst               {{ pairs = [(first, expr_slst)] }}
            (
                ","                 {{ map_item = None, None }}
                [ map_item ]        {{ pairs.append(map_item) }}
            )*                      {{ return MapLiteral(pairs) }}
        |   # Comma means this is a comma-delimited list
                                    {{ items = [first]; use_list = False }}
            (
                ","                 {{ use_list = True }}
                expr_slst           {{ items.append(expr_slst) }}
            )*                      {{ return ListLiteral(items) if use_list else items[0] }}
        )

    rule map_item:
        expr_slst                   {{ left = expr_slst }}
        ":" expr_slst               {{ return (left, expr_slst) }}


    # Lists:
    rule expr_lst:
        # TODO a trailing comma makes a list now, i believe
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
            | MOD u_expr            {{ v = BinaryOp(operator.mod, v, u_expr) }}
        )*                          {{ return v }}

    rule u_expr:
        SIGN u_expr                 {{ return UnaryOp(operator.neg, u_expr) }}
        | ADD u_expr                {{ return UnaryOp(operator.pos, u_expr) }}
        | atom                      {{ return atom }}

    rule atom:
        LPAR (
                                    {{ v = ListLiteral([], comma=False) }}
            | expr_map_or_list      {{ v = expr_map_or_list }}
        ) RPAR                      {{ return Parentheses(v) }}
        # Special functions.  Note that these technically overlap with the
        # regular function rule, which makes this not quite LL -- but they're
        # different tokens so yapps can't tell, and it resolves the conflict by
        # picking the first one.
        # TODO Ruby sass somehow allows a full expression in here too
        | URL_FUNCTION LPAR interpolated_url RPAR
            {{ return interpolated_url }}
        # alpha() is a built-in Sass function, but it's also part of the old IE
        # filter syntax, where it appears as alpha(opacity=NN).  Since = isn't
        # normally valid Sass, we have to special-case it here
        | ALPHA_FUNCTION LPAR (
            "opacity" "=" atom RPAR
                {{ return AlphaFunctionLiteral(atom) }}
            | argspec RPAR          {{ return CallOp("alpha", argspec) }}
            )
        | LITERAL_FUNCTION LPAR interpolated_function RPAR
            {{ return Interpolation.maybe(interpolated_function, type=Function, function_name=LITERAL_FUNCTION) }}
        | FNCT LPAR argspec RPAR    {{ return CallOp(FNCT, argspec) }}
        | BANG_IMPORTANT            {{ return Literal(String.unquoted("!important", literal=True)) }}
        | interpolated_bareword     {{ return Interpolation.maybe(interpolated_bareword) }}
        | NUM                       {{ UNITS = None }}
            [ UNITS ]               {{ return Literal(Number(float(NUM), unit=UNITS)) }}
        | interpolated_string       {{ return interpolated_string }}
        | COLOR                     {{ return Literal(Color.from_hex(COLOR, literal=True)) }}
        | VAR                       {{ return Variable(VAR) }}

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
        # Note: This rule DOES NOT include the url(...) delimiters.
        # Parsing a URL is finnicky: it can wrap an expression like any other
        # function call, OR it can wrap a literal URL (like regular ol' CSS
        # syntax) but possibly with Sass interpolations.
        # The string forms of url(), of course, are just special cases of
        # expressions.
        # The exact rules aren't documented, but after some experimentation, I
        # think Sass assumes a literal if it sees either #{} or the end of the
        # call before it sees a space, and an expression otherwise.
        # Translating that into LL is tricky.  We can't look for
        # interpolations, because interpolations are also expressions, and
        # left-factoring this would be a nightmare.  So instead the first rule
        # has some wacky lookahead tokens; see below.
        interpolated_bare_url
            {{ return Interpolation.maybe(interpolated_bare_url, type=Url, quotes=None) }}
        | expr_lst
            {{ return FunctionLiteral(expr_lst, "url") }}

    rule interpolated_bare_url:
        (
            # This token is identical to BASEURL, except that it ends with a
            # lookahead asserting that the next thing is either an
            # interpolation, OR optional whitespace and a closing paren.
            BAREURL_HEAD_HACK       {{ parts = [BAREURL_HEAD_HACK] }}
            # And this token merely checks that an interpolation comes next --
            # because if it does, we want the grammar to come down THIS path
            # rather than going down expr_lst and into atom (which also looks
            # for INTERP_START).
            | INTERP_START_URL_HACK  {{ parts = [''] }}
        )
        (
            interpolation           {{ parts.append(interpolation) }}
            ( BAREURL               {{ parts.append(BAREURL) }}
                | SPACE             {{ return parts }}
                |                   {{ parts.append('') }}
            )
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
        # This one is slightly fiddly because it can't be /completely/ empty,
        # and any space between tokens ends the bareword (via early return).
        # TODO yapps2 is spitting out warnings for the BAREWORD shenanigans,
        # because it's technically ambiguous with a spaced list of barewords --
        # but SPACE will match first in practice and yapps2 doesn't know that
        (
            BAREWORD                {{ parts = [BAREWORD] }}
            [ SPACE                 {{ return parts }}
            ]
            |
            interpolation           {{ parts = ['', interpolation] }}
            ( BAREWORD              {{ parts.append(BAREWORD) }}
                | SPACE             {{ return parts }}
                |                   {{ parts.append('') }}
            )
        )
        (
            interpolation           {{ parts.append(interpolation) }}
            ( BAREWORD              {{ parts.append(BAREWORD) }}
                | SPACE             {{ return parts }}
                |                   {{ parts.append('') }}
            )
        )*                          {{ return parts }}

    rule interpolated_function:
        # Completely arbitrary text, but with balanced parentheses.
        interpolated_function_parens        {{ parts = interpolated_function_parens }}
        (
            interpolation                   {{ parts.append(interpolation) }}
            interpolated_function_parens    {{ parts.extend(interpolated_function_parens) }}
        )*                                  {{ return parts }}

    rule interpolated_function_parens:
        INTERP_NO_PARENS            {{ parts = [INTERP_NO_PARENS] }}
        (
            LPAR
            interpolated_function   {{ parts = parts[:-1] + [parts[-1] + LPAR + interpolated_function[0]] + interpolated_function[1:] }}
            RPAR
            INTERP_NO_PARENS        {{ parts[-1] += RPAR + INTERP_NO_PARENS }}
        )*                          {{ return parts }}


    rule goal_interpolated_literal:
        # This isn't part of the grammar, but rather a separate goal, used for
        # text that might contain interpolations but should not be parsed
        # outside of them -- e.g., selector strings.
        INTERP_ANYTHING             {{ parts = [INTERP_ANYTHING] }}
        (
            interpolation           {{ parts.append(interpolation) }}
            INTERP_ANYTHING         {{ parts.append(INTERP_ANYTHING) }}
        )*
        END                         {{ return Interpolation.maybe(parts) }}

    rule goal_interpolated_literal_with_vars:
        # Another goal used for literal text that might contain interpolations
        # OR variables.  Created for the header of @media blocks.
        INTERP_NO_VARS              {{ parts = [INTERP_NO_VARS] }}
        (
            (
                interpolation       {{ parts.append(interpolation) }}
                | VAR               {{ parts.append(Variable(VAR)) }}
            )
            INTERP_NO_VARS          {{ parts.append(INTERP_NO_VARS) }}
        )*
        END                         {{ return Interpolation.maybe(parts) }}

%%
