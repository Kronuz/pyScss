Installation and usage
======================

Installation
------------

pyScss requires only Python 2.6 or later, including Python 3.x.  PyPy is also
known to work.  Install with pip::

    pip install pyScss

Its lone dependency is the ``six`` library, which pip should install for you.


Usage
-----

Run from the command line by using ``-m``::

    python -mscss < file.scss

Specify directories to search for imports with ``-I``.  See ``python -mscss
--help`` for more options.

.. note::

    ``-mscss`` will only work in Python 2.7 and above.  For Python 2.5 and 2.6,
    ``-m`` doesn't work with packages, and you need to invoke::

        python -mscss.tool



Interactive mode
----------------

To get a REPL::

    python -mscss --interactive

Example session::

    $ python scss.py --interactive
    >>> @import "compass/css3"
    >>> show()
    ['functions', 'mixins', 'options', 'vars']
    >>> show(mixins)
    ['apply-origin',
        'apply-transform',
        ...
        'transparent']
    >>> show(mixins, transparent)
    @mixin transparent() {
        @include opacity(0);
    }
    >>> 1px + 5px
    6px
    >>> _


Compass example
---------------

With ``--load-path`` or ``scss.config.LOAD_PATHS`` set to Compass and Blueprint
roots, you can compile with Compass like with the following::

    @option compress: no;

    $blueprint-grid-columns : 24;
    $blueprint-grid-width   : 30px;
    $blueprint-grid-margin  : 10px;
    $font-color             : #333;

    @import "compass/reset";
    @import "compass/utilities";
    @import "blueprint";

    // your code...
