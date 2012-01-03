#!/usr/bin/env python

# Yapps 3.0 - yet another python parser system
# Amit J Patel, January 1999
# German M. Bravo, December 2011
# See http://theory.stanford.edu/~amitp/Yapps/ for documentation and updates

# v3.0.0 changes (December 2011)
# * PEP 8 cleanups
# * Optimizations in the scanning (added cache and cleanup() for it)
# v2.0.1 changes (October 2001):
# * The exceptions inherit the standard Exception class (thanks Rich Salz)
# * The scanner can use either a different set of regular expressions
#   per instance, or allows the subclass to define class fields with
#   the patterns.  This improves performance when many Scanner objects
#   are being created, because the regular expressions don't have to
#   be recompiled each time. (thanks Amaury Forgeot d'Arc)
# v2.0.2 changes (April 2002)
# * Bug fix: generating the 'else' clause when the comment was too
#   long.  v2.0.1 was missing a newline.  (thanks Steven Engelhardt)
# v2.0.3 changes (August 2002)
# * Bug fix: inline tokens using the r"" syntax.
# v.2.0.4 changes (July 2003)
# * Style change: Replaced `expr` with repr(expr)
# * Style change: Changed (b >= a and b < c) into (a <= b < c)
# * Bug fix: identifiers in grammar rules that had digits in them were
#   not accessible in the {{python code}} section
# * Bug fix: made the SyntaxError exception class call
#   Exception.__init__ (thanks Alex Verstak)
# * Style change: replaced raise "string exception" with raise
#   ClassException(...) (thanks Alex Verstak)

from yappsrt import *
import sys
import re


INDENT = " " * 4


