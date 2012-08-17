"""..."""
# TODO
"""
    >>> css._scss_files = {}
    >>> css._scss_files['first.css'] = '''
    ... @option compress:no, short_colors:yes, reverse_colors:yes;
    ... .specialClass extends .basicClass {
    ...     padding: 10px;
    ...     font-size: 14px;
    ... }
    ... '''
    >>> css._scss_files['second.css'] = '''
    ... @option compress:no, short_colors:yes, reverse_colors:yes;
    ... .basicClass {
    ...     padding: 20px;
    ...     background-color: #FF0000;
    ... }
    ... '''
    >>> print css.compile() #doctest: +NORMALIZE_WHITESPACE
    /* Generated from: second.css */
    .basicClass,
    .specialClass {
        padding: 20px;
        background-color: red;
    }
    /* Generated from: first.css */
    .specialClass {
        padding: 10px;
        font-size: 14px;
    }
"""


# TODO; POSSIBLY UNSUPPORTED
"""
ADVANCED STUFF, NOT SUPPORTED (FROM SASS):
--------------------------------------------------------------------------------
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
... .mod {
...     margin: 10px;
... }
... .mod h1 {
...     font-size: 40px;
... }
... .cleanBox h1 extends .mod {
...     font-size: 60px;
... }
... ''') #doctest: +NORMALIZE_WHITESPACE
.cleanBox h1,
.mod {
    margin: 10px;
}
.cleanBox h1,
.mod h1 {
    font-size: 40px;
}
.cleanBox h1 {
    font-size: 60px;
}

http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html

Any rule that uses a:hover will also work for .hoverlink, even if they have other selectors as well
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
... .comment a.user:hover { font-weight: bold }
... .hoverlink { @extend a:hover }
... ''') #doctest: +NORMALIZE_WHITESPACE
.comment a.user:hover,
.comment .hoverlink.user {
    font-weight: bold;
}


Sometimes a selector sequence extends another selector that appears in another
sequence. In this case, the two sequences need to be merged.
While it would technically be possible to generate all selectors that could
possibly match either sequence, this would make the stylesheet far too large.
The simple example above, for instance, would require ten selectors. Instead,
Sass generates only selectors that are likely to be useful.
>>> print css.compile('''
... @option compress:no, short_colors:yes, reverse_colors:yes;
... #admin .tabbar a { font-weight: bold }
... #demo .overview .fakelink { @extend a }
... ''') #doctest: +NORMALIZE_WHITESPACE
#admin .tabbar a,
#admin .tabbar #demo .overview .fakelink,
#demo .overview #admin .tabbar .fakelink {
    font-weight: bold;
}

--------------------------------------------------------------------------------
"""
