#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
pyScss, a Scss compiler for Python

@author     German M. Bravo (Kronuz) <german.mb@gmail.com>
@version    1.0
@see        https://github.com/Kronuz/pyScss
@copyright  (c) 2011 German M. Bravo (Kronuz)
@license    MIT License
            http://www.opensource.org/licenses/mit-license.php

pyScss compiles Scss, a superset of CSS that is more powerful, elegant and
easier to maintain than plain-vanilla CSS. The library acts as a CSS source code
preprocesor which allows you to use variables, nested rules, mixins, andhave
inheritance of rules, all with a CSS-compatible syntax which the preprocessor
then compiles to standard CSS.

Scss, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten, many bugs have been fixed and it
has been extensively extended to support almost the full range of Sass' Scss
syntax and functionality.

Bits of code in pyScss come from various projects:
Compass:
    (c) 2009 Christopher M. Eppstein
    http://compass-style.org/
Sass:
    (c) 2006-2009 Hampton Catlin and Nathan Weizenbaum
    http://sass-lang.com/
xCSS:
    (c) 2010 Anton Pawlik
    http://xcss.antpaw.org/docs/

    These are the default settings for every pyScss project.

    To customize them check "example_settings.py" or the README.

"""

__all__ = [
    "VERBOSITY",
    "DEBUG",
    "SASS_FRAMEWORKS",
    "STATIC_URL",
    "ASSETS_URL",
]

## User configurable settings
VERBOSITY = 1
DEBUG = 0
# Urls for sass frameworks, static and assets:
SASS_FRAMEWORKS = '/sass/frameworks/'
STATIC_URL = '/static/'
ASSETS_URL = '/static/assets/'
