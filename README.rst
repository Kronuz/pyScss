pyScss, a Scss compiler for Python
==================================

pyScss2 is a compiler for the `Sass`_ language, a superset of CSS3 that adds
programming capabilities and some other syntactic sugar.

.. _Sass: http://sass-lang.com/

Originally it was forked from unmaintained https://github.com/Kronuz/pyScss.

Quickstart
----------

You need Python 2.7+ or 3.3+.  PyPy is also supported.

Installation::

    pip install pyScss2

Usage::

    python -mscss < style.scss

Python API::

    from scss import Compiler
    Compiler().compile_string("a { color: red + green; }")


Features
--------

95% of Sass 3.2 is supported.  If it's not supported, it's a bug!  Please file
a ticket.

Most of Compass 0.11 is also built in.


Further reading
---------------

Documentation is in Sphinx.  You can build it yourself by running ``make html``
from within the ``docs`` directory.

The canonical syntax reference is part of the Ruby Sass documentation:
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html


Obligatory
----------

Copyright © 2020 Ivan Kolodyazhny (e0ne).  Additional credits in the
documentation.

Licensed under the `MIT license`_, reproduced in ``LICENSE``.

.. _MIT license: http://www.opensource.org/licenses/mit-license.php