class Generator:
    def __init__(self, name, options, tokens, rules):
        self.change_count = 0
        self.name = name
        self.options = options
        self.preparser = ''
        self.postparser = None

        self.tokens = {}  # Map from tokens to regexps
        self.sets = {}  # Map for restriction sets
        self.ignore = []  # List of token names to ignore in parsing
        self.terminals = []  # List of token names (to maintain ordering)

        for n, t in tokens:
            if n == '#ignore':
                n = t
                self.ignore.append(n)
            if n in self.tokens.keys() and self.tokens[n] != t:
                if n not in self.ignore:
                    print 'Warning: token', n, 'multiply defined.'
            else:
                self.terminals.append(n)
            self.tokens[n] = t

        self.rules = {}  # Map from rule names to parser nodes
        self.params = {}  # Map from rule names to parameters
        self.goals = []  # List of rule names (to maintain ordering)
        for n, p, r in rules:
            self.params[n] = p
            self.rules[n] = r
            self.goals.append(n)

        self.output = sys.stdout

    def __getitem__(self, name):
        # Get options
        return self.options.get(name, 0)

    def non_ignored_tokens(self):
        return filter(lambda x, i=self.ignore: x not in i, self.terminals)

    def changed(self):
        self.change_count = 1 + self.change_count

    def subset(self, a, b):
        "See if all elements of a are inside b"
        for x in a:
            if x not in b:
                return 0
        return 1

    def equal_set(self, a, b):
        "See if a and b have the same elements"
        if len(a) != len(b):
            return 0
        if a == b:
            return 1
        return self.subset(a, b) and self.subset(b, a)

    def add_to(self, parent, additions):
        "Modify parent to include all elements in additions"
        for x in additions:
            if x not in parent:
                parent.append(x)
                self.changed()

    def equate(self, a, b):
        self.add_to(a, b)
        self.add_to(b, a)

    def write(self, *args):
        for a in args:
            self.output.write(a)

    def in_test(self, r, x, full, b):
        if not b:
            return '0'
        if len(b) == 1:
            return '%s == %s' % (x, repr(b[0]))
        if full and len(b) > len(full) / 2:
            # Reverse the sense of the test.
            not_b = filter(lambda x, b=b:
            x not in b, full)
            return self.not_in_test(r, x, full, not_b)
        n = None
        for k, v in self.sets.items():
            if v == b:
                n = k
        if n is None:
            n = '%s_chks' % r
            while n in self.sets:
                n += '_'
            self.sets[n] = b
        b_set = 'self.%s' % n
        return '%s in %s' % (x, b_set)

    def not_in_test(self, r, x, full, b):
        if not b:
            return '1'
        if len(b) == 1:
            return '%s != %s' % (x, repr(b[0]))
        n = None
        for k, v in self.sets.items():
            if v == b:
                n = k
        if n is None:
            n = '%s_chks' % r
            while n in self.sets:
                n += '_'
            self.sets[n] = b
        b_set = 'self.%s' % n
        return '%s not in %s' % (x, b_set)

    def peek_call(self, r, a):
        n = None
        for k, v in self.sets.items():
            if v == a:
                n = k
        if n is None:
            n = '%s_rsts' % r
            while n in self.sets:
                n += '_'
            self.sets[n] = a
        a_set = 'self.%s' % n
        if self.equal_set(a, self.non_ignored_tokens()):
            a_set = ''
        if self['context-insensitive-scanner']:
            a_set = ''
        return 'self._peek(%s)' % a_set

    def peek_test(self, r, a, b):
        if self.subset(a, b):
            return '1'
        if self['context-insensitive-scanner']:
            a = self.non_ignored_tokens()
        return self.in_test(r, self.peek_call(r, a), a, b)

    def not_peek_test(self, r, a, b):
        if self.subset(a, b):
            return '0'
        return self.not_in_test(r, self.peek_call(r, a), a, b)

    def calculate(self):
        while 1:
            for r in self.goals:
                self.rules[r].setup(self, r)
            if self.change_count == 0:
                break
            self.change_count = 0

        while 1:
            for r in self.goals:
                self.rules[r].update(self)
            if self.change_count == 0:
                break
            self.change_count = 0

    def dump_information(self):
        self.calculate()
        for r in self.goals:
            print '    _____' + '_' * len(r)
            print ('___/Rule ' + r + '\\' + '_' * 80)[:79]
            queue = [self.rules[r]]
            while queue:
                top = queue[0]
                del queue[0]

                print repr(top)
                top.first.sort()
                top.follow.sort()
                eps = []
                if top.accepts_epsilon:
                    eps = ['(null)']
                print '     FIRST:', join(top.first + eps, ', ')
                print '    FOLLOW:', join(top.follow, ', ')
                for x in top.get_children():
                    queue.append(x)

    def generate_output(self):

        self.calculate()
        self.write(self.preparser)
        # TODO: remove "import *" construct
        self.write("import re\n")
        self.write("from string import *\n")
        self.write("from yappsrt import *\n")
        self.write("\n\n")
        self.write("class ", self.name, "Scanner(Scanner):\n")
        self.write("    patterns = None\n")
        self.write("    _patterns = [\n")
        for p in self.terminals:
            self.write("        (%s, %s),\n" % (
                repr(p), repr(self.tokens[p])))
        self.write("    ]\n\n")
        self.write("    def __init__(self, input=None):\n")
        self.write("        if hasattr(self, 'setup_patterns'):\n")
        self.write("            self.setup_patterns(self._patterns)\n")
        self.write("        elif self.patterns is None:\n")
        self.write("            self.__class__.patterns = []\n")
        self.write("            for t, p in self._patterns:\n")
        self.write("                self.patterns.append((t, re.compile(p)))\n")
        self.write("        super(", self.name, "Scanner, self).__init__(None, %s, input)\n" %
                   repr(self.ignore))
        self.write("\n\n")

        self.write("class ", self.name, "(Parser):\n")
        for r in self.goals:
            self.write(INDENT, "def ", r, "(self")
            if self.params[r]:
                self.write(", ", self.params[r])
            self.write("):\n")
            self.rules[r].output(self, INDENT + INDENT)
            self.write("\n")

        for n, s in self.sets.items():
            self.write("    %s = %s\n" % (n, set(s)))

        if self.postparser is not None:
            self.write(self.postparser)
        else:
            self.write("\n")
            self.write("P = ", self.name, "(", self.name, "Scanner())\n")
            self.write("def parse(rule, text, *args):\n")
            self.write("    P.reset(text)\n")
            self.write("    return wrap_error_reporter(P, rule, *args)\n")
            self.write("\n")

            self.write("if __name__ == '__main__':\n")
            self.write(INDENT, "from sys import argv, stdin\n")
            self.write(INDENT, "if len(argv) >= 2:\n")
            self.write(INDENT * 2, "if len(argv) >= 3:\n")
            self.write(INDENT * 3, "f = open(argv[2],'r')\n")
            self.write(INDENT * 2, "else:\n")
            self.write(INDENT * 3, "f = stdin\n")
            self.write(INDENT * 2, "print parse(argv[1], f.read())\n")
            self.write(INDENT, "else: print 'Args:  <rule> [<filename>]'\n")


