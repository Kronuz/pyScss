from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import hashlib
import logging
import os
import re

import six

from scss.cssdefs import (
    _ml_comment_re, _sl_comment_re,
    _expand_rules_space_re, _collapse_properties_space_re,
    _strings_re,
)
from scss.cssdefs import determine_encoding


log = logging.getLogger(__name__)


_safe_strings = {
    '^doubleslash^': '//',
    '^bigcopen^': '/*',
    '^bigcclose^': '*/',
    '^doubledot^': ':',
    '^semicolon^': ';',
    '^curlybracketopen^': '{',
    '^curlybracketclosed^': '}',
}
_reverse_safe_strings = dict((v, k) for k, v in _safe_strings.items())
_safe_strings_re = re.compile('|'.join(map(re.escape, _safe_strings)))
_reverse_safe_strings_re = re.compile('|'.join(
    map(re.escape, _reverse_safe_strings)))


class SourceFile(object):
    """A single input file to be fed to the compiler.  Detects the encoding
    (according to CSS spec rules) and performs some light pre-processing.
    """

    path = None
    """For "real" files, an absolute path to the original source file.  For ad
    hoc strings, some other kind of identifier.  This is used as a hash key and
    a test of equality, so it MUST be unique!
    """

    def __init__(
            self, path, contents, encoding=None,
            is_real_file=True, is_sass=None):
        """Not normally used.  See the three alternative constructors:
        :func:`SourceFile.from_file`, :func:`SourceFile.from_filename`, and
        :func:`SourceFile.from_string`.
        """
        if not isinstance(contents, six.text_type):
            raise TypeError(
                "Expected bytes for 'contents', got {0}"
                .format(type(contents)))

        if is_real_file and not os.path.isabs(path):
            raise ValueError(
                "Expected an absolute path for 'path', got {0!r}"
                .format(path))

        self.path = path
        self.encoding = encoding
        if is_sass is None:
            # TODO autodetect from the contents if the extension is bogus or
            # missing?
            self.is_sass = os.path.splitext(path)[1] == '.sass'
        else:
            self.is_sass = is_sass
        self.contents = self.prepare_source(contents)
        self.is_real_file = is_real_file

    def __repr__(self):
        return "<{0} {1!r}>".format(type(self).__name__, self.path)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, SourceFile):
            return NotImplemented

        return self.path == other.path

    def __ne__(self, other):
        return not self == other

    @classmethod
    def from_filename(cls, fn, path=None, **kwargs):
        """Read Sass source from a file on disk."""
        # Open in binary mode so we can reliably detect the encoding
        with open(fn, 'rb') as f:
            return cls.from_file(f, path=path or fn, **kwargs)

    @classmethod
    def from_file(cls, f, path=None, **kwargs):
        """Read Sass source from a file or file-like object."""
        contents = f.read()
        encoding = determine_encoding(contents)
        if isinstance(contents, six.binary_type):
            contents = contents.decode(encoding)

        is_real_file = False
        if path is None:
            path = getattr(f, 'name', repr(f))
        elif os.path.exists(path):
            path = os.path.normpath(os.path.abspath(path))
            is_real_file = True

        return cls(
            path, contents, encoding=encoding, is_real_file=is_real_file,
            **kwargs)

    @classmethod
    def from_string(cls, string, path=None, encoding=None, is_sass=None):
        """Read Sass source from the contents of a string."""
        if isinstance(string, six.text_type):
            # Already decoded; we don't know what encoding to use for output,
            # though, so still check for a @charset.
            # TODO what if the given encoding conflicts with the one in the
            # file?  do we care?
            if encoding is None:
                encoding = determine_encoding(string)

            byte_contents = string.encode(encoding)
            text_contents = string
        elif isinstance(string, six.binary_type):
            encoding = determine_encoding(string)
            byte_contents = string
            text_contents = string.decode(encoding)
        else:
            raise TypeError("Expected text or bytes, got {0!r}".format(string))

        is_real_file = False
        if path is None:
            m = hashlib.sha256()
            m.update(byte_contents)
            path = 'string:' + m.hexdigest().decode('ascii')
        elif os.path.exists(path):
            path = os.path.normpath(os.path.abspath(path))
            is_real_file = True

        return cls(
            path, text_contents, encoding=encoding, is_real_file=is_real_file,
            is_sass=is_sass,
        )

    def parse_scss_line(self, line_no, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line.rstrip()  # remove EOL character

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ''
        else:
            state['line_buffer'] = ''

        output = state['prev_line']
        output = output.strip()

        state['prev_line'] = line
        state['prev_line_no'] = line_no

        if output:
            output += '\n'
            ret += output

        return ret

    def parse_sass_line(self, line_no, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line.rstrip()  # remove EOL character

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ret
        else:
            state['line_buffer'] = ''

        indent = len(line) - len(line.lstrip())

        # make sure we support multi-space indent as long as indent is
        # consistent
        if indent and not state['indent_marker']:
            state['indent_marker'] = indent

        if state['indent_marker']:
            indent //= state['indent_marker']

        if indent == state['prev_indent']:
            # same indentation as previous line
            if state['prev_line']:
                state['prev_line'] += ';'
        elif indent > state['prev_indent']:
            # new indentation is greater than previous, we just entered a new
            # block
            state['prev_line'] += ' {'
            state['nested_blocks'] += 1
        else:
            # indentation is reset, we exited a block
            block_diff = state['prev_indent'] - indent
            if state['prev_line']:
                state['prev_line'] += ';'
            state['prev_line'] += ' }' * block_diff
            state['nested_blocks'] -= block_diff

        output = state['prev_line']
        output = output.strip()

        state['prev_indent'] = indent
        state['prev_line'] = line
        state['prev_line_no'] = line_no

        if output:
            output += '\n'
            ret += output
        return ret

    def prepare_source(self, codestr, sass=False):
        # Decorate lines with their line numbers and a delimiting NUL and
        # remove empty lines
        state = {
            'line_buffer': '',
            'prev_line': '',
            'prev_line_no': 0,
            'prev_indent': 0,
            'nested_blocks': 0,
            'indent_marker': 0,
        }
        if self.is_sass:
            parse_line = self.parse_sass_line
        else:
            parse_line = self.parse_scss_line
        _codestr = codestr
        codestr = ''
        for line_no, line in enumerate(_codestr.splitlines()):
            codestr += parse_line(line_no, line, state)
        # parse the last line stored in prev_line buffer
        codestr += parse_line(None, None, state)

        # protects codestr: "..." strings
        codestr = _strings_re.sub(
            lambda m: _reverse_safe_strings_re.sub(
                lambda n: _reverse_safe_strings[n.group(0)], m.group(0)),
            codestr)

        # removes multiple line comments
        codestr = _ml_comment_re.sub('', codestr)

        # removes inline comments, but not :// (protocol)
        codestr = _sl_comment_re.sub('', codestr)

        codestr = _safe_strings_re.sub(
            lambda m: _safe_strings[m.group(0)], codestr)

        # expand the space in rules
        codestr = _expand_rules_space_re.sub(' {', codestr)

        # collapse the space in properties blocks
        codestr = _collapse_properties_space_re.sub(r'\1{', codestr)

        return codestr
