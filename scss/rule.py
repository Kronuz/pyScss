from __future__ import absolute_import
from __future__ import print_function

import six
import logging

from scss.cssdefs import _has_placeholder_re
from scss.types import Value


log = logging.getLogger(__name__)


def normalize_var(name):
    if isinstance(name, six.string_types):
        return name.replace('_', '-')
    else:
        log.warn("Variable name doesn't look like a string: %r", name)
        return name


class VariableScope(object):
    """Implements Sass variable scoping.

    Similar to `ChainMap`, except that assigning a new value will replace an
    existing value, not mask it.
    """
    def __init__(self, maps=()):
        self.maps = [dict()] + list(maps)

    def __repr__(self):
        return "<VariableScope(%s)>" % (', '.join(repr(map) for map in self.maps),)

    def __getitem__(self, key):
        for map in self.maps:
            if key in map:
                return map[key]

        raise KeyError(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def set(self, key, value, force_local=False):
        if force_local:
            self.maps[0][key] = value
            return

        for map in self.maps:
            if key in map:
                map[key] = value
                return

        self.maps[0][key] = value

    def new_child(self):
        return VariableScope(self.maps)


class Namespace(object):
    """..."""

    def __init__(self, variables=None, functions=None, mixins=None):
        if variables is None:
            self._variables = VariableScope()
        else:
            # TODO parse into sass values once that's a thing, or require them
            # all to be
            self._variables = VariableScope([variables])

        if functions is None:
            self._functions = VariableScope()
        else:
            self._functions = VariableScope([functions._functions])

        self._mixins = VariableScope()

    @classmethod
    def derive_from(cls, *others):
        self = cls()
        if len(others) == 1:
            self._variables = others[0]._variables.new_child()
            self._functions = others[0]._functions.new_child()
            self._mixins = others[0]._mixins.new_child()
        else:
            # Note that this will create a 2-dimensional scope where each of
            # these scopes is checked first in order.  TODO is this right?
            self._variables = VariableScope(other._variables for other in others)
            self._functions = VariableScope(other._functions for other in others)
            self._mixins = VariableScope(other._mixins for other in others)
        return self

    def derive(self):
        """Return a new child namespace.  All existing variables are still
        readable and writeable, but any new variables will only exist within a
        new scope.
        """
        return type(self).derive_from(self)

    def variable(self, name, throw=False):
        name = normalize_var(name)
        return self._variables[name]

    def set_variable(self, name, value, local_only=False):
        name = normalize_var(name)
        if not isinstance(value, Value):
            raise TypeError("Expected a Sass type, while setting %s got %r" % (name, value,))
        self._variables.set(name, value, force_local=local_only)

    def _get_callable(self, chainmap, name, arity):
        name = normalize_var(name)
        if arity is not None:
            # With explicit arity, try the particular arity before falling back
            # to the general case (None)
            try:
                return chainmap[name, arity]
            except KeyError:
                pass

        return chainmap[name, None]

    def _set_callable(self, chainmap, name, arity, cb):
        name = normalize_var(name)
        chainmap[name, arity] = cb

    def mixin(self, name, arity):
        return self._get_callable(self._mixins, name, arity)

    def set_mixin(self, name, arity, cb):
        self._set_callable(self._mixins, name, arity, cb)

    def function(self, name, arity):
        return self._get_callable(self._functions, name, arity)

    def set_function(self, name, arity, cb):
        self._set_callable(self._functions, name, arity, cb)


class SassRule(object):
    """At its heart, a CSS rule: combination of a selector and zero or more
    properties.  But this is Sass, so it also tracks some Sass-flavored
    metadata, like `@extend` rules and `@media` nesting.
    """

    def __init__(self, source_file, unparsed_contents=None, dependent_rules=None,
            options=None, properties=None,
            namespace=None,
            lineno=0, extends_selectors=frozenset(),
            ancestry=None):

        self.source_file = source_file
        self.lineno = lineno

        self.unparsed_contents = unparsed_contents
        self.options = options
        self.extends_selectors = extends_selectors

        if namespace is None:
            assert False
            self.namespace = Namespace()
        else:
            self.namespace = namespace

        if dependent_rules is None:
            self.dependent_rules = set()
        else:
            self.dependent_rules = dependent_rules

        if properties is None:
            self.properties = []
        else:
            self.properties = properties

        self.retval = None

        if ancestry is None:
            self.ancestry = []
        else:
            self.ancestry = ancestry

    def __repr__(self):
        return "<SassRule %s, %d props>" % (
            self.ancestry,
            len(self.properties),
        )

    @property
    def selectors(self):
        # TEMPORARY
        if self.ancestry and self.ancestry[-1].is_selector:
            return frozenset(self.ancestry[-1].selectors)
        else:
            return frozenset()

    @selectors.setter
    def selectors(self, value):
        for header in reversed(self.ancestry):
            if header.is_selector:
                header.selectors |= value
                return
            else:
                # TODO media
                break

        self.ancestry.append(BlockSelectorHeader(value))

    @property
    def file_and_line(self):
        """Returns the filename and line number where this rule originally
        appears, in the form "foo.scss:3".  Used for error messages.
        """
        return "%s:%d" % (self.source_file.filename, self.lineno)

    @property
    def is_empty(self):
        """Returns whether this rule is considered "empty" -- i.e., has no
        contents that should end up in the final CSS.
        """
        if self.properties:
            # Rules containing CSS properties are never empty
            return False

        if self.ancestry:
            header = self.ancestry[-1]
            if header.is_atrule and header.directive != '@media':
                # At-rules should always be preserved, UNLESS they are @media
                # blocks, which are known to be noise if they don't have any
                # contents of their own
                return False

        return True

    def copy(self):
        return type(self)(
            source_file=self.source_file,
            lineno=self.lineno,
            unparsed_contents=self.unparsed_contents,

            options=self.options,
            #properties=list(self.properties),
            properties=self.properties,
            extends_selectors=self.extends_selectors,
            #ancestry=list(self.ancestry),
            ancestry=self.ancestry,

            namespace=self.namespace.derive(),
        )


class Selector(object):
    """A single CSS selector."""

    def __init__(self, selector, tree):
        """Private; please use parse()."""
        self.original_selector = selector
        self._tree = tree

    @classmethod
    def parse(cls, selector):
        # Super dumb little selector parser

        # Yes, yes, this is a regex tokenizer.  The actual meaning of the
        # selector doesn't matter; the parts are just important for matching up
        # during @extend.
        import re
        tokenizer = re.compile(
        r'''
            # Colons introduce pseudo-selectors, sometimes with parens
            # TODO doesn't handle quoted )
            [:]+ [-\w]+ (?: [(] .+? [)] )?

            # Square brackets are attribute tests
            # TODO: this doesn't handle ] within a string
            | [[] .+? []]

            # Dot and pound start class/id selectors.  Percent starts a Sass
            # extend-target faux selector.
            | [.#%] [-\w]+

            # Plain identifiers, or single asterisks, are element names
            | [-\w]+
            | [*]

            # These guys are combinators -- note that a single space counts too
            | \s* [ +>~] \s*

            # And as a last-ditch effort for something really outlandish (e.g.
            # percentages as faux-selectors in @keyframes), just eat up to the
            # next whitespace
            | (\S+)
        ''', re.VERBOSE | re.MULTILINE)

        # Selectors have three levels: simple, combinator, comma-delimited.
        # Each combinator can only appear once as a delimiter between simple
        # selectors, so it can be thought of as a prefix.
        # So this:
        #     a.b + c, d#e
        # parses into two Selectors with these structures:
        #     [[' ', 'a', '.b'], ['+', 'c']]
        #     [[' ', 'd', '#e']]
        # Note that the first simple selector has an implied descendant
        # combinator -- i.e., it is a descendant of the root element.
        trees = [[[' ']]]
        pos = 0
        while pos < len(selector):
            # TODO i don't think this deals with " + " correctly.  anywhere.
            m = tokenizer.match(selector, pos)
            if not m:
                # TODO prettify me
                raise SyntaxError("Couldn't parse selector: %r" % (selector,))

            token = m.group(0)
            if token == ',':
                trees.append([[' ']])
            elif token in ' +>~':
                trees[-1].append([token])
            else:
                trees[-1][-1].append(token)

            pos += len(token)

        # TODO this passes the whole selector, not just the part
        return [cls(selector, tree) for tree in trees]

    def __repr__(self):
        return "<%s: %r>" % (type(self).__name__, self._tree)

    def lookup_key(self):
        """Build a key from the "important" parts of a selector: elements,
        classes, ids.
        """
        # TODO how does this work with multiple selectors
        parts = set()
        for node in self._tree:
            for token in node[1:]:
                if token[0] not in ':[':
                    parts.add(token)

        if not parts:
            # Should always have at least ONE key; selectors with no elements,
            # no classes, and no ids can be indexed as None to avoid a scan of
            # every selector in the entire document
            parts.add(None)

        return frozenset(parts)

    def is_superset_of(self, other):
        assert isinstance(other, Selector)

        idx = 0
        for other_node in other._tree:
            if idx >= len(self._tree):
                return False

            while idx < len(self._tree):
                node = self._tree[idx]
                idx += 1

                if node[0] == other_node[0] and set(node[1:]) <= set(other_node[1:]):
                    break

        return True

    def substitute(self, target, replacement):
        """Return a list of selectors obtained by replacing the `target`
        selector with `replacement`.

        Herein lie the guts of the Sass @extend directive.

        In general, for a selector ``a X b Y c``, a target ``X Y``, and a
        replacement ``q Z``, return the selectors ``a q X b Z c`` and ``q a X b
        Z c``.  Note in particular that no more than two selectors will be
        returned, and the permutation of ancestors will never insert new simple
        selectors "inside" the target selector.
        """

        # Find the hinge in the parent selector, and split it into before/after
        p_before, p_extras, p_after = self.break_around(target._tree)

        # The replacement has no hinge; it only has the most specific simple
        # selector (which is the part that replaces "self" in the parent) and
        # whatever preceding simple selectors there may be
        r_trail = replacement._tree[:-1]
        r_extras = replacement._tree[-1]

        # TODO is this the right order?
        # TODO what if the prefix doesn't match?  who wins?  should we even get
        # this far?
        focal_node = [p_extras[0]]
        focal_node.extend(sorted(
            p_extras[1:] + r_extras[1:],
            key=lambda token: {'#':1,'.':2,':':3}.get(token[0], 0)))

        befores = self._merge_trails(p_before, r_trail)

        return [Selector(None, before + focal_node + p_after) for before in befores]

    def break_around(self, hinge):
        """Given a simple selector node contained within this one (a "hinge"),
        break it in half and return a parent selector, extra specifiers for the
        hinge, and a child selector.

        That is, given a hinge X, break the selector A + X.y B into A, + .y,
        and B.
        """
        hinge_start = hinge[0]
        for i, node in enumerate(self._tree):
            # TODO does first combinator have to match?  maybe only if the
            # hinge has a non-descendant combinator?
            if set(hinge_start[1:]) <= set(node[1:]):
                start_idx = i
                break
        else:
            raise ValueError("Couldn't find hinge %r in compound selector %r", (hinge_start, self._tree))

        for i, hinge_node in enumerate(hinge):
            self_node = self._tree[start_idx + i]
            if hinge_node[0] == self_node[0] and set(hinge_node[1:]) <= set(self_node[1:]):
                continue

            # TODO this isn't true; consider finding `a b` in `a c a b`
            raise TypeError("no match")

        end_idx = start_idx + len(hinge) - 1
        focal_node = self._tree[end_idx]
        extras = [focal_node[0]] + [token for token in focal_node[1:] if token not in hinge[-1]]
        return self._tree[:start_idx], extras, self._tree[end_idx + 1:]

    @staticmethod
    def _merge_trails(left, right):
        # XXX docs docs docs

        if not left or not right:
            # At least one is empty, so there are no conflicts; just
            # return whichever isn't empty
            return [left or right]

        sequencer = LeastCommonSubsequencer(left, right, eq=_merge_selector_nodes)
        lcs = sequencer.find()

        ret = [[]]
        left_last = 0
        right_last = 0
        for left_next, right_next, merged in lcs:
            left_prefix = left[left_last:left_next]
            right_prefix = right[right_last:right_next]

            new_ret = [
                node + left_prefix + right_prefix + [merged]
                for node in ret]
            if left_prefix and right_prefix:
                new_ret.extend(
                    node + right_prefix + left_prefix + [merged]
                    for node in ret)
            ret = new_ret

            left_last = left_next + 1
            right_last = right_next + 1

        left_prefix = left[left_last:]
        right_prefix = right[right_last:]
        # TODO factor this out
        new_ret = [
            node + left_prefix + right_prefix
            for node in ret]
        if left_prefix and right_prefix:
            new_ret.extend(
                node + right_prefix + left_prefix
                for node in ret)
        ret = new_ret

        return ret

    def render(self):
        return ''.join(''.join(node) for node in self._tree).lstrip()


def _merge_selector_nodes(a, b):
    # TODO document, turn me into a method on something
    # TODO what about combinators
    aset = frozenset(a[1:])
    bset = frozenset(b[1:])
    if aset <= bset:
        return a + [token for token in b[1:] if token not in aset]
    elif bset <= aset:
        return b + [token for token in a[1:] if token not in bset]
    else:
        return None



class LeastCommonSubsequencer(object):
    # http://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Code_for_the_dynamic_programming_solution
    def __init__(self, a, b, eq=lambda a, b: a if a == b else None):
        self.a = a
        self.b = b
        self.eq_matrix = dict()
        self.length_matrix = dict()

        self.init_eq_matrix(eq)
        self.init_length_matrix()

    def init_eq_matrix(self, eq):
        for ai, aval in enumerate(self.a):
            for bi, bval in enumerate(self.b):
                self.eq_matrix[ai, bi] = eq(aval, bval)

    def init_length_matrix(self):
        for ai in range(-1, len(self.a)):
            for bi in range(-1, len(self.b)):
                if ai == -1 or bi == -1:
                    l = 0
                elif self.eq_matrix[ai, bi]:
                    l = self.length_matrix[ai - 1, bi - 1] + 1
                else:
                    l = max(
                        self.length_matrix[ai, bi - 1],
                        self.length_matrix[ai - 1, bi])

                self.length_matrix[ai, bi] = l

    def backtrack(self, ai, bi):
        if ai < 0 or bi < 0:
            # Base case: backtracked beyond the beginning with no match
            return []

        merged = self.eq_matrix[ai, bi]
        if merged is not None:
            return self.backtrack(ai - 1, bi - 1) + [(ai, bi, merged)]

        if self.length_matrix[ai, bi - 1] > self.length_matrix[ai - 1, bi]:
            return self.backtrack(ai, bi - 1)
        else:
            return self.backtrack(ai - 1, bi)

    def find(self):
        return self.backtrack(len(self.a) - 1, len(self.b) - 1)


class BlockHeader(object):
    """..."""
    # TODO doc me depending on how UnparsedBlock is handled...

    is_atrule = False
    is_scope = False
    is_selector = False

    @classmethod
    def parse(cls, prop, has_contents=False):
        # Simple pre-processing
        if prop.startswith('+') and not has_contents:
            # Expand '+' at the beginning of a rule as @include.  But not if
            # there's a block, because that's probably a CSS selector.
            # DEVIATION: this is some semi hybrid of Sass and xCSS syntax
            prop = '@include ' + prop[1:]
            try:
                if '(' not in prop or prop.index(':') < prop.index('('):
                    prop = prop.replace(':', '(', 1)
                    if '(' in prop:
                        prop += ')'
            except ValueError:
                pass
        elif prop.startswith('='):
            # Expand '=' at the beginning of a rule as @mixin
            prop = '@mixin ' + prop[1:]
        elif prop.startswith('@prototype '):
            # Remove '@prototype '
            # TODO what is @prototype??
            prop = prop[11:]

        # Minor parsing
        if prop.startswith('@'):
            if prop.lower().startswith('@else if '):
                directive = '@else if'
                argument = prop[9:]
            else:
                directive, _, argument = prop.partition(' ')
                directive = directive.lower()

            return BlockAtRuleHeader(directive, argument)
        else:
            if prop.endswith(':') or ': ' in prop:
                # Syntax is "<scope>: [prop]" -- if the optional prop exists,
                # it becomes the first rule with no suffix
                scope, unscoped_value = prop.split(':', 1)
                scope = scope.rstrip()
                unscoped_value = unscoped_value.lstrip()
                return BlockScopeHeader(scope, unscoped_value)
            else:
                return BlockSelectorHeader(prop)


class BlockAtRuleHeader(BlockHeader):
    is_atrule = True

    def __init__(self, directive, argument):
        self.directive = directive
        self.argument = argument

    def __repr__(self):
        return "<%s %r %r>" % (self.__class__.__name__, self.directive, self.argument)

    def render(self):
        if self.argument:
            return "%s %s" % (self.directive, self.argument)
        else:
            return self.directive


class BlockSelectorHeader(BlockHeader):
    is_selector = True

    def __init__(self, selectors):
        self.selectors = selectors

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.selectors)

    def render(self, sep=', ', super_selector=''):
        return sep.join(sorted(
            super_selector + s
            for s in self.selectors
            if not _has_placeholder_re.search(s)))


class BlockScopeHeader(BlockHeader):
    is_scope = True

    def __init__(self, scope, unscoped_value):
        self.scope = scope

        if unscoped_value:
            self.unscoped_value = unscoped_value
        else:
            self.unscoped_value = None


class UnparsedBlock(object):
    """A Sass block whose contents have not yet been parsed.

    At the top level, CSS (and Sass) documents consist of a sequence of blocks.
    A block may be a ruleset:

        selector { block; block; block... }

    Or it may be an @-rule:

        @rule arguments { block; block; block... }

    Or it may be only a single property declaration:

        property: value

    pyScss's first parsing pass breaks the document into these blocks, and each
    block becomes an instance of this class.
    """

    def __init__(self, parent_rule, lineno, prop, unparsed_contents):
        self.parent_rule = parent_rule
        self.header = BlockHeader.parse(prop, has_contents=bool(unparsed_contents))

        # Basic properties
        self.lineno = lineno
        self.prop = prop
        self.unparsed_contents = unparsed_contents

    @property
    def directive(self):
        return self.header.directive

    @property
    def argument(self):
        return self.header.argument

    ### What kind of thing is this?

    @property
    def is_atrule(self):
        return self.header.is_atrule

    @property
    def is_scope(self):
        return self.header.is_scope
