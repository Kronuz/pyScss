#!/usr/bin/env python

## locate_blocks() needs heavy optimizations... is way too slow right now!
## Any suggestion from python wizards? :-)

import re
import sys
from datetime import datetime

import pstats
import cProfile
from cStringIO import StringIO
def profile(fn):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        stream = StringIO()
        profiler.enable()
        try:
            res = fn(*args, **kwargs)
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats('time')
            print >>stream, ""
            print >>stream, "=" * 100
            print >>stream, "Stats:"
            stats.print_stats()

            print >>stream, "=" * 100
            print >>stream, "Callers:"
            stats.print_callers()

            print >>stream, "=" * 100
            print >>stream, "Callees:"
            stats.print_callees()
            print >>sys.stderr, stream.getvalue()
            stream.close()
        return res
    return wrapper


DEBUG = False
################################################################################
# Helpers

_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
PATTERNS = [
        ('":"', ':'),
        ('[ \r\t\n]+', '[ \r\t\n]+'),
        ('COMMA', ','),
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
        ('STR', "'[^']*'"),
        ('QSTR', '"[^"]*"'),
        ('UNITS', '(?<!\\s)(?:' + '|'.join(_units) + ')(?![-\\w])'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('BOOL', '(?<![-\\w])(?:true|false)(?![-\\w])'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('ID', '[-a-zA-Z_][-a-zA-Z0-9_]*'),
]


################################################################################

class NoMoreTokens(Exception):
    """
    Another exception object, for when we run out of tokens
    """
    pass


class Scanner(object):
    def __init__(self, patterns, ignore, input=None):
        """
        Patterns is [(terminal,regex)...]
        Ignore is [terminal,...];
        Input is a string
        """
        self.reset(input)
        self.ignore = ignore
        # The stored patterns are a pair (compiled regex,source
        # regex).  If the patterns variable passed in to the
        # constructor is None, we assume that the class already has a
        # proper .patterns list constructed
        if patterns is not None:
            self.patterns = []
            for k, r in patterns:
                self.patterns.append((k, re.compile(r)))

    def reset(self, input):
        self.tokens = []
        self.restrictions = []
        self.input = input
        self.pos = 0

    def __repr__(self):
        """
        Print the last 10 tokens that have been scanned in
        """
        output = ''
        for t in self.tokens[-10:]:
            output = "%s\n  (@%s)  %s  =  %s" % (output, t[0], t[2], repr(t[3]))
        return output

    def _scan(self, restrict):
        """
        Should scan another token and add it to the list, self.tokens,
        and add the restriction to self.restrictions
        """
        # Keep looking for a token, ignoring any in self.ignore
        token = None
        while True:
            best_pat = None
            # Search the patterns for a match, with earlier
            # tokens in the list having preference
            best_pat_len = 0
            for p, regexp in self.patterns:
                # First check to see if we're restricting to this token
                if restrict and p not in restrict and p not in self.ignore:
                    continue
                m = regexp.match(self.input, self.pos)
                if m:
                    # We got a match
                    best_pat = p
                    best_pat_len = len(m.group(0))
                    break

            # If we didn't find anything, raise an error
            if best_pat is None:
                msg = "Bad Token"
                if restrict:
                    msg = "Trying to find one of " + ", ".join(restrict)
                raise SyntaxError("SyntaxError[@ char %s: %s]" % (repr(self.pos), msg))

            # If we found something that isn't to be ignored, return it
            if best_pat in self.ignore:
                # This token should be ignored...
                self.pos += best_pat_len
            else:
                end_pos = self.pos + best_pat_len
                # Create a token with this data
                token = (
                    self.pos,
                    end_pos,
                    best_pat,
                    self.input[self.pos:end_pos]
                )
                break
        if token is not None:
            self.pos = token[1]
            # Only add this token if it's not in the list
            # (to prevent looping)
            if not self.tokens or token != self.tokens[-1]:
                self.tokens.append(token)
                self.restrictions.append(restrict)
                return 1
        return 0

    def token(self, i, restrict=None):
        """
        Get the i'th token, and if i is one past the end, then scan
        for another token; restrict is a list of tokens that
        are allowed, or 0 for any token.
        """
        tokens_len = len(self.tokens)
        if i == tokens_len:  # We are at the end, get the next...
            tokens_len += self._scan(restrict)
        elif i >= 0 and i < tokens_len:
            if restrict and self.restrictions[i] and restrict > self.restrictions[i]:
                raise NotImplementedError("Unimplemented: restriction set changed")
        if i >= 0 and i < tokens_len:
            return self.tokens[i]
        raise NoMoreTokens()

    def rewind(self, i):
        tokens_len = len(self.tokens)
        if i <= tokens_len:
            token = self.tokens[i]
            self.tokens = self.tokens[:i]
            self.restrictions = self.restrictions[:i]
            self.pos = token[0]



class _Scanner_a(Scanner):
    patterns = None
    _patterns = PATTERNS

    def __init__(self, input=None):
        if hasattr(self, 'setup_patterns'):
            self.setup_patterns(self._patterns)
        elif self.patterns is None:
            self.__class__.patterns = []
            for t, p in self._patterns:
                self.patterns.append((t, re.compile(p)))
        super(_Scanner_a, self).__init__(None, ['[ \r\t\n]+'], input)


################################################################################

try:
    from _speedups import Scanner

    class _Scanner_b(Scanner):
        patterns = None
        _patterns = PATTERNS

        def __init__(self, input=None):
            if hasattr(self, 'setup_patterns'):
                self.setup_patterns(self._patterns)
            elif self.patterns is None:
                self.__class__.patterns = []
                for t, p in self._patterns:
                    self.patterns.append((t, re.compile(p)))
            super(_Scanner_b, self).__init__(None, ['[ \r\t\n]+'], input)

except ImportError:
    _Scanner_b = None


def process_scan(Scanner, level=0, dump=False):
    ret = '' if dump else None
    s = Scanner('[(5px - 3) * (5px - 3)]')
    i = 0
    while True:
        try:
            s.token(i)
            i += 1
            if dump:
                ret += '%s\n%s\n' % ('-' * 70, repr(s))
        except:
            break
    return ret


verify = "----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  '['\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n----------------------------------------------------------------------\n\n  (@1)  LPAR  =  '('\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n----------------------------------------------------------------------\n\n  (@2)  NUM  =  '5'\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n  (@18)  SUB  =  '- '\n----------------------------------------------------------------------\n\n  (@3)  UNITS  =  'px'\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n  (@18)  SUB  =  '- '\n  (@20)  NUM  =  '3'\n----------------------------------------------------------------------\n\n  (@6)  SUB  =  '- '\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n  (@18)  SUB  =  '- '\n  (@20)  NUM  =  '3'\n  (@21)  RPAR  =  ')'\n----------------------------------------------------------------------\n\n  (@8)  NUM  =  '3'\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n  (@18)  SUB  =  '- '\n  (@20)  NUM  =  '3'\n  (@21)  RPAR  =  ')'\n  (@22)  RPAR  =  ']'\n----------------------------------------------------------------------\n\n  (@9)  RPAR  =  ')'\n  (@11)  MUL  =  '*'\n  (@13)  LPAR  =  '('\n  (@14)  NUM  =  '5'\n  (@15)  UNITS  =  'px'\n  (@18)  SUB  =  '- '\n  (@20)  NUM  =  '3'\n  (@21)  RPAR  =  ')'\n  (@22)  RPAR  =  ']'\n  (@23)  END  =  ''\n"


def process_scans(Scanner):
    for q in xrange(20000):
        process_scan(Scanner)
profiled_process_scans = profile(process_scans)

if __name__ == "__main__":
    for scanner, desc in (
        (_Scanner_a, "Pure Python, Full algorithm (_Scanner_a)"),
        (_Scanner_b, "Builtin C Function, Full algorithm (_Scanner_b)"),
    ):
        if scanner:
            ret = process_scan(scanner, dump=True)
            # print "This is what %s returned:" % desc
            # print ret
            # print repr(ret)
            assert ret == verify, '\nFrom %s, got:\n%s\nShould be:\n%s' % (desc, ret, verify)

            start = datetime.now()
            print >>sys.stderr, "Timing: %s..." % desc,
            process_scans(scanner)
            elap = datetime.now() - start

            elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
            print >>sys.stderr, "Done! took %06.3fms" % elapms
