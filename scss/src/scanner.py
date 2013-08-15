#!/usr/bin/env python

## locate_blocks() needs heavy optimizations... is way too slow right now!
## Any suggestion from python wizards? :-)

import re
import sys
from datetime import datetime

from six.moves import xrange

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


################################################################################
# Helpers

BASE_UNITS = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
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
        ('UNITS', '(?<!\\s)(?:' + '|'.join(BASE_UNITS) + ')(?![-\\w])'),
        ('NUM', '(?:\\d+(?:\\.\\d*)?|\\.\\d+)'),
        ('COLOR', '#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?![a-fA-F0-9])'),
        ('VAR', '\\$[-a-zA-Z0-9_]+'),
        ('NAME', '\\$?[-a-zA-Z0-9_]+'),
        ('FNCT', '[-a-zA-Z_][-a-zA-Z0-9_]*(?=\\()'),
        ('ID', '!?[-a-zA-Z_][-a-zA-Z0-9_]*'),
]


################################################################################
# Parser
DEBUG = False

from yapps.runtime import Scanner

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
    s = Scanner('[(5px - 3) * (5px - 3)], function($arg1: a b c, $arg2: 4px + 5px, $arg3: red #fff #000000 #ffff0088), "Some string"')
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


# Expected resulting string:
EXPECTED = '----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n----------------------------------------------------------------------\n\n  (@0)  LPAR  =  \'[\'\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n----------------------------------------------------------------------\n\n  (@1)  LPAR  =  \'(\'\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n----------------------------------------------------------------------\n\n  (@2)  NUM  =  \'5\'\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n----------------------------------------------------------------------\n\n  (@3)  UNITS  =  \'px\'\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n----------------------------------------------------------------------\n\n  (@6)  SUB  =  \'- \'\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n----------------------------------------------------------------------\n\n  (@8)  NUM  =  \'3\'\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n----------------------------------------------------------------------\n\n  (@9)  RPAR  =  \')\'\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n----------------------------------------------------------------------\n\n  (@11)  MUL  =  \'*\'\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n----------------------------------------------------------------------\n\n  (@13)  LPAR  =  \'(\'\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n----------------------------------------------------------------------\n\n  (@14)  NUM  =  \'5\'\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n----------------------------------------------------------------------\n\n  (@15)  UNITS  =  \'px\'\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n----------------------------------------------------------------------\n\n  (@18)  SUB  =  \'- \'\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n----------------------------------------------------------------------\n\n  (@20)  NUM  =  \'3\'\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n----------------------------------------------------------------------\n\n  (@21)  RPAR  =  \')\'\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n----------------------------------------------------------------------\n\n  (@22)  RPAR  =  \']\'\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n----------------------------------------------------------------------\n\n  (@23)  COMMA  =  \',\'\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n----------------------------------------------------------------------\n\n  (@25)  NAME  =  \'function\'\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n----------------------------------------------------------------------\n\n  (@33)  LPAR  =  \'(\'\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n----------------------------------------------------------------------\n\n  (@34)  VAR  =  \'$arg1\'\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n----------------------------------------------------------------------\n\n  (@39)  ":"  =  \':\'\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n----------------------------------------------------------------------\n\n  (@41)  NAME  =  \'a\'\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n----------------------------------------------------------------------\n\n  (@43)  NAME  =  \'b\'\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n----------------------------------------------------------------------\n\n  (@45)  NAME  =  \'c\'\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n----------------------------------------------------------------------\n\n  (@46)  COMMA  =  \',\'\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n  (@66)  VAR  =  \'$arg3\'\n----------------------------------------------------------------------\n\n  (@48)  VAR  =  \'$arg2\'\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n  (@66)  VAR  =  \'$arg3\'\n  (@71)  ":"  =  \':\'\n----------------------------------------------------------------------\n\n  (@53)  ":"  =  \':\'\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n  (@66)  VAR  =  \'$arg3\'\n  (@71)  ":"  =  \':\'\n  (@73)  NAME  =  \'red\'\n----------------------------------------------------------------------\n\n  (@55)  NUM  =  \'4\'\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n  (@66)  VAR  =  \'$arg3\'\n  (@71)  ":"  =  \':\'\n  (@73)  NAME  =  \'red\'\n  (@77)  COLOR  =  \'#fff\'\n----------------------------------------------------------------------\n\n  (@56)  UNITS  =  \'px\'\n  (@59)  ADD  =  \'+\'\n  (@61)  NUM  =  \'5\'\n  (@62)  UNITS  =  \'px\'\n  (@64)  COMMA  =  \',\'\n  (@66)  VAR  =  \'$arg3\'\n  (@71)  ":"  =  \':\'\n  (@73)  NAME  =  \'red\'\n  (@77)  COLOR  =  \'#fff\'\n  (@82)  COLOR  =  \'#000000\'\n'


def process_scans(Scanner):
    for q in xrange(10000):
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
            assert ret == EXPECTED, '\nFrom %s, got:\n%s\nShould be:\n%s' % (desc, ret, EXPECTED)

            start = datetime.now()
            print >>sys.stderr, "Timing: %s..." % desc,
            process_scans(scanner)
            elap = datetime.now() - start

            elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
            print >>sys.stderr, "Done! took %06.3fms" % elapms
