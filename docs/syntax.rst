.. highlight:: scss

=============
pyScss syntax
=============

Supported Sass features
=======================

pyScss is mostly compatible with Sass 3.2 and has partial support for the
upcoming Sass 3.3.  The canonical syntax reference is in the Sass
documentation:
http://sass-lang.com/docs/yardoc/file.SASS_REFERENCE.html


Both syntaxes
-------------

SCSS (CSS3 superset) is the primary syntax, but there's experimental support
for the SASS (YAML-like) syntax.


Built-in functions
------------------

All of the Sass 3.2 functions described in `the Sass documentation`_ are
supported.

.. _the Sass documentation: <http://sass-lang.com/docs/yardoc/Sass/Script/Functions.html


Rule nesting
------------

Rule/selector nesting and the ``&`` parent-reference selector are both
supported.

Example::

    .selector {
        a {
            display: block;
        }
        strong {
            color: blue;
        }
    }

Produces::

    .selector a {
        display: block;
    }
    .selector strong {
        color: blue;
    }


Variables, data types
---------------------

Variables are supported.  All of the Sass data types—strings, numbers,
booleans, colors, lists, maps, and null—are supported.

Example::

    $main-color: #ce4dd6;
    $style: solid;
    $side: bottom;
    #navbar {
        border-#{$side}: {
            color: $main-color;
            style: $style;
        }
    }

Produces::

    #navbar {
        border-bottom-color: #ce4dd6;
        border-bottom-style: solid;
    }


Functions and mixins
--------------------

``@function``, ``@mixin``, and ``@include`` (optionally with ``@content``) are
supported.

Named arguments (``foo($name: value)``) and slurpy arguments
(``foo($args...)``) are also supported.

Example::

    @mixin rounded($side, $radius: 10px) {
        border-#{$side}-radius: $radius;
        -moz-border-radius-#{$side}: $radius;
        -webkit-border-#{$side}-radius: $radius;
    }
    #navbar li { @include rounded(top); }
    #footer { @include rounded(top, 5px); }
    #sidebar { @include rounded(left, 8px); }

Produces::

    #navbar li {
        border-top-radius: 10px;
        -moz-border-radius-top: 10px;
        -webkit-border-top-radius: 10px;
    }
    #footer {
        border-top-radius: 5px;
        -moz-border-radius-top: 5px;
        -webkit-border-top-radius: 5px;
    }
    #sidebar {
        border-left-radius: 8px;
        -moz-border-radius-left: 8px;
        -webkit-border-left-radius: 8px;
    }


Rule extension
--------------

``@extend`` is supported, though some particularly thorny edge cases may not
produce output identical to the reference compiler.

Example::

    .error {
        border: 1px #f00;
        background-color: #fdd;
    }
    .error.intrusion {
        background-image: url("/image/hacked.png");
    }
    .seriousError {
        @extend .error;
        border-width: 3px;
    }

Produces::

    .error,
    .seriousError {
        border: 1px red;
        background-color: #fdd;
    }
    .error.intrusion,
    .seriousError.intrusion {
        background-image: url("/image/hacked.png");
    }
    .seriousError {
        border-width: 3px;
    }


Conditions
----------

``@if``, ``@else if``, and ``@else`` are supported.


Loops
-----

Both types of iteration are supported::

    @for $n from 1 through 9 {
        .span-#{$n} { width: $n * 10%; }
    }

    @each $color in red, blue, yellow {
        .button-#{$color} {
            background-color: $color;
        }
    }

Additionally, the unpacking-iteration syntax in Sass trunk is supposed; see
:ref:`maps`.


.. _maps:

Maps
----

pyScss has experimental support for maps, a data type recently added to Sass
trunk.  Maps are defined with colons inside parentheses::

    $colors: (
        text: black,
        background: white
    );

Keys may be any Sass expression, not just strings.

Maps are manipulated with a handful of map functions::

    a {
        color: map-get($colors, text);
        background-color: map-get($colors, background);
    }

A map is semantically equivalent to a list of 2-lists, stored in the order they
appeared when the map was defined.  Any list operation will work on a map::

    div {
        // I don't know why you'd do this  :)
        margin: nth($colors, 1);  // => text, black
    }

Maps may be iterated over with ``@each``, of course, but each item will be a
somewhat clumsy 2-list.  Instead, you can give multiple variables to do an
unpacking iteration::

    @each $key, $value in $colors {
        // I don't know why you'd do this either!
        [data-style=$key] {
            color: $value;
        }
    }

This syntax works on any list-of-lists.


Everything is a list
--------------------

Another change borrowed from Sass trunk: any scalar type (string, number,
boolean, etc.) will also act as a list of one element when used where a list is
expected.  This is most useful when writing Python extensions, but may also
save you from checking ``type-of`` in a complex API.


Compass support
===============

