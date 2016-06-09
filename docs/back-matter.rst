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
output with the ``.css`` file of the same name.  To run only particular tests,
you can pass them directly as filenames::

    py.test scss/tests/files/general/000-smoketest.scss

There are also several tests borrowed from the Ruby and C implementations.
Many of these don't work (due to missing features, different error messages,
slightly different formatting, etc.), so to reduce the useless noise produced
by a test run, you must explicitly opt into them with ``--include-ruby``, even
when using a file filter.  These files are in the ``from-ruby/`` and
``from-sassc/`` subdirectories.

Other than the borrowed tests, the directory names are arbitrary.


License and copyright
---------------------

Copyright © 2012 German M. Bravo (Kronuz), with additional heavy contributions
by Eevee (Lexy Munroe).  Licensed under the `MIT license`_.

.. _MIT license: http://www.opensource.org/licenses/mit-license.php

pyScss is inspired by and partially derived from various projects:

* `Compass`_ © 2009 Christopher M. Eppstein
* `Sass`_ © 2006-2009 Hampton Catlin and Nathan Weizenbaum
* `xCSS`_ © 2010 Anton Pawlik

.. _Compass: http://compass-style.org/
.. _Sass: http://sass-lang.com/
.. _xCSS: http://xcss.antpaw.org/docs/

Special thanks to Yelp for allowing Eevee to contribute to pyScss during
working hours.  Yelp does not claim copyright.


Changelog
---------

1.3.5 (June 8, 2016)
^^^^^^^^^^^^^^^^^^^^

* The new ``less2scss`` module attempts to convert Less syntax to SCSS.
* The ``*-exists`` functions from Sass 3.3 are now supported.
* The contents of a file ``@import``-ed in the middle of an input file now
  appears in the expected place, not at the end of the output.
* Double-slashes within URLs, as often happens with base64-encoded data URLs,
  are no longer stripped as comments.
* Nesting selectors that end with a combinator, e.g. ``div > { p { ... } }``,
  now works correctly.
* ``invert()`` is now left alone when the argument is a number, indicating the
  CSS filter rather than the Sass function.
* ``if()`` now evaluates its arguments lazily.
* ``str-slice()`` now silently corrects out-of-bounds indices.
* ``append()`` now defaults to returning a space-delimited list, when the given
  list has fewer than two elements.
* ``-moz-calc`` and ``-webkit-calc`` are recognized as variants of the
  ``calc()`` CSS function.
* Filenames containing dots can now be imported.
* Properties with a computed value of ``null`` are now omitted from the output.
* The ``opacity`` token in IE's strange ``alpha(opacity=N)`` construct is now
  recognized case-insensitively.
* The Compass gradient functions now recognize ``currentColor`` as a color.
* The fonts extension should now work under Python 3.
* Escaped astral plane characters no longer crash narrow Python 2 builds.
* The alpha value in ``rgba(...)`` is no longer truncated to only two decimal places.
* Some edge cases with float precision were fixed, so 742px - 40px is no longer
  701.99999999px.

1.3.4 (Dec 15, 2014)
^^^^^^^^^^^^^^^^^^^^

* The modulus (``%``) operator is now supported.
* ``/`` and ``-`` inside an expression work correctly; this fixes some cases of using vanilla CSS's ``/`` syntax.
* Relative imports have been more fixed.
* Line numbers in error messages are...  more likely to be correct.
* Sass at-blocks now parse correctly even when there's no space after the block name, e.g. ``@if(foo){...}``.
* A few more cases of ``#{...}`` being replaced lexically have been switched to real parsing.

With these changes, pyScss can now successfully compile Zurb Foundation 5.

1.3.3 (Nov 18, 2014)
^^^^^^^^^^^^^^^^^^^^

* URLs with quotes now parse as the `Url` type, not as generic functions.  Fixes some uses of ``@import``.
* A ``return`` got lost in the Compass gradient code, which would break some uses of gradients.
* Some API work in an attempt to get django-pyscss working against 1.3.

1.3.2 (Oct 17, 2014)
^^^^^^^^^^^^^^^^^^^^

