import re

# Super dumb little selector parser.

# Yes, yes, this is a regex tokenizer.  The actual meaning of the
# selector doesn't matter; the parts are just important for matching up
# during @extend.

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
# TODO `*html` is incorrectly parsed as a single selector
# TODO this oughta be touched up for css4 selectors
SELECTOR_TOKENIZER = re.compile(
r'''
    # Colons introduce pseudo-selectors, sometimes with parens
    # TODO doesn't handle quoted )
    [:]+ [-\w]+ (?: [(] .+? [)] )?

    # These guys are combinators -- note that a single space counts too
    | \s* [ +>~] \s*

    # Square brackets are attribute tests
    # TODO: this doesn't handle ] within a string
    | [[] .+? []]

    # Dot and pound start class/id selectors.  Percent starts a Sass
    # extend-target faux selector.
    | [.#%] [-\w]+

    # Percentages are used for @keyframes
    | \d+ [%]

    # Plain identifiers, or single asterisks, are element names
    | [-\w]+
    | [*]

    # & is the sass replacement token
    | [&]

    # And as a last-ditch effort, just eat up to whitespace
    | (\S+)
''', re.VERBOSE | re.MULTILINE)


# Maps the first character of a token to a rough ordering.  The default
# (element names) is zero.
TOKEN_TYPE_ORDER = {
    '#': 2,
    '.': 3,
    ':': 4,
    '[': 5,
    '%': 6,
}
TOKEN_SORT_KEY = lambda token: TOKEN_TYPE_ORDER.get(token[0], 0)


class SimpleSelector(object):
    def __init__(self, combinator, tokens):
        self.combinator = combinator
        # TODO enforce that only one element name (including *) appears in a
        # selector
        # TODO remove duplicates
        self.tokens = tuple(sorted(tokens, key=TOKEN_SORT_KEY))

    def __repr__(self):
        return "<%s: %r>" % (type(self).__name__, self.render())

    def __hash__(self):
        return hash((self.combinator, self.tokens))

    def __eq__(self, other):
        if not isinstance(other, SimpleSelector):
            return NotImplemented

        return self.combinator == other.combinator and self.tokens == other.tokens

    @property
    def has_parent_reference(self):
        return '&' in self.tokens or 'self' in self.tokens

    @property
    def has_placeholder(self):
        return any(
            token[0] == '%'
            for token in self.tokens)

    def is_superset_of(self, other):
        return (
            self.combinator == other.combinator and
            set(self.tokens) <= set(other.tokens))

    def replace_parent(self, parent_simples):
        assert parent_simples

        ancestors = parent_simples[:-1]
        parent = parent_simples[-1]

        did_replace = False
        new_tokens = []
        for token in self.tokens:
            if not did_replace and token in ('&', 'self'):
                did_replace = True
                new_tokens.extend(parent.tokens)
            else:
                new_tokens.append(token)

        if did_replace:
            # This simple selector was merged into the direct parent
            merged_simple = type(self)(self.combinator, new_tokens)
            return ancestors + (merged_simple,)
        else:
            # This simple selector is completely separate
            return parent_simples + (self,)

    # TODO just use set ops for these, once the constructor removes dupes
    def merge_with(self, other):
        new_tokens = self.tokens + tuple(token for token in other.tokens if token not in set(self.tokens))
        return type(self)(self.combinator, new_tokens)

    def difference(self, other):
        new_tokens = tuple(token for token in self.tokens if token not in set(other.tokens))
        return type(self)(self.combinator, new_tokens)

    def render(self):
        # TODO fail if there are no tokens, or if one is a placeholder?
        rendered = ''.join(self.tokens)
        if self.combinator != ' ':
            rendered = ' '.join((self.combinator, rendered))

        return rendered


