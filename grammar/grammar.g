# python yapps2.py grammar.g grammar.py 
def _reorder_list(lst):
    return dict((i if isinstance(k, int) else k, v) for i, (k, v) in enumerate(sorted(lst.items())))

_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
ParserValue = lambda s: s
NumberValue = lambda s: float(s)
StringValue = lambda s: s
QuotedStringValue = lambda s: s
BooleanValue = lambda s: bool(s)
ColorValue = lambda s: s
ListValue = lambda s: s
_inv = lambda s: s

def call(fn, args, C, O, function=True):
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
    token SIGN: "-(?![a-zA-Z_])"
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
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token VAR: "\$[-a-zA-Z0-9_]+"
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"

    rule goal<<C,O>>:         expr_lst<<C,O>>               {{ v = expr_lst }}
                              END                           {{ return v }}
                                                            
    rule expr<<C,O>>:         and_test<<C,O>>               {{ v = and_test }}
                              (                             
                                  OR and_test<<C,O>>        {{ v = v or and_test }}
                              )*                            {{ return v }}
                                                            
    rule and_test<<C,O>>:     not_test<<C,O>>               {{ v = not_test }}
                              (                             
                                  AND not_test<<C,O>>       {{ v = v and not_test }}
                              )*                            {{ return v }}
                                                            
    rule not_test<<C,O>>:     comparison<<C,O>>             {{ return comparison }}
                              |                             
                              (                             
                                  NOT not_test<<C,O>>       {{ v = not not_test }}
                                  |                         
                                  INV not_test<<C,O>>       {{ v = _inv('!', not_test) }}
                              )+                            {{ return v }}
                                                            
    rule comparison<<C,O>>:   or_expr<<C,O>>                {{ v = or_expr }}
                              (                             
                                  LT or_expr<<C,O>>         {{ v = v < or_expr }}
                                  |                         
                                  GT or_expr<<C,O>>         {{ v = v > or_expr }}
                                  |                         
                                  LE or_expr<<C,O>>         {{ v = v <= or_expr }}
                                  |                         
                                  GE or_expr<<C,O>>         {{ v = v >= or_expr }}
                                  |                         
                                  EQ or_expr<<C,O>>         {{ v = v == or_expr }}
                                  |                         
                                  NE or_expr<<C,O>>         {{ v = v != or_expr }}
                              )*                            {{ return v }}
                                                            
    rule or_expr<<C,O>>:      and_expr<<C,O>>               {{ v = and_expr }}
                              (                             
                                  OR and_expr<<C,O>>        {{ v = v or and_expr }}
                              )*                            {{ return v }}
                                                            
    rule and_expr<<C,O>>:     a_expr<<C,O>>                 {{ v = a_expr }}
                              (                             
                                  AND a_expr<<C,O>>         {{ v = v and a_expr }}
                              )*                            {{ return v }}
                                                            
    rule a_expr<<C,O>>:       m_expr<<C,O>>                 {{ v = m_expr }}
                              (                             
                                  ADD m_expr<<C,O>>         {{ v = v + m_expr }}
                                  |                         
                                  SUB m_expr<<C,O>>         {{ v = v - m_expr }}
                              )*                            {{ return v }}
                                                            
    rule m_expr<<C,O>>:       u_expr<<C,O>>                 {{ v = u_expr }}
                              (                             
                                  MUL u_expr<<C,O>>         {{ v = v * u_expr }}
                                  |                         
                                  DIV u_expr<<C,O>>         {{ v = v / u_expr }}
                              )*                            {{ return v }}
                                                            
    rule u_expr<<C,O>>:       SIGN u_expr<<C,O>>            {{ return _inv('-', u_expr) }}
                              |                             
                              ADD u_expr<<C,O>>             {{ return u_expr }}
                              |                             
                              atom<<C,O>>                   {{ v = atom }}
                              [                             
                                  UNITS                     {{ v = call(UNITS, ListValue(ParserValue({ 0: v, 1: UNITS })), C, O, False) }}
                              ]                             {{ return v }}
                                                            
    rule atom<<C,O>>:         LPAR expr_lst<<C,O>> RPAR     {{ return expr_lst.first() if len(expr_lst) == 1 else expr_lst }}
                              |                             
                              ID                            {{ v = ID }}
                              [                             {{ v = None }}
                                  LPAR [
                                      expr_lst<<C,O>>       {{ v = expr_lst }}
                                  ] RPAR                    {{ return call(ID, v, C, O) }}
                              ]                             {{ return v }}
                              |                             
                              NUM                           {{ return NumberValue(ParserValue(NUM)) }}
                              |                             
                              STR                           {{ return StringValue(ParserValue(STR)) }}
                              |                             
                              QSTR                          {{ return QuotedStringValue(ParserValue(QSTR)) }}
                              |                             
                              BOOL                          {{ return BooleanValue(ParserValue(BOOL)) }}
                              |                             
                              COLOR                         {{ return ColorValue(ParserValue(COLOR)) }}
                                                            
    rule expr_lst<<C,O>>:                                   {{ n = None }}
                              [                             
                                  VAR ":"                   {{ n = VAR }}
                              ]                             
                              expr_slst<<C,O>>              {{ v = { n or 0: expr_slst } }}
                              (                             {{ n = None }}
                                  COMMA                     {{ v['_'] = COMMA }}
                                  [                         
                                      VAR ":"               {{ n = VAR }}
                                  ]                         
                                  expr_slst<<C,O>>          {{ v[n or len(v)] = expr_slst }}
                              )*                            {{ return ListValue(ParserValue(v)) }}

    rule expr_slst<<C,O>>:    expr<<C,O>>                   {{ v = { 0: expr } }}
                              (                             
                                  expr<<C,O>>               {{ v[len(v)] = expr }}
                              )*                            {{ return ListValue(ParserValue(v)) if len(v) > 1 else v[0] }}
%%
### Grammar ends.


if __name__ == '__main__':
    while True:
        try: s = raw_input('>>> ')
        except EOFError: break
        if not s.strip(): break
        print parse('goal', s, {}, {})
    print 'Bye.'