######################################################################


class Node:
    def __init__(self):
        self.first = []
        self.follow = []
        self.accepts_epsilon = 0
        self.rule = '?'

    def setup(self, gen, rule):
        # Setup will change accepts_epsilon,
        # sometimes from 0 to 1 but never 1 to 0.
        # It will take a finite number of steps to set things up
        self.rule = rule

    def used(self, vars):
        "Return two lists: one of vars used, and the other of vars assigned"
        return vars, []

    def get_children(self):
        "Return a list of sub-nodes"
        return []

    def __repr__(self):
        return str(self)

    def update(self, gen):
        if self.accepts_epsilon:
            gen.add_to(self.first, self.follow)

    def output(self, gen, indent):
        "Write out code to _gen_ with _indent_:string indentation"
        gen.write(indent, "assert 0  # Invalid parser node\n")


class Terminal(Node):
    def __init__(self, token):
        Node.__init__(self)
        self.token = token
        self.accepts_epsilon = 0

    def __str__(self):
        return self.token

    def update(self, gen):
        Node.update(self, gen)
        if self.first != [self.token]:
            self.first = [self.token]
            gen.changed()

    def output(self, gen, indent):
        gen.write(indent)
        if re.match('[a-zA-Z_][a-zA-Z_0-9]*$', self.token):
            gen.write(self.token, " = ")
        gen.write("self._scan(%s)\n" % repr(self.token))


class Eval(Node):
    def __init__(self, expr):
        Node.__init__(self)
        self.expr = expr

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '{{ %s }}' % self.expr.strip()

    def output(self, gen, indent):
        gen.write(indent, self.expr.strip(), '\n')


class NonTerminal(Node):
    def __init__(self, name, args):
        Node.__init__(self)
        self.name = name
        self.args = args

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        try:
            self.target = gen.rules[self.name]
            if self.accepts_epsilon != self.target.accepts_epsilon:
                self.accepts_epsilon = self.target.accepts_epsilon
                gen.changed()
        except KeyError:  # Oops, it's nonexistent
            print 'Error: no rule <%s>' % self.name
            self.target = self

    def __str__(self):
        return '<%s>' % self.name

    def update(self, gen):
        Node.update(self, gen)
        gen.equate(self.first, self.target.first)
        gen.equate(self.follow, self.target.follow)

    def output(self, gen, indent):
        gen.write(indent)
        gen.write(self.name, " = ")
        gen.write("self.", self.name, "(", self.args, ")\n")


class Sequence(Node):
    def __init__(self, *children):
        Node.__init__(self)
        self.children = children

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        for c in self.children:
            c.setup(gen, rule)

        if not self.accepts_epsilon:
            # If it's not already accepting epsilon, it might now do so.
            for c in self.children:
                # any non-epsilon means all is non-epsilon
                if not c.accepts_epsilon:
                    break
            else:
                self.accepts_epsilon = 1
                gen.changed()

    def get_children(self):
        return self.children

    def __str__(self):
        return '( %s )' % join(map(lambda x: str(x), self.children))

    def update(self, gen):
        Node.update(self, gen)
        for g in self.children:
            g.update(gen)

        empty = 1
        for g_i in range(len(self.children)):
            g = self.children[g_i]

            if empty:
                gen.add_to(self.first, g.first)
            if not g.accepts_epsilon:
                empty = 0

            if g_i == len(self.children) - 1:
                next = self.follow
            else:
                next = self.children[1 + g_i].first
            gen.add_to(g.follow, next)

        if self.children:
            gen.add_to(self.follow, self.children[-1].follow)

    def output(self, gen, indent):
        if self.children:
            for c in self.children:
                c.output(gen, indent)
        else:
            # Placeholder for empty sequences, just in case
            gen.write(indent, 'pass\n')

