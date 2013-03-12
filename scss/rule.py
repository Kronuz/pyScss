class SassRule(object):
    """At its heart, a CSS rule: combination of a selector and zero or more
    properties.  But this is Sass, so it also tracks some Sass-flavored
    metadata, like `@extend` rules and `@media` nesting.
    """

    def __init__(self, source_file, position=None, unparsed_contents=None, dependent_rules=None,
            context=None, options=None, selectors=frozenset(), properties=None,
            path='./', lineno=0, media=None, extends_selectors=frozenset(),
            ancestors=None):

        self.source_file = source_file

        self.position = position
        self.unparsed_contents = unparsed_contents
        self.context = context
        self.options = options
        self.selectors = selectors
        self.path = path
        self.lineno = lineno
        self.media = media
        self.extends_selectors = extends_selectors

        if dependent_rules is None:
            self.dependent_rules = set()
        else:
            self.dependent_rules = dependent_rules

        if properties is None:
            self.properties = []
        else:
            self.properties = properties

    @property
    def file_and_line(self):
        """Returns the filename and line number where this rule originally
        appears, in the form "foo.scss:3".  Used for error messages.
        """
        return "%s:%d" % (self.source_file.filename, self.lineno)

    def copy(self):
        return type(self)(
            source_file=self.source_file,
            position=self.position,
            unparsed_contents=self.unparsed_contents,
            #deps=set(self.deps),
            dependent_rules=self.dependent_rules,
            context=self.context,
            options=self.options,
            selectors=self.selectors,
            #properties=list(self.properties),
            properties=self.properties,
            path=self.path,
            lineno=self.lineno,
            media=self.media,
            extends_selectors=self.extends_selectors,
        )


class RuleHeader(object):
    """..."""
    # TODO doc me depending on how UnparsedBlock is handled...

    is_atrule = False
    is_scope = False
    is_selector = False

    def __init__(self, prop):

        # Simple pre-processing
        if prop.startswith('+'):
            # Expand '+' at the beginning of a rule as @include
            prop = '@include ' + prop[1:]
            # TODO what is this, partial sass syntax?
            try:
                if '(' not in prop or prop.index(':') < prop.index('('):
                    prop = prop.replace(':', '(', 1)
                    if '(' in prop:
                        prop += ')'
            except ValueError:
                pass
        elif prop.startswith('='):
            # Expand '=' at the beginning of a rule as @mixin
            prop = '@mixin' + prop[1:]
        elif prop.startswith('@prototype '):
            # Remove '@prototype '
            # TODO what is @prototype??
            prop = prop[11:]

        self.prop = prop

        # Minor parsing
        if prop.startswith('@'):
            self.is_atrule = True

            if prop.lower().startswith('@else if '):
                self.directive = '@else if'
                self.argument = prop[9:]
            else:
                directive, _, self.argument = prop.partition(' ')
                self.directive = directive.lower()
        else:
            self.directive = None
            self.argument = None

            if prop.endswith(':'):
                self.is_scope = True
            else:
                self.is_selector = True



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

    def __init__(self, calculator, parent_rule, lineno, prop, unparsed_contents):
        self.calculator = calculator
        self.parent_rule = parent_rule
        self.header = RuleHeader(prop)

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
        return self.prop.startswith('@')

    @property
    def is_nested_property(self):
        return self.prop.endswith(':') and not self.is_atrule
