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

    This is an example configuration file.

    IMPORTANT: It MUST named "scss_settings.py" or it won't work.

"""

# Tell pyScss to be more verbose.
# Only useful for devs or pyScss monkey patchers.
# Default: 1
VERBOSITY = 1

# Tell pyScss to work, or not to work, in debug mode.
# Currently not working? :/
# Default: 0
DEBUG = 0


# Project root path is also configurable
# Default: absolute path to dirname of current file (the one that imports pyScss)
# PROJECT_ROOT = "/var/www/media"

# Urls for sass frameworks.
# Must begin with "/".
# Default: "/sass/frameworks/"
SASS_FRAMEWORKS = "/my_sass/potato_frameworks/"

# Url for static.
# Must begin with "/".
# Default: "/static/"
STATIC_URL = "/my_static/"

# Url for assets.
# Must begin with "/".
# Default: "/static/assets/""
ASSETS_URL = "/my_static/my_assets/"