class Choice(Node):
    def __init__(self, *children):
        Node.__init__(self)
        self.children = children

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        for c in self.children:
            c.setup(gen, rule)

        if not self.accepts_epsilon:
            for c in self.children:
                if c.accepts_epsilon:
                    self.accepts_epsilon = 1
                    gen.changed()

    def get_children(self):
        return self.children

    def __str__(self):
        return '( %s )' % join(map(lambda x: str(x), self.children), ' | ')

    def update(self, gen):
        Node.update(self, gen)
        for g in self.children:
            g.update(gen)

        for g in self.children:
            gen.add_to(self.first, g.first)
            gen.add_to(self.follow, g.follow)
        for g in self.children:
            gen.add_to(g.follow, self.follow)
        if self.accepts_epsilon:
            gen.add_to(self.first, self.follow)

    def output(self, gen, indent):
        test = "if"
        gen.write(indent, "_token_ = ", gen.peek_call(self.rule, self.first), "\n")
        tokens_seen = []
        tokens_unseen = self.first[:]
        if gen['context-insensitive-scanner']:
            # Context insensitive scanners can return ANY token,
            # not only the ones in first.
            tokens_unseen = gen.non_ignored_tokens()
        for c in self.children:
            testset = c.first[:]
            removed = []
            for x in testset:
                if x in tokens_seen:
                    testset.remove(x)
                    removed.append(x)
                if x in tokens_unseen:
                    tokens_unseen.remove(x)
            tokens_seen = tokens_seen + testset
            if removed:
                if not testset:
                    print 'Error in rule', self.rule + ':', c, 'never matches.'
                else:
                    print 'Warning:', self
                print ' * These tokens are being ignored:', join(removed, ', ')
                print '   due to previous choices using them.'

            if testset:
                if not tokens_unseen:  # context sensitive scanners only!
                    if test == 'if':
                        # if it's the first AND last test, then
                        # we can simply put the code without an if/else
                        c.output(gen, indent)
                    else:
                        gen.write(indent, "else:")
                        t = gen.in_test(self.rule, '', [], testset)
                        if len(t) < 70 - len(indent):
                            gen.write("  #", t)
                        gen.write("\n")
                        c.output(gen, indent + INDENT)
                else:
                    gen.write(indent, test, " ",
                              gen.in_test(self.rule, '_token_', tokens_unseen, testset),
                              ":\n")
                    c.output(gen, indent + INDENT)
                test = "elif"

        if gen['context-insensitive-scanner'] and tokens_unseen:
            gen.write(indent, "else:\n")
            gen.write(indent, INDENT, "raise SyntaxError(self._pos, ")
            gen.write("'Could not match ", self.rule, "')\n")


class Wrapper(Node):
    def __init__(self, child):
        Node.__init__(self)
        self.child = child

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        self.child.setup(gen, rule)

    def get_children(self):
        return [self.child]

    def update(self, gen):
        Node.update(self, gen)
        self.child.update(gen)
        gen.add_to(self.first, self.child.first)
        gen.equate(self.follow, self.child.follow)


class Option(Wrapper):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '[ %s ]' % str(self.child)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule + ': contents may be empty.'
        gen.write(indent, "if %s:\n" %
                  gen.peek_test(self.rule, self.first, self.child.first))
        self.child.output(gen, indent + INDENT)


class Plus(Wrapper):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if self.accepts_epsilon != self.child.accepts_epsilon:
            self.accepts_epsilon = self.child.accepts_epsilon
            gen.changed()

    def __str__(self):
        return '%s+' % str(self.child)

    def update(self, gen):
        Wrapper.update(self, gen)
        gen.add_to(self.follow, self.first)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule + ':'
            print ' * The repeated pattern could be empty.  The resulting'
            print '   parser may not work properly.'
        gen.write(indent, "while 1:\n")
        self.child.output(gen, indent + INDENT)
        union = self.first[:]
        gen.add_to(union, self.follow)
        gen.write(indent + INDENT, "if %s:\n" %
                  gen.not_peek_test(self.rule, union, self.child.first))
        gen.write(indent + INDENT * 2, "break\n")


class Star(Plus):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '%s*' % str(self.child)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule + ':'
            print ' * The repeated pattern could be empty.  The resulting'
            print '   parser probably will not work properly.'
        gen.write(indent, "while %s:\n" %
                  gen.peek_test(self.rule, self.follow, self.child.first))
        self.child.output(gen, indent + INDENT)

######################################################################
# The remainder of this file is from parsedesc.{g,py}


def append(lst, x):
    "Imperative append"
    lst.append(x)
    return lst


def add_inline_token(tokens, str):
    tokens.insert(0, (str, eval(str, {}, {})))
    return Terminal(str)


def cleanup_choice(lst):
    if len(lst) == 0:
        return Sequence([])
    if len(lst) == 1:
        return lst[0]
    return apply(Choice, tuple(lst))


