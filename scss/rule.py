FILEID = 0
POSITION = 1
CODESTR = 2
DEPS = 3
CONTEXT = 4
OPTIONS = 5
SELECTORS = 6
PROPERTIES = 7
PATH = 8
INDEX = 9
LINENO = 10
MEDIA = 11
EXTENDS = 12
RULE_VARS = {
    'FILEID': FILEID,
    'POSITION': POSITION,
    'CODESTR': CODESTR,
    'DEPS': DEPS,
    'CONTEXT': CONTEXT,
    'OPTIONS': OPTIONS,
    'SELECTORS': SELECTORS,
    'PROPERTIES': PROPERTIES,
    'PATH': PATH,
    'INDEX': INDEX,
    'LINENO': LINENO,
    'MEDIA': MEDIA,
    'EXTENDS': EXTENDS,
}


def spawn_rule(from_rule=None, **kwargs):
    if from_rule is None:
        rule = CSSRule()
    else:
        rule = from_rule.copy()

    for k, v in kwargs.items():
        rule[RULE_VARS[k.upper()]] = v

    return rule


class CSSRule(object):
    """A CSS rule: combination of a selector and zero or more properties."""

    def __init__(self, file_id=None, position=None, code_string=None, deps=None,
            context=None, options=None, selectors=frozenset(), properties=None,
            path='./', index=None, lineno=0, media=None, extends=frozenset()):

        self.file_id = file_id
        self.position = position
        self.code_string = code_string
        self.context = context
        self.options = options
        self.selectors = selectors
        self.path = path
        self.lineno = lineno
        self.media = media
        self.extends = extends

        if deps is None:
            self.deps = set()
        else:
            self.deps = deps

        if properties is None:
            self.properties = []
        else:
            self.properties = properties

        if index is None:
            self.index = {0: '<unknown>'}
        else:
            self.index = index

    def copy(self):
        return type(self)(
            file_id=self.file_id,
            position=self.position,
            code_string=self.code_string,
            #deps=set(self.deps),
            deps=self.deps,
            context=self.context,
            options=self.options,
            selectors=self.selectors,
            #properties=list(self.properties),
            properties=self.properties,
            path=self.path,
            #index=dict(self.index),
            index=self.index,
            lineno=self.lineno,
            media=self.media,
            extends=self.extends,
        )



    def __iter__(self):
        raise TypeError


    def __setitem__(self, key, value):
        """Backwards compatibility for the list approach."""
        if key == FILEID:
            self.file_id = value
        elif key == POSITION:
            self.position = value
        elif key == CODESTR:
            self.code_string = value
        elif key == DEPS:
            self.deps = value
        elif key == CONTEXT:
            self.context = value
        elif key == OPTIONS:
            self.options = value
        elif key == SELECTORS:
            self.selectors = value
        elif key == PROPERTIES:
            self.properties = value
        elif key == PATH:
            self.path = value
        elif key == INDEX:
            self.index = value
        elif key == LINENO:
            self.lineno = value
        elif key == MEDIA:
            self.media = value
        elif key == EXTENDS:
            self.extends = value
        else:
            raise KeyError(key)

    def __getitem__(self, key):
        """Backwards compatibility for the list approach."""
        if key == FILEID:
            return self.file_id
        elif key == POSITION:
            return self.position
        elif key == CODESTR:
            return self.code_string
        elif key == DEPS:
            return self.deps
        elif key == CONTEXT:
            return self.context
        elif key == OPTIONS:
            return self.options
        elif key == SELECTORS:
            return self.selectors
        elif key == PROPERTIES:
            return self.properties
        elif key == PATH:
            return self.path
        elif key == INDEX:
            return self.index
        elif key == LINENO:
            return self.lineno
        elif key == MEDIA:
            return self.media
        elif key == EXTENDS:
            return self.extends
        else:
            raise KeyError(key)
