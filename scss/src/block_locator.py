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
# Helper functions


SEPARATOR = '\x00'
_nl_re = re.compile(r'\s*\n\s*', re.MULTILINE)
_nl_num_re = re.compile(r'\n.+' + SEPARATOR, re.MULTILINE)
_nl_num_nl_re = re.compile(r'\n.+' + SEPARATOR + r'\s*(?=\n)', re.MULTILINE)
_blocks_re = re.compile(r'[{},;()\'"\n]')


def load_string(codestr):
    """
    Add line numbers to the string using SEPARATOR as the separation between
    the line number and the line.
    """
    idx = {'line': 1}

    # Add line numbers:
    def _cnt(m):
        idx['line'] += 1
        return '\n' + str(idx['line']) + SEPARATOR
    codestr = str(idx['line']) + SEPARATOR + _nl_re.sub(_cnt, codestr + '\n')

    # remove empty lines
    codestr = _nl_num_nl_re.sub('', codestr)
    return codestr


def _strip_selprop(selprop, lineno):
    # Get the line number of the selector or property and strip all other
    # line numbers that might still be there (from multiline selectors)
    _lineno, _sep, selprop = selprop.partition(SEPARATOR)
    if _sep == SEPARATOR:
        _lineno = _lineno.strip(' \t\n;')
        try:
            lineno = int(_lineno)
        except ValueError:
            pass
    else:
        selprop = _lineno
    selprop = _nl_num_re.sub('\n', selprop)
    selprop = selprop.strip()
    return selprop, lineno


def _strip(selprop):
    # Strip all line numbers, ignoring them in the way
    selprop, _ = _strip_selprop(selprop, None)
    return selprop


################################################################################
# Algorithm implemented in C (much slower here):

PAR = 0
INSTR = 1
DEPTH = 2
SKIP = 3
THIN = 4
INIT = 5
SAFE = 6
LOSE = 7
START = 8
END = 9
LINENO = 10
SELPROP = 11


def _start_string(codestr, ctx, i, c):
    if DEBUG: print "_start_string"
    # A string starts
    ctx[INSTR] = c
    return
    yield


def _end_string(codestr, ctx, i, c):
    if DEBUG: print "_end_string"
    # A string ends (FIXME: needs to accept escaped characters)
    ctx[INSTR] = None
    return
    yield


def _start_parenthesis(codestr, ctx, i, c):
    if DEBUG: print "_start_parenthesis"
    # parenthesis begins:
    ctx[PAR] += 1
    ctx[THIN] = None
    ctx[SAFE] = i + 1
    return
    yield


def _end_parenthesis(codestr, ctx, i, c):
    if DEBUG: print "_end_parenthesis"
    ctx[PAR] -= 1
    return
    yield


def _flush_properties(codestr, ctx, i, c):
    if DEBUG: print "_flush_properties"
    # Flush properties
    if ctx[LOSE] <= ctx[INIT]:
        _property, ctx[LINENO] = _strip_selprop(codestr[ctx[LOSE]:ctx[INIT]], ctx[LINENO])
        if _property:
            yield ctx[LINENO], _property, None
            ctx[SELPROP] = _property
        ctx[LOSE] = ctx[INIT]
    return
    yield


def _start_block1(codestr, ctx, i, c):
    if DEBUG: print "_start_block1"
    # Start level-1 block
    if i > 0 and codestr[i - 1] == '#':  # Do not process #{...} as blocks!
        ctx[SKIP] = True
    else:
        ctx[START] = i
        if ctx[THIN] is not None and _strip(codestr[ctx[THIN]:i]):
            ctx[INIT] = ctx[THIN]
        for y in _flush_properties(codestr, ctx, i, c):
            yield y
        ctx[THIN] = None
    ctx[DEPTH] += 1
    return
    yield


def _start_block(codestr, ctx, i, c):
    if DEBUG: print "_start_block"
    # Start blocks:
    ctx[DEPTH] += 1
    return
    yield


def _end_block1(codestr, ctx, i, c):
    if DEBUG: print "_end_block1"
    # End level-1 block:
    ctx[DEPTH] -= 1
    if not ctx[SKIP]:
        ctx[END] = i
        _selectors, ctx[LINENO] = _strip_selprop(codestr[ctx[INIT]:ctx[START]], ctx[LINENO])
        _codestr = codestr[ctx[START] + 1:ctx[END]]
        if _selectors:
            yield ctx[LINENO], _selectors, _codestr
            ctx[SELPROP] = _selectors
        ctx[INIT] = ctx[SAFE] = ctx[LOSE] = ctx[END] + 1
        ctx[THIN] = None
    ctx[SKIP] = False
    return
    yield


