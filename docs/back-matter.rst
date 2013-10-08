Back matter
===========

Reporting bugs
--------------

If you have any suggestions, bug reports, or minor annoyances, please report
them to the issue tracker on GitHub: http://github.com/Kronuz/pyScss/issues


Contributing
------------

Please send us pull requests on GitHub!  https://github.com/Kronuz/pyScss


Running the test suite
----------------------

The test suite is built atop the excellent `py.test`_ library, and can be run with::

    py.test

from the root of a source checkout.

.. _py.test: http://pytest.org/latest/

Most of the tests are pairs of input/output files in ``scss/tests/files``; the
test suite scans for these, compiles all the ``.scss`` files, and compares the
output with the ``.css`` file of the same name.  You can limit which file tests
run::

    py.test --test-file-filter=REGEX,REGEX,REGEX...

There are also several tests borrowed from the Ruby and C implementations.
Many of these don't work (due to missing features, different error messages,
slightly different formatting, etc.), so to reduce the useless noise produced
by a test run, you must explicitly opt into them with ``--include-ruby``, even
when using a file filter.  These files are in the ``from-ruby/`` and
``from-sassc/`` subdirectories.

Additionally, test files in the ``xfail/`` subdirectory are assumed to fail.
Other than these cases, the directory names are arbitrary.


License and copyright
---------------------

Copyright © 2012 German M. Bravo (Kronuz).  Licensed under the `MIT license`_.

.. _MIT license: http://www.opensource.org/licenses/mit-license.php

pyScss is inspired by and partially derived from various projects:

* `Compass`_ © 2009 Christopher M. Eppstein
* `Sass`_ © 2006-2009 Hampton Catlin and Nathan Weizenbaum
* `xCSS`_ © 2010 Anton Pawlik

.. _Compass: http://compass-style.org/
.. _Sass: http://sass-lang.com/
.. _xCSS: http://xcss.antpaw.org/docs/


Changelog
---------

1.2.0 (not yet released)
^^^^^^^^^^^^^^^^^^^^^^^^

This is a significant release that greatly increases compatibility with the
reference compiler; in particular, the Sass port of Bootstrap now compiles.

There are a lot of changes here, so please feel free to report any bugs you
see!  The goal is 100% compatibility with the Ruby project.

Missing Sass features
"""""""""""""""""""""

* Dashes and underscores are treated as interchangeable in variable, function, and mixin names.
* Rule blocks in the form ``background: red { ... }`` are now supported.
* Colors are output as their shortest representation, and never as ``hsl()``.  The separate compiler options for compressing colors have been removed.
* The color modification functions (``adjust-color``, etc.) now work reliably.
* ``transparent`` is recognized as a color.
* Unrecognized units are now supported and treated as opaque.
* Arbitrary combinations of units (e.g., ``px * px``) are supported for intermediate values.  Unit cancellation now works reliably.
* Comparison and addition are now more in line with the Ruby behavior.
* ``/`` is now left untouched when it appears between literals, as in ``font: 0 / 0``.
* ``null`` is supported.
* ``zip()`` is supported.
* ``grayscale()`` now knows it's also a CSS3 filter function, and won't be evaluated if its argument is a number.
* Slurpy arguments (``some-function($args...)``) are supported.
* ``@extend`` has been greatly improved: it eliminates common ancestors and works in many complex cases that used to produce strange results.
* Several Compass functions now adhere more closely to Compass's behavior.  ``linear-gradient()`` is less likely to wreck valid CSS3 syntax.
* Compass's ``e()``, ``pow()``, ``log()``, and ``sqrt()`` are now supported.

Bug fixes
"""""""""