An arbitrary cross-section of Compass 0.11 is supported:

    * **Math functions**: ``sin``, ``cos``, ``tan``, ``round``, ``ceil``, ``floor``, ``pi``, ``e``
    * **Images**: ``image-url``, ``image-width``, ``image-height``...
    * **Embedded (inline) images**: ``inline-image``


.. todo::

    Document exactly what's supported, how it works, and what's missing.

.. note::

    Currently, Compass support is provided by default, which has led to some
    surprising behavior since parts of Compass conflict with parts of CSS3.  In
    the future, Compass will become an extension like it is for Ruby, and you
    will have to opt in.


Sprites
-------

Example::

    $icons: sprite-map("sociable/*.png"); // contains sociable/facebook.png among others.
    div {
        background: $icons;
    }
    @each $icon in sprites($icons) {
        div .#{$icon} {
            width: image-width(sprite-file($icons, $icon));
            height: image-height(sprite-file($icons, $icon));
            background-position: sprite-position($icons, $icon);
        }
    }

...generates a new sprite file and produces something like::

    div {
        background: url("/static/assets/u8Y7yEQL0UffAVw5rX7yhw.png?_=1298240989") 0px 0px no-repeat;
    }
    div .facebook {
        width: 32px;
        height: 32px;
        background-position: 0px 0px;
    }
    div .twitter {
        width: 32px;
        height: 32px;
        background-position: 0px -32px;
    }
    ...


pyScss-specific extensions
==========================

pyScss supports some constructs that upstream Sass does not, for various
reasons.  Listed here are "blessed" features in no danger of being removed,
though you should avoid them if you're at all interested in working with the
reference compiler.

There are also some deviations that only exist for backwards compatibility; you
should **not** rely on them, they will start spewing warnings at some point in
the future, and eventually they will disappear.  They are listed separately in
:ref:`deprecated-features`.


``@option``
-----------

Compiler options may be toggled at runtime with ``@option``.  At the moment the
only supported option is ``compress``, to control whether the output is
compressed::

    @option compress: true;


Multiplying strings by numbers
------------------------------

Much like in Python, this works::

    content: "foo" * 3;  // => "foofoofoo"

This is a runtime error in the reference compiler.


.. _deprecated-features:

Deprecated features
===================

Brackets to delimit expressions
-------------------------------

In an expression, square brackets are equivalent to parentheses::

    margin-top: [1px + 2px] * 3;  // => 9px

This is a holdover from xCSS and will be removed in the future.


``extends``
-----------

There's an alternative syntax for ``@extend``::

    a extends b {
        ...
    }

This is identical to::

    a {
        @extend b;
        ...
    }

This is a holdover from xCSS and will be removed in the future.


``self`` selector
-----------------

``self`` is an alias for ``&``::

    a {
        self:hover {
            text-decoration: underline;
        }
    }

This is a holdover from xCSS and will be removed in the future.


``@variables`` block
--------------------

Variables may be declared in a dedicated block::

    @variables {
        $color: red;
    }

``@vars`` is an alias for ``@variables``.

This is a holdover from xCSS and will be removed in the future.


``+foo`` to include a mixin
---------------------------

This::

    div {
        +border-radius 3px;
    }

Is equivalent to this::

    div {
        @include border-radius(3px);
    }

This is the same as the Sass syntax, but causes some parsing ambiguity, since
``+foo`` with a block could be either a nested CSS block with a sibling
selector or a mixin call.  Its future is uncertain, but you should probably
avoid using it in SCSS files.


Soft errors
-----------

pyScss is much more liberal in what it accepts than the reference compiler; for
example, rules at the top level and missing closing braces are accepted without
complaint, and attempting to use a non-existent mixin only results in a
warning.

pyScss 2.0 is likely to be much stricter; don't rely on any particular abuse of
syntax to work in the future.


Operations on lists
-------------------

Binary operations with a list on the left-hand side are performed
element-wise::

    p {
        margin: (1em 0 3em) * 0.5;  // => 0.5em 0 1.5em
    }

Given that future versions of the reference compiler are likely to introduce
built-in list operations, the future of this feature is unclear.


Mixin "injection"
-----------------

A mixin defined like this::

    @mixin foo(...) {
        // ...
    }

will accept **any** keyword arguments, which will be available as variables
within the mixin.

This behavior exists for historical reasons and due to the lack of a
``**kwargs`` equivalent within Sass.  Its usage makes mixin behavior harder to
understand and you should not use it.


Unsupported Sass features
=========================

Some Sass features are not supported or have some gaps.  Each of these may be
considered a bug.

CLI
---

pyScss's command-line arguments are not entirely compatible with those of the
reference compiler.


Sass 3.3
--------

The following Sass 3.3 improvements are not yet implemented, but are planned
for the near future:

* Use of ``&`` in expressions.
* ``@at-root``
* Source map support.
* Using ``...`` multiple times in a function call, or passing a map of
  arguments with ``...``.  Likewise, ``keywords()`` is not implemented.
* ``unique-id()``, ``call()``, and the various ``*-exists()`` functions are not
  implemented.