* Fix another couple embarrassing bugs, this time with the CLI.
* Fix the auto behavior of ``join()`` to match Ruby.
* Fully allow arbitrary expressions as map keys; previously, this only worked
  for the first key.  LL(1) is hard.
* Restore Python 3.2 compatibility.
* Travis CI and Coveralls are now enabled.

1.3.1 (Oct 16, 2014)
^^^^^^^^^^^^^^^^^^^^

Fixes an embarrassing crash when compiling multiple files together.

1.3.0 (Oct 15, 2014)
^^^^^^^^^^^^^^^^^^^^

This is a somewhat transitional release along the road to 2.0, which will
remove a lot of deprecated features.

Sass/CSS compatibility
""""""""""""""""""""""

* Importing files from a parent directory with ``../`` now works (as long as the imported file is still on the search path).
* Multiple CSS imports on the same line are now left unchanged.  (Previously, the line would be repeated once for each import.)
* CSS 3 character set detection is supported.
* CSS escapes within strings are supported (though, unlike Sass, are usually printed literally rather than escaped).
* Map keys may now be arbitrary expressions.
* Slurpy named arguments are now supported.
* ``!global`` on variable assignments is now supported (and does nothing, as in Sass).
* `rebeccapurple`_ is understood as a color name.

.. _rebeccapurple: http://meyerweb.com/eric/thoughts/2014/06/19/rebeccapurple/

Additionally, a great many more constructs should now parse correctly.  By default, when pyScss encounters a parse error, it replaces any interpolations and variables, and treats the result as a single opaque string.

This was the only way syntax like ``url(http://foo/bar)`` was recognized, since a colon is usually not allowed in the middle of a bareword.  As a result, code like ``background: url(...) scale-color(...);`` didn't work, because the url would fail to parse and so pyScss would never even know that ``scale-color`` is supposed to be a function call.

Now, the parser understands most of the unusual quirks of CSS syntax:

* ``()`` is recognized as an empty list.
* ``url()`` is fully supported.
* ``expression()``, ``alpha(opacity=...)``, and ``calc()`` are supported (and left alone, except for interpolation).
* Interpolation is part of the parser, rather than being applied before parsing, so there should be far fewer bugs with it.
* CSS escapes within barewords are recognized (and ignored).
* ``!important`` may have whitespace after the ``!``.

Glossing over a bad parse now spits out a deprecation warning, and will be
removed entirely in 2.0.

Bug fixes
"""""""""

* Old-style pseudo-element selectors (``:before`` and friends, written with only one colon) always stay at the end of the selector.
* The CSS3 ``grayscale(90%)`` function is now left alone, rather than being treated as a Sass function.  (Previously, only unitless numbers would trigger this behavior.)
* Placeholder selectors (``%foo``) no longer end up in the output.
* Iterating over a list of lists with a single variable works (again).
* File path handling is much more polite with Windows directory separators.
* At-rules broken across several lines are now recognized correctly.
* ``@for ... to`` now excludes the upper bound.
* ``@extend`` no longer shuffles rules around, and should now produce rules in the same order as Ruby Sass.  It also produces rules in the correct order when extending from the same rule more than once.  Hopefully it's now correct, once and for all.
* Fixed a couple more Compass gradient bugs.  Probably.


New features
""""""""""""

* Compatibility with Python 3.2, allegedly.
* Support for building SVG font sheets from within stylesheets.
* Error messages have been improved once again: parse errors should be somewhat less cryptic, the source of mixins is included in a traceback, and missing closing braces are reported.

Backwards-incompatible changes
""""""""""""""""""""""""""""""

* Missing imports are now fatal.
* Much sloppy behavior or reliance on old xCSS features will now produce deprecation warnings.  All such behaviors will be removed in pyScss 2.0.

Internals
"""""""""

* The C speedups module is now Unicode-aware, and works under CPython 3.
* There's no longer a runtime warning if the speedups module is not found.
* pyScss is now (a lot more) Unicode-clean; everything internally is treated as text, not bytes.
* Compiling the grammar is now much less painful, and doesn't require copy-pasting anything.
* Several large modules have been broken up further.  ``__init__`` is, at last, virtually empty.
* All the built-in functions have been moved into built-in extensions.

1.2.0 (Oct 8, 2013)
^^^^^^^^^^^^^^^^^^^

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