def cleanup_sequence(lst):
    if len(lst) == 1:
        return lst[0]
    return apply(Sequence, tuple(lst))


def cleanup_rep(node, rep):
    if rep == 'star':
        return Star(node)
    elif rep == 'plus':
        return Plus(node)
    else:
        return node


def resolve_name(tokens, id, args):
    if id in map(lambda x: x[0], tokens):
        # It's a token
        if args:
            print 'Warning: ignoring parameters on TOKEN %s<<%s>>' % (id, args)
        return Terminal(id)
    else:
        # It's a name, so assume it's a nonterminal
        return NonTerminal(id, args)


from string import *
from yappsrt import *


class ParserDescriptionScanner(Scanner):
    def __init__(self, str):
        Scanner.__init__(self, [
            ('"rule"', 'rule'),
            ('"ignore"', 'ignore'),
            ('"token"', 'token'),
            ('"option"', 'option'),
            ('":"', ':'),
            ('"parser"', 'parser'),
            ('[ \011\015\012]+', '[ \011\015\012]+'),
            ('#.*?\015?\012', '#.*?\015?\012'),
            ('END', '$'),
            ('ATTR', '<<.+?>>'),
            ('STMT', '{{.+?}}'),
            ('ID', '[a-zA-Z_][a-zA-Z_0-9]*'),
            ('STR', '[rR]?\'([^\\n\'\\\\]|\\\\.)*\'|[rR]?"([^\\n"\\\\]|\\\\.)*"'),
            ('LP', '\\('),
            ('RP', '\\)'),
            ('LB', '\\['),
            ('RB', '\\]'),
            ('OR', '[|]'),
            ('STAR', '[*]'),
            ('PLUS', '[+]'),
        ], ['[ \011\015\012]+', '#.*?\015?\012'], str)


class ParserDescription(Parser):
    def Parser(self):
        self._scan('"parser"')
        ID = self._scan('ID')
        self._scan('":"')
        Options = self.Options()
        Tokens = self.Tokens()
        Rules = self.Rules(Tokens)
        END = self._scan('END')
        return Generator(ID, Options, Tokens, Rules)

    def Options(self):
        opt = {}
        while self._peek(set(['"option"', '"token"', '"ignore"', 'END', '"rule"'])) == '"option"':
            self._scan('"option"')
            self._scan('":"')
            Str = self.Str()
            opt[Str] = 1
        return opt

    def Tokens(self):
        tok = []
        while self._peek(set(['"token"', '"ignore"', 'END', '"rule"'])) in ['"token"', '"ignore"']:
            _token_ = self._peek(set(['"token"', '"ignore"']))
            if _token_ == '"token"':
                self._scan('"token"')
                ID = self._scan('ID')
                self._scan('":"')
                Str = self.Str()
                tok.append((ID, Str))
            else:  # == '"ignore"'
                self._scan('"ignore"')
                self._scan('":"')
                Str = self.Str()
                tok.append(('#ignore', Str))
        return tok

    def Rules(self, tokens):
        rul = []
        while self._peek(set(['"rule"', 'END'])) == '"rule"':
            self._scan('"rule"')
            ID = self._scan('ID')
            OptParam = self.OptParam()
            self._scan('":"')
            ClauseA = self.ClauseA(tokens)
            rul.append((ID, OptParam, ClauseA))
        return rul

    def ClauseA(self, tokens):
        ClauseB = self.ClauseB(tokens)
        v = [ClauseB]
        while self._peek(set(['OR', 'RP', 'RB', '"rule"', 'END'])) == 'OR':
            OR = self._scan('OR')
            ClauseB = self.ClauseB(tokens)
            v.append(ClauseB)
        return cleanup_choice(v)

    def ClauseB(self, tokens):
        v = []
        while self._peek(set(['STR', 'ID', 'LP', 'LB', 'STMT', 'OR', 'RP', 'RB', '"rule"', 'END'])) in ['STR', 'ID', 'LP', 'LB', 'STMT']:
            ClauseC = self.ClauseC(tokens)
            v.append(ClauseC)
        return cleanup_sequence(v)

    def ClauseC(self, tokens):
        ClauseD = self.ClauseD(tokens)
        _token_ = self._peek(set(['PLUS', 'STAR', 'STR', 'ID', 'LP', 'LB', 'STMT', 'OR', 'RP', 'RB', '"rule"', 'END']))
        if _token_ == 'PLUS':
            PLUS = self._scan('PLUS')
            return Plus(ClauseD)
        elif _token_ == 'STAR':
            STAR = self._scan('STAR')
            return Star(ClauseD)
        else:
            return ClauseD

    def ClauseD(self, tokens):
        _token_ = self._peek(set(['STR', 'ID', 'LP', 'LB', 'STMT']))
        if _token_ == 'STR':
            STR = self._scan('STR')
            t = (STR, eval(STR, {}, {}))
            if t not in tokens:
                tokens.insert(0, t)
            return Terminal(STR)
        elif _token_ == 'ID':
            ID = self._scan('ID')
            OptParam = self.OptParam()
            return resolve_name(tokens, ID, OptParam)
        elif _token_ == 'LP':
            LP = self._scan('LP')
            ClauseA = self.ClauseA(tokens)
            RP = self._scan('RP')
            return ClauseA
        elif _token_ == 'LB':
            LB = self._scan('LB')
            ClauseA = self.ClauseA(tokens)
            RB = self._scan('RB')
            return Option(ClauseA)
        else:  # == 'STMT'
            STMT = self._scan('STMT')
            return Eval(STMT[2:-2])

    def OptParam(self):
        if self._peek(set(['ATTR', '":"', 'PLUS', 'STAR', 'STR', 'ID', 'LP', 'LB', 'STMT', 'OR', 'RP', 'RB', '"rule"', 'END'])) == 'ATTR':
            ATTR = self._scan('ATTR')
            return ATTR[2:-2]
        return ''

    def Str(self):
        STR = self._scan('STR')
        return eval(STR, {}, {})


