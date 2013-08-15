#!/usr/bin/env python

#
# Yapps 2 - yet another python parser system
# Copyright 1999-2003 by Amit J. Patel <amitp@cs.stanford.edu>
#
# This version of Yapps 2 can be distributed under the
# terms of the MIT open source license, either found in the LICENSE file
# included with the Yapps distribution
# <http://theory.stanford.edu/~amitp/yapps/> or at
# <http://www.opensource.org/licenses/mit-license.php>
#

import os
import sys

try:
    from yapps import runtime
    from yapps import parsetree
    from yapps import grammar
except ImportError:
    try:
        import runtime
        import parsetree
        import grammar
    except ImportError:
        # For running binary from a checkout-path directly
        if os.path.isfile('yapps/__init__.py'):
            sys.path.append('.')
            from yapps import runtime
            from yapps import parsetree
            from yapps import grammar
        else:
            raise


def generate(inputfilename, outputfilename=None, dump=0, **flags):
    """Generate a grammar, given an input filename (X.g)
    and an output filename (defaulting to X.py)."""

    if not outputfilename:
        if inputfilename.endswith('.g'):
            outputfilename = inputfilename[:-2] + '.py'
        else:
            raise Exception('Must specify output filename if input filename is not *.g')

    DIVIDER = '\n%%\n'  # This pattern separates the pre/post parsers
    preparser, postparser = None, None  # Code before and after the parser desc

    # Read the entire file
    s = open(inputfilename, 'r').read()

    # See if there's a separation between the pre-parser and parser
    f = s.find(DIVIDER)
    if f >= 0:
        preparser, s = s[:f] + '\n\n', s[f + len(DIVIDER):]

    # See if there's a separation between the parser and post-parser
    f = s.find(DIVIDER)
    if f >= 0:
        s, postparser = s[:f] + '\n\n', s[f + len(DIVIDER):]

    # Create the parser and scanner and parse the text
    scanner = grammar.ParserDescriptionScanner(s, filename=inputfilename)
    if preparser:
        scanner.del_line += preparser.count('\n')

    parser = grammar.ParserDescription(scanner)
    t = runtime.wrap_error_reporter(parser, 'Parser')
    if t is None:
        return 1  # Failure
    if preparser is not None:
        t.preparser = preparser
    if postparser is not None:
        t.postparser = postparser

    # Add command line options to the set
    t.options.update(flags)

    # Generate the output
    if dump:
        t.dump_information()
    else:
        t.output = open(outputfilename, 'w')
        t.generate_output()
    return 0


def main(argv=None):
    import doctest
    doctest.testmod(sys.modules['__main__'])
    doctest.testmod(parsetree)

    import argparse
    parser = argparse.ArgumentParser(
        description='Generate python parser code from grammar description file.')
    parser.add_argument('grammar_path', help='Path to grammar description file (input).')
    parser.add_argument('parser_path', nargs='?',
        help='Path to output file to be generated.'
            ' Input path, but with .py will be used, if omitted.')
    parser.add_argument('-i', '--context-insensitive-scanner',
        action='store_true', help='Scan all tokens (see docs).')
    parser.add_argument('-t', '--indent-with-tabs', action='store_true',
        help='Use tabs instead of four spaces for indentation in generated code.')
    parser.add_argument('--dump', action='store_true', help='Dump out grammar information.')
    optz = parser.parse_args(argv if argv is not None else sys.argv[1:])

    parser_flags = dict()
    for k in 'dump', 'context_insensitive_scanner':
        if getattr(optz, k, False):
            parser_flags[k] = True
    if optz.indent_with_tabs:
        parsetree.INDENT = '\t'  # not the cleanest way

    sys.exit(generate(optz.grammar_path, optz.parser_path, **parser_flags))


if __name__ == '__main__':
    main()
