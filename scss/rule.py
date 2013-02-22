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
}


def spawn_rule(rule=None, **kwargs):
    if rule is None:
        rule = [None] * len(RULE_VARS)
        rule[DEPS] = set()
        rule[SELECTORS] = ''
        rule[PROPERTIES] = []
        rule[PATH] = './'
        rule[INDEX] = {0: '<unknown>'}
        rule[LINENO] = 0
    else:
        rule = list(rule)
    for k, v in kwargs.items():
        rule[RULE_VARS[k.upper()]] = v
    return rule
