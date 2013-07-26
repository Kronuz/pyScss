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
    token KWSTR: "'[^']*'(?=\s*:)"
    token STR: "'[^']*'"
    token KWQSTR: '"[^"]*"(?=\s*:)'
    token QSTR: '"[^"]*"'
    token UNITS: "(?<!\s)(?:[a-zA-Z]+|%)(?![-\w])"
    token KWNUM: "(?:\d+(?:\.\d*)?|\.\d+)(?=\s*:)"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token KWCOLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])(?=\s*:)"
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token KWVAR: "\$[-a-zA-Z0-9_]+(?=\s*:)"
    token VAR: "\$[-a-zA-Z0-9_]+"
    token FNCT: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\()"
    token KWID: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\s*:)"
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"
    token BANG_IMPORTANT: "!important"
    token LINTERP: "#[{]"
    token RINTERP: "[}]"
    token SQUOT: "'"
    token DQUOT: '"'
    token SQCHAR: "([^'#]|#(?![{]))*"
    token DQCHAR: '([^"#]|#(?![{]))*'

    # Goals:
    rule goal:          expr_lst END                {{ return expr_lst }}

    rule goal_argspec:  argspec END                 {{ return argspec }}

    # Arguments:
    rule argspec:       argspec_item                {{ argpairs = [argspec_item] }}
                        (
                            ","                     {{ argspec_item = (None, None) }}
                            [ argspec_item ]        {{ argpairs.append(argspec_item) }}
                        )*                          {{ return ArgspecLiteral(argpairs) }}

    rule argspec_item:
                        KWVAR ":" expr_slst         {{ return (Variable(KWVAR), expr_slst) }}
                        | expr_slst                 {{ return (None, expr_slst) }}

    # Maps:
    rule expr_map:      map_item                    {{ pairs = [map_item] }}
                        (
                            ","                     {{ map_item = (None, None) }}
                            [ map_item ]            {{ pairs.append(map_item) }}
                        )*                          {{ return MapLiteral(pairs) }}

    rule map_item:      kwatom ":" expr_slst        {{ return (kwatom, expr_slst) }}

    # Lists:
    rule expr_lst:      expr_slst                   {{ v = [expr_slst] }}
                        (
                            ","
                            expr_slst               {{ v.append(expr_slst) }}
                        )*                          {{ return ListLiteral(v) if len(v) > 1 else v[0] }}

    # Expressions:
    rule expr_slst:     or_expr                     {{ v = [or_expr] }}
                        (
                            or_expr                 {{ v.append(or_expr) }}
                        )*                          {{ return ListLiteral(v, comma=False) if len(v) > 1 else v[0] }}

    rule or_expr:       and_expr                    {{ v = and_expr }}
                        (
                            OR and_expr             {{ v = AnyOp(v, and_expr) }}
                        )*                          {{ return v }}

    rule and_expr:      not_expr                    {{ v = not_expr }}
                        (
                            AND not_expr            {{ v = AllOp(v, not_expr) }}
                        )*                          {{ return v }}

    rule not_expr:      comparison                  {{ return comparison }}
                        | NOT not_expr              {{ return NotOp(not_expr) }}

    rule comparison:    a_expr                      {{ v = a_expr }}
                        (
                            LT a_expr               {{ v = BinaryOp(operator.lt, v, a_expr) }}
                            | GT a_expr             {{ v = BinaryOp(operator.gt, v, a_expr) }}
                            | LE a_expr             {{ v = BinaryOp(operator.le, v, a_expr) }}
                            | GE a_expr             {{ v = BinaryOp(operator.ge, v, a_expr) }}
                            | EQ a_expr             {{ v = BinaryOp(operator.eq, v, a_expr) }}
                            | NE a_expr             {{ v = BinaryOp(operator.ne, v, a_expr) }}
                        )*                          {{ return v }}

    rule a_expr:        m_expr                      {{ v = m_expr }}
                        (
                            ADD m_expr              {{ v = BinaryOp(operator.add, v, m_expr) }}
                            | SUB m_expr            {{ v = BinaryOp(operator.sub, v, m_expr) }}
                        )*                          {{ return v }}

    rule m_expr:        u_expr                      {{ v = u_expr }}
                        (
                            MUL u_expr              {{ v = BinaryOp(operator.mul, v, u_expr) }}
                            | DIV u_expr            {{ v = BinaryOp(operator.truediv, v, u_expr) }}
                        )*                          {{ return v }}

    rule u_expr:        SIGN u_expr                 {{ return UnaryOp(operator.neg, u_expr) }}
                        | ADD u_expr                {{ return UnaryOp(operator.pos, u_expr) }}
                        | atom                      {{ return atom }}

    rule atom:          LPAR (
                            expr_map                {{ v = expr_map }}
                            | expr_lst              {{ v = expr_lst }}
                        ) RPAR                      {{ return Parentheses(v) }}
                        | FNCT                      {{ argspec = ArgspecLiteral([]) }}
                            LPAR [ argspec ] RPAR   {{ return CallOp(FNCT, argspec) }}
                        | BANG_IMPORTANT            {{ return Literal(String(BANG_IMPORTANT, quotes=None)) }}
                        | ID                        {{ return Literal(parse_bareword(ID)) }}
                        | NUM                       {{ UNITS = None }}
                            [ UNITS ]               {{ return Literal(Number(float(NUM), unit=UNITS)) }}
                        | COLOR                     {{ return Literal(Color(ParserValue(COLOR))) }}
                        | SQUOT
                            SQCHAR                  {{ v = Literal(String(SQCHAR, quotes="'")) }}
                            (
                                LINTERP
                                expr_lst
                                RINTERP
                                SQCHAR              {{ v = Interpolation(v, expr_lst, Literal(String(SQCHAR, quotes="'")), quotes="'") }}
                            )*
                            SQUOT                   {{ return v }}
                        | DQUOT
                            DQCHAR                  {{ v = Literal(String(DQCHAR, quotes='"')) }}
                            (
                                LINTERP
                                expr_lst
                                RINTERP
                                DQCHAR              {{ v = Interpolation(v, expr_lst, Literal(String(DQCHAR, quotes='"')), quotes='"') }}
                            )*
                            DQUOT                   {{ return v }}
                        | VAR                       {{ return Variable(VAR) }}

    rule kwatom:
                        | KWID                      {{ return Literal(parse_bareword(KWID)) }}
                        | KWNUM                     {{ UNITS = None }}
                            [ UNITS ]               {{ return Literal(Number(float(KWNUM), unit=UNITS)) }}
                        | KWSTR                     {{ return Literal(String(KWSTR[1:-1], quotes="'")) }}
                        | KWQSTR                    {{ return Literal(String(KWQSTR[1:-1], quotes='"')) }}
                        | KWCOLOR                   {{ return Literal(Color(ParserValue(KWCOLOR))) }}
                        | KWVAR                     {{ return Variable(KWVAR) }}
%%
### Grammar ends.
################################################################################