def _end_block(codestr, ctx, i, c):
    if DEBUG: print "_end_block"
    # Block ends:
    ctx[DEPTH] -= 1
    return
    yield


def _end_property(codestr, ctx, i, c):
    if DEBUG: print "_end_property"
    # End of property (or block):
    ctx[INIT] = i
    if ctx[LOSE] <= ctx[INIT]:
        _property, ctx[LINENO] = _strip_selprop(codestr[ctx[LOSE]:ctx[INIT]], ctx[LINENO])
        if _property:
            yield ctx[LINENO], _property, None
            ctx[SELPROP] = _property
        ctx[INIT] = ctx[SAFE] = ctx[LOSE] = i + 1
    ctx[THIN] = None
    return
    yield


def _mark_safe(codestr, ctx, i, c):
    if DEBUG: print "_mark_safe"
    # We are on a safe zone
    if ctx[THIN] is not None and _strip(codestr[ctx[THIN]:i]):
        ctx[INIT] = ctx[THIN]
    ctx[THIN] = None
    ctx[SAFE] = i + 1
    return
    yield


def _mark_thin(codestr, ctx, i, c):
    if DEBUG: print "_mark_thin"
    # Step on thin ice, if it breaks, it breaks here
    if ctx[THIN] is not None and _strip(codestr[ctx[THIN]:i]):
        ctx[INIT] = ctx[THIN]
        ctx[THIN] = i + 1
    elif ctx[THIN] is None and _strip(codestr[ctx[SAFE]:i]):
        ctx[THIN] = i + 1
    return
    yield


scss_function_map = {
    # (c, instr, par, depth)
    ('"', None, False, 0): _start_string,
    ("'", None, False, 0): _start_string,
    ('"', None, True, 0): _start_string,
    ("'", None, True, 0): _start_string,
    ('"', None, False, 1): _start_string,
    ("'", None, False, 1): _start_string,
    ('"', None, True, 1): _start_string,
    ("'", None, True, 1): _start_string,
    ('"', None, False, 2): _start_string,
    ("'", None, False, 2): _start_string,
    ('"', None, True, 2): _start_string,
    ("'", None, True, 2): _start_string,

    ('"', '"', False, 0): _end_string,
    ("'", "'", False, 0): _end_string,
    ('"', '"', True, 0): _end_string,
    ("'", "'", True, 0): _end_string,
    ('"', '"', False, 1): _end_string,
    ("'", "'", False, 1): _end_string,
    ('"', '"', True, 1): _end_string,
    ("'", "'", True, 1): _end_string,
    ('"', '"', False, 2): _end_string,
    ("'", "'", False, 2): _end_string,
    ('"', '"', True, 2): _end_string,
    ("'", "'", True, 2): _end_string,

    ("(", None, False, 0): _start_parenthesis,
    ("(", None, True, 0): _start_parenthesis,
    ("(", None, False, 1): _start_parenthesis,
    ("(", None, True, 1): _start_parenthesis,
    ("(", None, False, 2): _start_parenthesis,
    ("(", None, True, 2): _start_parenthesis,

    (")", None, True, 0): _end_parenthesis,
    (")", None, True, 1): _end_parenthesis,
    (")", None, True, 2): _end_parenthesis,

    ("{", None, False, 0): _start_block1,
    ("{", None, False, 1): _start_block,
    ("{", None, False, 2): _start_block,

    ("}", None, False, 1): _end_block1,
    ("}", None, False, 2): _end_block,

    (";", None, False, 0): _end_property,

    (",", None, False, 0): _mark_safe,

    ("\n", None, False, 0): _mark_thin,

    (None, None, False, 0): _flush_properties,
    (None, None, False, 1): _flush_properties,
    (None, None, False, 2): _flush_properties,
}


