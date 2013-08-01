# python yapps2.py grammar.g grammar.py

################################################################################
## Grammar compiled using Yapps:
%%
parser SassExpression:
    ignore: "[ \r\t\n]+"
    token COMMA: ","
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
    token STR: "'[^']*'"
    token QSTR: '"[^"]*"'
    token UNITS: "(?<!\s)(?:[a-zA-Z]+|%)(?![-\w])"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token VAR: "\$[-a-zA-Z0-9_]+"
    token FNCT: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\()"
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"

    rule goal:          expr_lst                    {{ v = expr_lst }}
                        END                         {{ return v }}

    rule expr:          and_test                    {{ v = and_test }}
                        (
                            OR and_test             {{ v = AnyOp(v, and_test) }}
                        )*                          {{ return v }}

    rule and_test:      not_test                    {{ v = not_test }}
                        (
                            AND not_test            {{ v = AllOp(v, not_test) }}
                        )*                          {{ return v }}

    rule not_test:      comparison                  {{ return comparison }}
                        | NOT not_test              {{ return NotOp(not_test) }}

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
                            | DIV u_expr            {{ v = BinaryOp(operator.div, v, u_expr) }}
                        )*                          {{ return v }}

    rule u_expr:        SIGN u_expr                 {{ return UnaryOp(operator.neg, u_expr) }}
                        | ADD u_expr                {{ return UnaryOp(operator.pos, u_expr) }}
                        | atom                      {{ return atom }}

    rule atom:          LPAR expr_lst RPAR          {{ return Parentheses(expr_lst) }}
                        | ID                        {{ return Literal(parse_bareword(ID)) }}
                        | FNCT                      {{ v = ArgspecLiteral([]) }}
                            LPAR [
                                argspec             {{ v = argspec }}
                            ] RPAR                  {{ return CallOp(FNCT, v) }}
                        | NUM [
                                UNITS               {{ return Literal(NumberValue(float(NUM), unit=UNITS.lower())) }}
                            ]                       {{ return Literal(NumberValue(float(NUM))) }}
                        | STR                       {{ return Literal(String(STR[1:-1], quotes="'")) }}
                        | QSTR                      {{ return Literal(String(QSTR[1:-1], quotes='"')) }}
                        | COLOR                     {{ return Literal(ColorValue(ParserValue(COLOR))) }}
                        | VAR                       {{ return Variable(VAR) }}

    rule argspec:       argspec_item                {{ v = [argspec_item] }}
                        (
                            COMMA
                            argspec_item            {{ v.append(argspec_item) }}
                        )*                          {{ return ArgspecLiteral(v) }}

    rule argspec_item:                              {{ var = None }}
                        [
                            VAR
                            [ ":"                   {{ var = VAR }}
                            ]                       {{ else: self._rewind() }}
                        ]
                        expr_slst                   {{ return (var, expr_slst) }}

    rule expr_lst:      expr_slst                   {{ v = [expr_slst] }}
                        (
                            COMMA
                            expr_slst               {{ v.append(expr_slst) }}
                        )*                          {{ return ListLiteral(v) if len(v) > 1 else v[0] }}

    rule expr_slst:     expr                        {{ v = [expr] }}
                        (
                            expr                    {{ v.append(expr) }}
                        )*                          {{ return ListLiteral(v, comma=False) if len(v) > 1 else v[0] }}
%%

### Grammar ends.
################################################################################