* Interactive mode works.  Again.
* Color names in strings and selectors are no longer replaced with hex equivalents.
* Unrecognized ``@``-rule blocks such as ``@keyframes`` are left alone, rather than being treated like selectors.
* ``@media`` blocks aren't repeated for every rule inside.
* Pound-interpolation always drops quotes on strings.
* Single quoted strings no longer lose their quotes when rendered.
* ``+ foo { ... }`` is now recognized as a nested block, not an include.
* ``color-stop()`` and several proposed CSS4 functions no longer produce "unrecognized function" warnings.
* Several obscure bugs with variable scoping have been fixed, though a couple others remain.
* Several bugfixes to the C speedups module to bring it in line with the behavior of the pure-Python scanner.

New features
""""""""""""

* Python 3 support.  As a result, Python 2.5 no longer works; whether this is a bug or a feature is not yet clear.
* It's possible to write custom Sass functions in Python, though the API for this is not final.
* Experimental support for the map type and destructuring ``@each``, both unreleased additions to the Ruby project.
* Support for the new string and list functions in Sass 3.3.
* Added ``background-brushed``.

Backwards-incompatible changes
""""""""""""""""""""""""""""""

* Configuration via monkeypatching the ``scss`` module no longer works.  Monkeypatch ``scss.config`` instead.
* ``em`` and ``px`` are no longer compatible.
* Unrecognized variable names are now a fatal error.

Internals
"""""""""

* No longer a single 5000-line file!
* Vastly expanded test suite, including some experimental tests borrowed from the Ruby and C implementations.
* Parser now produces an AST rather than evaluating expressions during the parse, which allows for heavier caching and fixes some existing cache bugs.
* The type system has been virtually rewritten; types now act much less like Python types, and compilation uses Sass types throughout rather than mixing Python types with Sass types.

1.1.5 (Feb 15, 2013)
^^^^^^^^^^^^^^^^^^^^

* ``debug_info`` now properly produces rules that can be used by FireSass and Google Chrome SASS Source Maps.
* Improved memory usage for large sets of files to be used as sprites.
* Warns about IE 4095 maximum number of selectors.
* ``debug_info`` prints info as comments if specified as ``comments``.
* Better handling of undefined variables.
* Added CSS filter functions and ``skewX`` ``skewY``.
* Command line tool and entry point fixed.
* Fix cache buster URLs when paths already include queries or fragments.
* Hashable Values.

1.1.4 (Aug 8, 2012)
^^^^^^^^^^^^^^^^^^^

* Added ``--debug-info`` command line option (for *FireSass* output).
* Added compass helper function ``reject()``.
* Added ``undefined`` keyword for undefined variables.

1.1.3 (Jan 9, 2012)
^^^^^^^^^^^^^^^^^^^

* Support for the new Sass 3.2.0 features (``@content`` and placeholder selectors)
* Fixed bug with line numbers throwing an exception.

1.1.2 (Jan 3, 2012)
^^^^^^^^^^^^^^^^^^^

* Regression bug fixed from 1.1.1

1.1.1 (Jan 2, 2012)
^^^^^^^^^^^^^^^^^^^

* Added optional C speedup module for an amazing boost in scanning speed!
* Added ``headings``, ``stylesheet-url``, ``font-url``, ``font-files``, ``inline-font-files`` and ``sprite-names``.

1.1.0 (Dec 22, 2011)
^^^^^^^^^^^^^^^^^^^^

* Added ``min()`` and ``max()`` for lists.
* Removed exception raise.

1.0.9 (Dec 22, 2011)
^^^^^^^^^^^^^^^^^^^^

* Optimizations in the scanner.
* Added ``background-noise()`` for compass-recipes support.
* ``enumerate()`` and ``range()`` can go backwards. Ex.: ``range(3, 0)`` goes from 3 to 0.
* Added line numbers and files for errors.
* Added support for *Firebug* with *FireSass*.
* ``nth(n)`` is round (returns the ``nth mod len`` item of the list).
* ``--watch`` added to the command line.
* Several bugs fixed.

1.0.8 (May 13, 2011)
^^^^^^^^^^^^^^^^^^^^

* Changed source color (``$src-color``) default to black.
* Moved the module filename to ``__init__.py`` and module renamed back to scss.