def _locate_blocks_a(codestr):
    """
    For processing CSS like strings.

    Either returns all selectors (that can be "smart" multi-lined, as
    long as it's joined by `,`, or enclosed in `(` and `)`) with its code block
    (the one between `{` and `}`, which can be nested), or the "lose" code
    (properties) that doesn't have any blocks.

    threshold is the number of blank lines before selectors are broken into
    pieces (properties).
    """
    ctx = [0, None, 0, False, None, 0, 0, 0, None, None, 0, '??']

    for m in _blocks_re.finditer(codestr):
        c = m.group()

        fn = scss_function_map.get((c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH]))
        if DEBUG: print fn and ' > ' or '   ', fn and fn.__name__, (c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH])
        if fn:
            for y in fn(codestr, ctx, m.start(), c):
                yield y

    codestr_end = len(codestr)
    exc = None
    if ctx[PAR]:
        exc = exc or "Missing closing parenthesis somewhere in block: '%s'" % ctx[SELPROP]
    elif ctx[INSTR]:
        exc = exc or "Missing closing string somewhere in block: '%s'" % ctx[SELPROP]
    elif ctx[DEPTH]:
        exc = exc or "Block never closed: '%s'" % ctx[SELPROP]
        while ctx[DEPTH] > 0 and ctx[INIT] < codestr_end:
            c = '}'
            fn = scss_function_map.get((c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH]))
            if DEBUG: print fn and ' > ' or ' ! ', fn and fn.__name__, (c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH])
            if fn:
                for y in fn(codestr, ctx, m.start(), c):
                    yield y

    if ctx[INIT] < codestr_end:
        ctx[INIT] = codestr_end
        c = None
        fn = scss_function_map.get((c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH]))
        if DEBUG: print fn and ' > ' or ' ! ', fn and fn.__name__, (c, ctx[INSTR], ctx[PAR] != 0, 2 if ctx[DEPTH] > 1 else ctx[DEPTH])
        if fn:
            for y in fn(codestr, ctx, m.start(), c):
                yield y

    if exc:
        raise Exception(exc)


################################################################################
# Algorithm using Regexps in pure Python (fastest pure python):


def _locate_blocks_b(codestr):
    """
    For processing CSS like strings.

    Either returns all selectors (that can be "smart" multi-lined, as
    long as it's joined by `,`, or enclosed in `(` and `)`) with its code block
    (the one between `{` and `}`, which can be nested), or the "lose" code
    (properties) that doesn't have any blocks.

    threshold is the number of blank lines before selectors are broken into
    pieces (properties).
    """
    lineno = 0

    par = 0
    instr = None
    depth = 0
    skip = False
    thin = None
    i = init = safe = lose = 0
    start = end = None

    for m in _blocks_re.finditer(codestr):
        i = m.start(0)
        c = codestr[i]
        if instr is not None:
            if c == instr:
                instr = None  # A string ends (FIXME: needs to accept escaped characters)
        elif c in ('"', "'"):
            instr = c  # A string starts
        elif c == '(':  # parenthesis begins:
            par += 1
            thin = None
            safe = i + 1
        elif c == ')':  # parenthesis ends:
            par -= 1
        elif not par and not instr:
            if c == '{':  # block begins:
                if depth == 0:
                    if i > 0 and codestr[i - 1] == '#':  # Do not process #{...} as blocks!
                        skip = True
                    else:
                        start = i
                        if thin is not None and _strip(codestr[thin:i]):
                            init = thin
                        if lose <= init:
                            _property, lineno = _strip_selprop(codestr[lose:init], lineno)
                            if _property:
                                yield lineno, _property, None
                            lose = init
                        thin = None
                depth += 1
            elif c == '}':  # block ends:
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        if not skip:
                            end = i
                            _selectors, lineno = _strip_selprop(codestr[init:start], lineno)
                            _codestr = codestr[start + 1:end].strip()
                            if _selectors:
                                yield lineno, _selectors, _codestr
                            init = safe = lose = end + 1
                            thin = None
                        skip = False
            elif depth == 0:
                if c == ';':  # End of property (or block):
                    init = i
                    if lose <= init:
                        _property, lineno = _strip_selprop(codestr[lose:init], lineno)
                        if _property:
                            yield lineno, _property, None
                        init = safe = lose = i + 1
                    thin = None
                elif c == ',':
                    if thin is not None and _strip(codestr[thin:i]):
                        init = thin
                    thin = None
                    safe = i + 1
                elif c == '\n':
                    if thin is not None and _strip(codestr[thin:i]):
                        init = thin
                        thin = i + 1
                    elif thin is None and _strip(codestr[safe:i]):
                        thin = i + 1  # Step on thin ice, if it breaks, it breaks here
    if depth > 0:
        if not skip:
            _selectors, lineno = _strip_selprop(codestr[init:start], lineno)
            _codestr = codestr[start + 1:].strip()
            if _selectors:
                yield lineno, _selectors, _codestr
            if par:
                raise Exception("Missing closing parenthesis somewhere in block: '%s'" % _selectors)
            elif instr:
                raise Exception("Missing closing string somewhere in block: '%s'" % _selectors)
            else:
                raise Exception("Block never closed: '%s'" % _selectors)
    losestr = codestr[lose:]
    for _property in losestr.split(';'):
        _property, lineno = _strip_selprop(_property, lineno)
        if _property:
            yield lineno, _property, None


