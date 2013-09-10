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