class Selector(object):
    """A single CSS selector."""

    def __init__(self, selector, tree):
        """Private; please use parse()."""
        self.original_selector = selector
        # TODO rename this
        # TODO enforce uniqueness
        self._tree = tuple(tree)

    @classmethod
    def parse_many(cls, selector):
        selector = selector.strip()
        ret = []
        pending_tree = []
        pending_combinator = ' '
        pending_tokens = []

        pos = 0
        while pos < len(selector):
            # TODO i don't think this deals with " + " correctly.  anywhere.
            m = SELECTOR_TOKENIZER.match(selector, pos)
            if not m:
                # TODO prettify me
                raise SyntaxError("Couldn't parse selector: %r" % (selector,))

            token = m.group(0)
            pos += len(token)

            # Kill any extraneous space, BUT make sure not to turn a lone space
            # into an empty string
            token = token.strip() or ' '

            if token == ',':
                # End current selector
                # TODO what about "+ ,"?  what do i even do with that
                if pending_tokens:
                    pending_tree.append(
                        SimpleSelector(pending_combinator, pending_tokens))
                if pending_tree:
                    ret.append(cls(selector, pending_tree))
                pending_tree = []
                pending_combinator = ' '
                pending_tokens = []
            elif token in ' +>~':
                # End current simple selector
                if pending_tokens:
                    pending_tree.append(
                        SimpleSelector(pending_combinator, pending_tokens))
                pending_combinator = token
                pending_tokens = []
            else:
                # Add to pending simple selector
                pending_tokens.append(token)


        # Deal with any remaining pending bits
        # TODO reduce copy-paste yikes
        if pending_tokens:
            pending_tree.append(
                SimpleSelector(pending_combinator, pending_tokens))
        if pending_tree:
            ret.append(cls(selector, pending_tree))

        return ret

    @classmethod
    def parse(cls, selector_string):
        # TODO remove me
        return cls.parse_many(selector_string)

    @classmethod
    def parse_one(cls, selector_string):
        selectors = cls.parse_many(selector_string)
        if len(selectors) != 1:
            # TODO better error
            raise ValueError

        return selectors[0]

    def __repr__(self):
        return "<%s: %r>" % (type(self).__name__, self.render())

    def __hash__(self):
        return hash(self._tree)

    def __eq__(self, other):
        if not isinstance(other, Selector):
            return NotImplemented

        return self._tree == other._tree

    @property
    def has_parent_reference(self):
        return any(
            simple.has_parent_reference
            for simple in self._tree)

    @property
    def has_placeholder(self):
        return any(
            simple.has_placeholder
            for simple in self._tree)

    def with_parent(self, parent):
        saw_parent_ref = False

        new_tree = []
        for simple in self._tree:
            if simple.has_parent_reference:
                new_tree.extend(simple.replace_parent(parent._tree))
                saw_parent_ref = True
            else:
                new_tree.append(simple)

        if not saw_parent_ref:
            new_tree = parent._tree + tuple(new_tree)

        return type(self)("", new_tree)

    def lookup_key(self):
        """Build a key from the "important" parts of a selector: elements,
        classes, ids.
        """
        # TODO how does this work with multiple selectors
        parts = set()
        for node in self._tree:
            for token in node.tokens:
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

                if node.is_superset_of(other_node):
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

        # TODO what if the prefix doesn't match?  who wins?  should we even get
        # this far?
        focal_nodes = (p_extras.merge_with(r_extras),)

        befores = self._merge_trails(p_before, r_trail)

        return [Selector(None, before + focal_nodes + p_after) for before in befores]

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
            if hinge_start.is_superset_of(node):
                start_idx = i
                break
        else:
            raise ValueError("Couldn't find hinge %r in compound selector %r", (hinge_start, self._tree))

        for i, hinge_node in enumerate(hinge):
            self_node = self._tree[start_idx + i]
            if hinge_node.is_superset_of(self_node):
                continue

            # TODO this isn't true; consider finding `a b` in `a c a b`
            raise TypeError("no match")

        end_idx = start_idx + len(hinge) - 1
        focal_node = self._tree[end_idx]
        extras = focal_node.difference(hinge[-1])
        return self._tree[:start_idx], extras, self._tree[end_idx + 1:]

    @staticmethod
    def _merge_trails(left, right):
        # XXX docs docs docs

        if not left or not right:
            # At least one is empty, so there are no conflicts; just
            # return whichever isn't empty
            return [left or right]

        lcs = longest_common_subsequence(left, right, _merge_selector_nodes)

        ret = [()]
        left_last = 0
        right_last = 0
        for left_next, right_next, merged in lcs:
            left_prefix = left[left_last:left_next]
            right_prefix = right[right_last:right_next]

            new_ret = [
                node + left_prefix + right_prefix + (merged,)
                for node in ret]
            if left_prefix and right_prefix:
                new_ret.extend(
                    node + right_prefix + left_prefix + (merged,)
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
        return ' '.join(simple.render() for simple in self._tree).lstrip()


def _merge_selector_nodes(a, b):
    # TODO document, turn me into a method on something
    # TODO what about combinators
    if a.is_superset_of(b):
        return a.merge_with(b)
    elif b.is_superset_of(a):
        return b.merge_with(a)
    else:
        return None


def longest_common_subsequence(a, b, mergefunc=None):
    """Find the longest common subsequence between two iterables.

    The longest common subsequence is the core of any diff algorithm: it's the
    longest sequence of elements that appears in both parent sequences in the
    same order, but NOT necessarily consecutively.

    Original algorithm borrowed from Wikipedia:
    http://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Code_for_the_dynamic_programming_solution

    This function is used only to implement @extend, largely because that's
    what the Ruby implementation does.  Thus it's been extended slightly from
    the simple diff-friendly algorithm given above.

    What @extend wants to know is whether two simple selectors are compatible,
    not just equal.  To that end, you must pass in a "merge" function to
    compare a pair of elements manually.  It should return `None` if they are
    incompatible, and a MERGED element if they are compatible -- in the case of
    selectors, this is whichever one is more specific.

    Because of this fuzzier notion of equality, the return value is a list of
    ``(a_index, b_index, value)`` tuples rather than items alone.
    """
    if mergefunc is None:
        # Stupid default, just in case
        def mergefunc(a, b):
            if a == b:
                return a
            return None

    # Precalculate equality, since it can be a tad expensive and every pair is
    # compared at least once
    eq = {}
    for ai, aval in enumerate(a):
        for bi, bval in enumerate(b):
            eq[ai, bi] = mergefunc(aval, bval)

    # Build the "length" matrix, which provides the length of the LCS for
    # arbitrary-length prefixes.  -1 exists only to support the base case
    prefix_lcs_length = {}
    for ai in range(-1, len(a)):
        for bi in range(-1, len(b)):
            if ai == -1 or bi == -1:
                l = 0
            elif eq[ai, bi]:
                l = prefix_lcs_length[ai - 1, bi - 1] + 1
            else:
                l = max(
                    prefix_lcs_length[ai, bi - 1],
                    prefix_lcs_length[ai - 1, bi])

            prefix_lcs_length[ai, bi] = l

    # The interesting part.  The key insight is that the bottom-right value in
    # the length matrix must be the length of the LCS because of how the matrix
    # is defined, so all that's left to do is backtrack from the ends of both
    # sequences in whatever way keeps the LCS as long as possible, and keep
    # track of the equal pairs of elements we see along the way.
    # Wikipedia does this with recursion, but the algorithm is trivial to
    # rewrite as a loop, as below.
    ai = len(a) - 1
    bi = len(b) - 1

    ret = []
    while ai >= 0 and bi >= 0:
        merged = eq[ai, bi]
        if merged is not None:
            ret.append((ai, bi, merged))
            ai -= 1
            bi -= 1
        elif prefix_lcs_length[ai, bi - 1] > prefix_lcs_length[ai - 1, bi]:
            bi -= 1
        else:
            ai -= 1

    # ret has the latest items first, which is backwards
    ret.reverse()
    return ret
