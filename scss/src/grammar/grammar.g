# python yapps2.py grammar.g grammar.py


_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
_inv = lambda s: s
ParserValue = lambda s: s
NumberValue = lambda s: float(s)
StringValue = lambda s: s
QuotedStringValue = lambda s: s
BooleanValue = lambda s: bool(s)
ColorValue = lambda s: s
class ListValue():
    def __init__(self, v):
        if isinstance(v, self.__class__):
            self.v = v
        else:
            self.v = {0: v}
    def first(self):
        return self.v[0]
    def __len__(self):
        return len(self.v)


def _reorder_list(lst):
    return dict((i if isinstance(k, int) else k, v) for i, (k, v) in enumerate(sorted(lst.items())))


def interpolate(v, R, library):
    return v


def call(fn, args, R, library, function=True):
    print 'call: ', fn, args
    return args

################################################################################
#'(?<!\\s)(?:' + '|'.join(_units) + ')(?![-\\w])'
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
    token UNITS: "(?<!\s)(?:px|cm|mm|hz|%)(?![-\w])"
    token NUM: "(?:\d+(?:\.\d*)?|\.\d+)"
    token BOOL: "(?<![-\w])(?:true|false)(?![-\w])"
    token COLOR: "#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])"
    token VAR: "\$[-a-zA-Z0-9_]+"
    token FNCT: "[-a-zA-Z_][-a-zA-Z0-9_]*(?=\()"
    token ID: "[-a-zA-Z_][-a-zA-Z0-9_]*"
    rule goal<<R>>:         expr_lst<<R>>                   {{ v = expr_lst }}
                              END                           {{ return v }}
    rule expr<<R>>:         and_test<<R>>                   {{ v = and_test }}
                              (
                                  OR and_test<<R>>          {{ v = AnyOp(v, and_test) }}
                              )*                            {{ return v }}
    rule and_test<<R>>:     not_test<<R>>                   {{ v = not_test }}
                              (
                                  AND not_test<<R>>         {{ v = AllOp(v, not_test) }}
                              )*                            {{ return v }}
    rule not_test<<R>>:     comparison<<R>>                 {{ return comparison }}
                              |
                              NOT not_test<<R>>             {{ return NotOp(not_test) }}
    rule comparison<<R>>:   a_expr<<R>>                     {{ v = a_expr }}
                              (
                                  LT a_expr<<R>>            {{ v = BinaryOp(operator.lt, v, a_expr) }}
                                  |
                                  GT a_expr<<R>>            {{ v = BinaryOp(operator.gt, v, a_expr) }}
                                  |
                                  LE a_expr<<R>>            {{ v = BinaryOp(operator.le, v, a_expr) }}
                                  |
                                  GE a_expr<<R>>            {{ v = BinaryOp(operator.ge, v, a_expr) }}
                                  |
                                  EQ a_expr<<R>>            {{ v = BinaryOp(operator.eq, v, a_expr) }}
                                  |
                                  NE a_expr<<R>>            {{ v = BinaryOp(operator.ne, v, a_expr) }}
                              )*                            {{ return v }}
    rule a_expr<<R>>:       m_expr<<R>>                     {{ v = m_expr }}
                              (
                                  ADD m_expr<<R>>           {{ v = BinaryOp(operator.add, v, m_expr) }}
                                  |
                                  SUB m_expr<<R>>           {{ v = BinaryOp(operator.sub, v, m_expr) }}
                              )*                            {{ return v }}
    rule m_expr<<R>>:       u_expr<<R>>                     {{ v = u_expr }}
                              (
                                  MUL u_expr<<R>>           {{ v = BinaryOp(operator.mul, v, u_expr) }}
                                  |
                                  DIV u_expr<<R>>           {{ v = BinaryOp(operator.div, v, u_expr) }}
                              )*                            {{ return v }}
    rule u_expr<<R>>:       SIGN u_expr<<R>>                {{ return UnaryOp(operator.neg, u_expr) }}
                              |
                              ADD u_expr<<R>>               {{ return UnaryOp(operator.pos, u_expr) }}
                              |
                              atom<<R>>                     {{ return atom }}
    rule atom<<R>>:         LPAR expr_lst<<R>> RPAR         {{ return expr_lst }}
                              |
                              ID                            {{ return Literal(StringValue(ID)) }}
                              |
                              FNCT                          {{ v = ArgspecLiteral([]) }}
                              LPAR [
                                  argspec<<R>>              {{ v = argspec }}
                              ] RPAR                        {{ return CallOp(FNCT, v) }}
                              |
                              NUM [
                                  UNITS                     {{ return Literal(NumberValue(float(NUM), type=UNITS)) }}
                              ]                             {{ return Literal(NumberValue(float(NUM))) }}
                              |
                              STR                           {{ return Literal(StringValue(ParserValue(STR))) }}
                              |
                              QSTR                          {{ return Literal(QuotedStringValue(ParserValue(QSTR))) }}
                              |
                              BOOL                          {{ return Literal(BooleanValue(ParserValue(BOOL))) }}
                              |
                              COLOR                         {{ return Literal(ColorValue(ParserValue(COLOR))) }}
                              |
                              VAR                           {{ return Variable(VAR) }}
    rule argspec<<R>>:      argspec_item<<R>>               {{ v = [argspec_item] }}
                              (
                                  COMMA
                                  argspec_item<<R>>         {{ v.append(argspec_item) }}
                              )*                            {{ return ArgspecLiteral(v) }}
    rule argspec_item<<R>>:                                 {{ var = None }}
                              [
                                VAR
                                [ ":"                       {{ var = VAR }}
                                ]                           {{ else: self._rewind() }}
                              ]
                              expr_slst<<R>>                {{ return (var, expr_slst) }}
    rule expr_lst<<R>>:     expr_slst<<R>>                  {{ v = [expr_slst] }}
                              (
                                  COMMA
                                  expr_slst<<R>>            {{ v.append(expr_slst) }}
                              )*                            {{ return ListLiteral(v) if len(v) > 1 else v[0] }}
    rule expr_slst<<R>>:    expr<<R>>                       {{ v = [expr] }}
                              (
                                  expr<<R>>                 {{ v.append(expr) }}
                              )*                            {{ return ListLiteral(v, comma=False) if len(v) > 1 else v[0] }}
%%
    expr_lst_rsts_ = None

    def __init__(self, scanner, library):
        self._library = library
        super(Calculator, self).__init__(scanner)


### Grammar ends.
################################################################################

P = Calculator(CalculatorScanner())


def parse(rule, text, *args):
    P.reset(text)
    return wrap_error_reporter(P, rule, *args)


if __name__ == '__main__':
    while True:
        try:
            s = raw_input('>>> ')
        except EOFError:
            break
        if not s.strip():
            break
        print parse('goal', s, None)
    print 'Bye.'