################################################################################
# Algorithm implemented in C:


try:
    from _speedups import locate_blocks as _locate_blocks_c
except ImportError:
    _locate_blocks_c = None
    print >>sys.stderr, "Scanning acceleration disabled (_speedups not found)!"



################################################################################


codestr = """
simple {
    block;
}
#{ignored};
some,
selectors,
and multi-lined,
selectors
with more
{
    the block in here;
    can have, nested, selectors {
        and properties in nested blocks;
        and stuff with #{ ignored blocks };
    }
    properties-can: "have strings with stuff like this: }";
}
and other,
selectors
can be turned into "lose"
properties
if no commas are found
however this is a selector (
    as well as these things,
    which are parameters
    and can expand
    any number of
    lines) {
    and this is its block;;
}
"""
verify = '\t----------------------------------------------------------------------\n\t>[1] \'simple\'\n\t----------------------------------------------------------------------\n\t>\t[3] \'block\'\n\t----------------------------------------------------------------------\n\t>[5] \'#{ignored}\'\n\t----------------------------------------------------------------------\n\t>[6] \'some,\\nselectors,\\nand multi-lined,\\nselectors\'\n\t----------------------------------------------------------------------\n\t>[10] \'with more\'\n\t----------------------------------------------------------------------\n\t>\t[12] \'the block in here\'\n\t----------------------------------------------------------------------\n\t>\t[13] \'can have, nested, selectors\'\n\t----------------------------------------------------------------------\n\t>\t\t[14] \'and properties in nested blocks\'\n\t----------------------------------------------------------------------\n\t>\t\t[15] \'and stuff with #{ ignored blocks }\'\n\t----------------------------------------------------------------------\n\t>\t[17] \'properties-can: "have strings with stuff like this: }"\'\n\t----------------------------------------------------------------------\n\t>[19] \'and other,\\nselectors\\ncan be turned into "lose"\\nproperties\'\n\t----------------------------------------------------------------------\n\t>[23] \'if no commas are found\\nhowever this is a selector (\\nas well as these things,\\nwhich are parameters\\nand can expand\\nany number of\\nlines)\'\n\t----------------------------------------------------------------------\n\t>\t[30] \'and this is its block\'\n'


def process_block(locate_blocks, codestr, level=0, dump=False):
    ret = '' if dump else None
    for lineno, selprop, block in locate_blocks(codestr):
        if dump:
            ret += '\t%s\n\t>%s[%s] %s\n' % ('-' * 70, '\t' * level, lineno, repr(selprop))
        if block:
            _ret = process_block(locate_blocks, block, level + 1, dump)
            if dump:
                ret += _ret
    return ret


def process_blocks(locate_blocks, codestr):
    for q in xrange(20000):
        process_block(locate_blocks, codestr)
profiled_process_blocks = profile(process_blocks)

if __name__ == "__main__":
    codestr = load_string(codestr)

    for locate_blocks, desc in (
        (_locate_blocks_a, "Pure Python, Full algorithm (_locate_blocks_a)"),
        (_locate_blocks_b, "Pure Python, Condensed algorithm (_locate_blocks_b)"),
        (_locate_blocks_c, "Builtin C Function, Full algorithm (_locate_blocks_c)"),
    ):
        if locate_blocks:
            ret = process_block(locate_blocks, codestr, dump=True)
            # print "This is what %s returned:" % desc
            # print ret
            # print repr(ret)
            assert ret == verify, '\nFrom %s, got:\n%s\nShould be:\n%s' % (desc, ret, verify)

            start = datetime.now()
            print >>sys.stderr, "Timing: %s..." % desc,
            process_blocks(locate_blocks, codestr)
            elap = datetime.now() - start

            elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
            print >>sys.stderr, "Done! took %06.3fms" % elapms
