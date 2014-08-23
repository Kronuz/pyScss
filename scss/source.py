from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import os
import re

import six

from scss.cssdefs import (
    _ml_comment_re, _sl_comment_re,
    _expand_rules_space_re, _collapse_properties_space_re,
    _strings_re,
)
from scss.cssdefs import determine_encoding


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
_reverse_safe_strings_re = re.compile('|'.join(map(re.escape, _reverse_safe_strings)))


class SourceFile(object):
    def __init__(self, filename, contents, encoding=None, parent_dir=None, is_string=False, is_sass=None, line_numbers=True, line_strip=True):
        filename = os.path.realpath(filename)
        if parent_dir is None:
            parent_dir = os.path.dirname(filename)
        else:
            parent_dir = os.path.realpath(parent_dir)
        filename = os.path.basename(filename)

        self.filename = filename
        self.parent_dir = parent_dir

        self.encoding = encoding
        self.sass = filename.endswith('.sass') if is_sass is None else is_sass
        self.line_numbers = line_numbers
        self.line_strip = line_strip
        self.contents = self.prepare_source(contents)
        self.is_string = is_string

    def __repr__(self):
        return "<SourceFile '%s' at 0x%x>" % (
            self.filename,
            id(self),
        )

    @property
    def full_filename(self):
        if self.is_string:
            return self.filename
        return os.path.join(self.parent_dir, self.filename)

    @classmethod
    def from_filename(cls, fn, filename=None, parent_dir=None, **kwargs):
        # Open in binary mode so we can reliably detect the encoding
        with open(fn, 'rb') as f:
            return cls.from_file(f, filename=filename, parent_dir=parent_dir, **kwargs)

    @classmethod
    def from_file(cls, f, filename=None, parent_dir=None, **kwargs):
        contents = f.read()
        encoding = determine_encoding(contents)
        if isinstance(contents, six.binary_type):
            contents = contents.decode(encoding)

        if filename is None:
            filename = getattr(f, 'name', None)

        return cls(filename, contents, encoding=encoding, parent_dir=parent_dir, **kwargs)

    @classmethod
    def from_string(cls, string, filename=None, parent_dir=None, is_sass=None, line_numbers=True):
        if isinstance(string, six.text_type):
            # Already decoded; we don't know what encoding to use for output,
            # though, so still check for a @charset.
            encoding = determine_encoding(string)
        elif isinstance(string, six.binary_type):
            encoding = determine_encoding(string)
            string = string.decode(encoding)
        else:
            raise TypeError("Expected a string, got {0!r}".format(string))

        if filename is None:
            filename = "<string %r...>" % string[:50]
            is_string = True
        else:
            # Must have come from a file at some point
            is_string = False

        return cls(filename, string, parent_dir=parent_dir, is_string=is_string, is_sass=is_sass, line_numbers=line_numbers)

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
        if self.line_strip:
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

        # make sure we support multi-space indent as long as indent is consistent
        if indent and not state['indent_marker']:
            state['indent_marker'] = indent

        if state['indent_marker']:
            indent //= state['indent_marker']

        if indent == state['prev_indent']:
            # same indentation as previous line
            if state['prev_line']:
                state['prev_line'] += ';'
        elif indent > state['prev_indent']:
            # new indentation is greater than previous, we just entered a new block
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
        if self.line_strip:
            output = output.strip()

        state['prev_indent'] = indent
        state['prev_line'] = line
        state['prev_line_no'] = line_no

        if output:
            output += '\n'
            ret += output
        return ret

    def prepare_source(self, codestr, sass=False):
        # Decorate lines with their line numbers and a delimiting NUL and remove empty lines
        state = {
            'line_buffer': '',
            'prev_line': '',
            'prev_line_no': 0,
            'prev_indent': 0,
            'nested_blocks': 0,
            'indent_marker': 0,
        }
        if self.sass:
            parse_line = self.parse_sass_line
        else:
            parse_line = self.parse_scss_line
        _codestr = codestr
        codestr = ''
        for line_no, line in enumerate(_codestr.splitlines()):
            codestr += parse_line(line_no, line, state)
        codestr += parse_line(None, None, state)  # parse the last line stored in prev_line buffer

        # protects codestr: "..." strings
        codestr = _strings_re.sub(lambda m: _reverse_safe_strings_re.sub(lambda n: _reverse_safe_strings[n.group(0)], m.group(0)), codestr)

        # removes multiple line comments
        codestr = _ml_comment_re.sub('', codestr)

        # removes inline comments, but not :// (protocol)
        codestr = _sl_comment_re.sub('', codestr)

        codestr = _safe_strings_re.sub(lambda m: _safe_strings[m.group(0)], codestr)

        # expand the space in rules
        codestr = _expand_rules_space_re.sub(' {', codestr)

        # collapse the space in properties blocks
        codestr = _collapse_properties_space_re.sub(r'\1{', codestr)

        return codestr