# This replaces the default main routine


yapps_options = [
    ('context-insensitive-scanner', 'context-insensitive-scanner',
     'Scan all tokens (see docs)')
    ]


def generate(inputfilename, outputfilename='', dump=0, **flags):
    """Generate a grammar, given an input filename (X.g)
    and an output filename (defaulting to X.py)."""

    if not outputfilename:
        if inputfilename[-2:] == '.g':
            outputfilename = inputfilename[:-2] + '.py'
        else:
            raise Exception("Missing output filename")

    print 'Input Grammar:', inputfilename
    print 'Output File:', outputfilename

    DIVIDER = '\n%%\n'  # This pattern separates the pre/post parsers
    preparser, postparser = None, None  # Code before and after the parser desc

    # Read the entire file
    s = open(inputfilename, 'r').read()

    # See if there's a separation between the pre-parser and parser
    f = find(s, DIVIDER)
    if f >= 0:
        preparser, s = s[:f] + '\n\n', s[f + len(DIVIDER):]

    # See if there's a separation between the parser and post-parser
    f = find(s, DIVIDER)
    if f >= 0:
        s, postparser = s[:f], '\n\n' + s[f + len(DIVIDER):]

    # Create the parser and scanner
    p = ParserDescription(ParserDescriptionScanner(s))
    if not p:
        return

    # Now parse the file
    t = wrap_error_reporter(p, 'Parser')
    if not t:
        return  # Error
    if preparser is not None:
        t.preparser = preparser
    if postparser is not None:
        t.postparser = postparser

    # Check the options
    for f in t.options.keys():
        for opt, _, _ in yapps_options:
            if f == opt:
                break
        else:
            print 'Warning: unrecognized option', f
    # Add command line options to the set
    for f in flags.keys():
        t.options[f] = flags[f]

    # Generate the output
    if dump:
        t.dump_information()
    else:
        t.output = open(outputfilename, 'w')
        t.generate_output()

if __name__ == '__main__':
    import getopt
    optlist, args = getopt.getopt(sys.argv[1:], 'f:', ['dump'])
    if not args or len(args) > 2:
        print 'Usage:'
        print '  python', sys.argv[0], '[flags] input.g [output.py]'
        print 'Flags:'
        print ('  --dump' + ' ' * 40)[:35] + 'Dump out grammar information'
        for flag, _, doc in yapps_options:
            print ('  -f' + flag + ' ' * 40)[:35] + doc
    else:
        # Read in the options and create a list of flags
        flags = {}
        for opt in optlist:
            for flag, name, _ in yapps_options:
                if opt == ('-f', flag):
                    flags[name] = 1
                    break
            else:
                if opt == ('--dump', ''):
                    flags['dump'] = 1
                else:
                    print 'Warning: unrecognized option', opt[0], opt[1]

        apply(generate, tuple(args), flags)
