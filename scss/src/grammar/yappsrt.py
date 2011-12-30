# Yapps 3.0 Runtime (by Kronuz)
#
# This module is needed to run generated parsers.

import re

try:
    from _scss import Scanner, NoMoreTokens
except ImportError:
    Scanner = None

################################################################################
# Parser

if not Scanner:
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
            if i < tokens_len:
                if restrict and self.restrictions[i] and restrict > self.restrictions[i]:
                    raise NotImplementedError("Unimplemented: restriction set changed")
                return self.tokens[i]
            raise NoMoreTokens

        def rewind(self, i):
            tokens_len = len(self.tokens)
            if i <= tokens_len:
                token = self.tokens[i]
                self.tokens = self.tokens[:i]
                self.restrictions = self.restrictions[:i]
                self.pos = token[0]


class CachedScanner(Scanner):
    """
    Same as Scanner, but keeps cached tokens for any given input
    """
    _cache_ = {}
    _goals_ = ['END']

    @classmethod
    def cleanup(cls):
        cls._cache_ = {}

    def __init__(self, patterns, ignore, input=None):
        try:
            self._tokens = self._cache_[input]
        except KeyError:
            self._tokens = None
            self.__tokens = {}
            self.__input = input
            super(CachedScanner, self).__init__(patterns, ignore, input)

    def reset(self, input):
        try:
            self._tokens = self._cache_[input]
        except KeyError:
            self._tokens = None
            self.__tokens = {}
            self.__input = input
            super(CachedScanner, self).reset(input)

    def __repr__(self):
        if self._tokens is None:
            return super(CachedScanner, self).__repr__()
        output = ''
        for t in self._tokens[-10:]:
            output = "%s\n  (@%s)  %s  =  %s" % (output, t[0], t[2], repr(t[3]))
        return output

    def token(self, i, restrict=None):
        if self._tokens is None:
            token = super(CachedScanner, self).token(i, restrict)
            self.__tokens[i] = token
            if token[2] in self._goals_:  # goal tokens
                self._cache_[self.__input] = self._tokens = self.__tokens
            return token
        else:
            token = self._tokens.get(i)
            if token is None:
                raise NoMoreTokens
            return token

    def rewind(self, i):
        if self._tokens is None:
            super(CachedScanner, self).rewind(i)


class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._pos = 0

    def reset(self, input):
        self._scanner.reset(input)
        self._pos = 0

    def _peek(self, types):
        """
        Returns the token type for lookahead; if there are any args
        then the list of args is the set of token types to allow
        """
        tok = self._scanner.token(self._pos, types)
        return tok[2]

    def _scan(self, type):
        """
        Returns the matched text, and moves to the next token
        """
        tok = self._scanner.token(self._pos, set([type]))
        if tok[2] != type:
            raise SyntaxError("SyntaxError[@ char %s: %s]" % (repr(tok[0]), "Trying to find " + type))
        self._pos += 1
        return tok[3]

    def _rewind(self, n=1):
        self._pos -= min(n, self._pos)
        self._scanner.rewind(self._pos)


################################################################################


def print_error(input, err, scanner):
    """This is a really dumb long function to print error messages nicely."""
    p = err.pos
    # Figure out the line number
    line = input[:p].count('\n')
    print err.msg + " on line " + repr(line + 1) + ":"
    # Now try printing part of the line
    text = input[max(p - 80, 0):
        p + 80]
    p = p - max(p - 80, 0)

    # Strip to the left
    i = text[:p].rfind('\n')
    j = text[:p].rfind('\r')
    if i < 0 or (0 <= j < i):
        i = j
    if 0 <= i < p:
        p = p - i - 1
        text = text[i + 1:]

    # Strip to the right
    i = text.find('\n', p)
    j = text.find('\r', p)
    if i < 0 or (0 <= j < i):
        i = j
    if i >= 0:
        text = text[:i]

    # Now shorten the text
    while len(text) > 70 and p > 60:
        # Cut off 10 chars
        text = "..." + text[10:]
        p = p - 7

    # Now print the string, along with an indicator
    print '> ', text
    print '> ', ' ' * p + '^'
    print 'List of nearby tokens:', scanner


def wrap_error_reporter(parser, rule, *args):
    try:
        return getattr(parser, rule)(*args)
    except SyntaxError, s:
        input = parser._scanner.input
        try:
            print_error(input, s, parser._scanner)
            raise
        except ImportError:
            print "Syntax Error %s on line %d" % (s.msg, input[:s.pos].count('\n') + 1)
    except NoMoreTokens:
        print "Could not complete parsing; stopped around here:"
        print parser._scanner
