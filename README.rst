pyScss, a Scss compiler for Python
==================================

|build-status| |coverage|

.. |build-status| image:: https://travis-ci.org/Kronuz/pyScss.svg?branch=master
    :target: https://travis-ci.org/Kronuz/pyScss

.. |coverage| image:: https://coveralls.io/repos/Kronuz/pyScss/badge.png
    :target: https://coveralls.io/r/Kronuz/pyScss

pyScss is a compiler for the `Sass`_ language, a superset of CSS3 that adds
programming capabilities and some other syntactic sugar.

.. _Sass: http://sass-lang.com/

Quickstart
----------

You need Python 2.6+ or 3.3+.  PyPy is also supported.

Installation::

    pip install pyScss

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
from within the ``docs`` directory, or read it on RTD:
http://pyscss.readthedocs.org/en/latest/

The canonical syntax reference is part of the Ruby Sass documentation:
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html


Obligatory
----------

Copyright © 2012 German M. Bravo (Kronuz).  Additional credits in the
documentation.

Licensed under the `MIT license`_, reproduced in ``LICENSE``.

.. _MIT license: http://www.opensource.org/licenses/mit-license.php
