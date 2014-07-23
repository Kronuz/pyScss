# python yapps2.py grammar.g grammar.py

################################################################################
## Grammar compiled using Yapps:
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
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"
    token BANG_IMPORTANT: "!important"
    # http://dev.w3.org/csswg/css-syntax-3/#consume-a-url-token0
    # URLs may not contain quotes, parentheses, or unprintables
    # TODO reify escapes, for this and for strings
    # FIXME: Also, URLs may not contain $ as it breaks urls with variables?
    token URL: "(?:[\\\\].|[^$'\"()\\x00-\\x08\\x0b\\x0e-\\x1f\\x7f])*"

    # Goals:
    rule goal:          expr_lst END                {{ return expr_lst }}

    rule goal_argspec:  argspec END                 {{ return argspec }}

    # Arguments:
    # Note that at the moment, named arguments and slurpy arguments appear to
    # be incompatible.
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
        | "url" LPAR
            (
                URL                 {{ quotes = None }}
                | "\"" URL "\""     {{ quotes = '"' }}
                | "'" URL "'"       {{ quotes = "'" }}
            )
            RPAR                    {{ return Literal(Url(URL, quotes=quotes)) }}
        | FNCT LPAR argspec RPAR    {{ return CallOp(FNCT, argspec) }}
        | BANG_IMPORTANT            {{ return Literal(String(BANG_IMPORTANT, quotes=None)) }}
        | ID                        {{ return Literal(parse_bareword(ID)) }}
        | NUM                       {{ UNITS = None }}
            [ UNITS ]               {{ return Literal(Number(float(NUM), unit=UNITS)) }}
        | STR                       {{ return Literal(String(dequote(STR), quotes="'")) }}
        | QSTR                      {{ return Literal(String(dequote(QSTR), quotes='"')) }}
        | COLOR                     {{ return Literal(Color.from_hex(COLOR, literal=True)) }}
        | VAR                       {{ return Variable(VAR) }}

    rule kwatom:
        # nothing
        | KWID                      {{ return Literal(parse_bareword(KWID)) }}
        | KWNUM                     {{ UNITS = None }}
            [ UNITS ]               {{ return Literal(Number(float(KWNUM), unit=UNITS)) }}
        | KWSTR                     {{ return Literal(String(dequote(KWSTR), quotes="'")) }}
        | KWQSTR                    {{ return Literal(String(dequote(KWQSTR), quotes='"')) }}
        | KWCOLOR                   {{ return Literal(Color.from_hex(KWCOLOR, literal=True)) }}
        | KWVAR                     {{ return Variable(KWVAR) }}

%%
### Grammar ends.
################################################################################
