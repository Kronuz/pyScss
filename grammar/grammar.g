# python yapps2.py grammar.g grammar.py 
_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
ParserValue = lambda s: s
NumberValue = lambda s: float(s)
StringValue = lambda s: s
QuotedStringValue = lambda s: s
BooleanValue = lambda s: bool(s)
ColorValue = lambda s: s

def call(fn, args):
    print 'call: ',fn, args
    return args


#'|'.join(_units)
## Grammar compiled using Yapps:
%%
parser Calculator:
    ignore: "[ \r\t\n]+"

    token COMMA: ","
    token LPAR: "\\(|\\["
    token RPAR: "\\)|\\]"

    token END: "$"

    token MUL: "[*]"
    token DIV: "/"
    token ADD: "[+]"
    token SUB: "-\s"
    token SIGN: "-"
    token AND: "and"
    token OR: "or"
    token NOT: "not"
    token INV: "!"

    token EQ: "=="
    token NE: "!="
    token LT: "<"
    token GT: ">"
    token LE: "<="
    token GE: ">="

    token STR: "'[^']*'"
    token QSTR: '"[^"]*"'
    token UNITS: "px|cm|mm|hz|%"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token BOOL: "(?:true|false)"
    token COLOR: "#(?:[a-fA-F0-9]{8}|[a-fA-F0-9]{6}|[a-fA-F0-9]{3,4})"
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"

    rule goal:          expr                    {{ v = [ str(expr) ] }}
                        (
                            expr                {{ v.append(str(expr)) }}
                        )*                      
                        END                     {{ return v }}

    rule expr:          and_test                {{ v = and_test }}
                        (
                            OR and_test         {{ v = v or and_test }}
                        )*                      {{ return v }}

    rule and_test:      not_test                {{ v = not_test }}
                        (
                            AND not_test        {{ v = v and not_test }}
                        )*                      {{ return v }}

    rule not_test:      comparison              {{ return comparison }}
                        |
                        (
                            NOT not_test        {{ v = not not_test }}
                            |
                            INV not_test        {{ v = _inv('!', not_test) }}
                        )+                      {{ return v }}

    rule comparison:    or_expr                 {{ v = or_expr }}
                        (
                            LT or_expr          {{ v = v < or_expr }}
                            |
                            GT or_expr          {{ v = v > or_expr }}
                            |
                            LE or_expr          {{ v = v <= or_expr }}
                            |
                            GE or_expr          {{ v = v >= or_expr }}
                            |
                            EQ or_expr          {{ v = v == or_expr }}
                            |
                            NE or_expr          {{ v = v != or_expr }}
                        )*                      {{ return v }}

    rule or_expr:       and_expr                {{ v = and_expr }}
                        (
                            OR and_expr         {{ v = v or and_expr }}
                        )*                      {{ return v }}

    rule and_expr:      a_expr                  {{ v = a_expr }}
                        (
                            AND a_expr          {{ v = v and a_expr }}
                        )*                      {{ return v }}

    rule a_expr:        m_expr                  {{ v = m_expr }}
                        (
                            ADD m_expr          {{ v = v + m_expr }}
                            |
                            SUB m_expr          {{ v = v - m_expr }}
                        )*                      {{ return v }}

    rule m_expr:        u_expr                  {{ v = u_expr }}
                        (
                            MUL u_expr          {{ v = v * u_expr }}
                            |
                            DIV u_expr          {{ v = v / u_expr }}
                        )*                      {{ return v }}

    rule u_expr:        SIGN u_expr             {{ return _inv('-', u_expr) }}
                        |
                        ADD u_expr              {{ return u_expr }}
                        |
                        atom                    {{ v = atom }}
                        [
                            UNITS               {{ v = call(UNITS, [v, UNITS]) }}
                        ]                       {{ return v }}

    rule atom:          LPAR expr RPAR          {{ return expr }}
                        |
                        ID                      {{ v = ID }}
                        [
                            LPAR expr_lst RPAR  {{ return call(v, expr_lst) }}
                        ]                       {{ return v }}
                        |
                        NUM                     {{ return NumberValue(ParserValue(NUM)) }}
                        |
                        STR                     {{ return StringValue(ParserValue(STR)) }}
                        |
                        QSTR                    {{ return QuotedStringValue(ParserValue(QSTR)) }}
                        |
                        BOOL                    {{ return BooleanValue(ParserValue(BOOL)) }}
                        |
                        COLOR                   {{ return ColorValue(ParserValue(COLOR)) }}

    rule expr_lst:      expr                    {{ v = [expr] }}
                        (
                            [ COMMA ] expr      {{ v.append(expr) }}
                        )*                      {{ return v }}
%%
### Grammar ends.


if __name__ == '__main__':
    while 1:
        try: s = raw_input('>>> ')
        except EOFError: break
        if not strip(s): break
        print parse('goal', s)
    print 'Bye.'
