pyScss, a Scss compiler for Python
==================================
:Author:
    German M. Bravo (Kronuz) <german.mb@gmail.com>

About
=====
pyScss compiles Scss (Sass), a superset of CSS that is more powerful, elegant
and easier to maintain than plain-vanilla CSS. The library acts as a CSS source
code preprocesor which allows you to use variables, nested rules, mixins, and
have inheritance of rules, all with a CSS-compatible syntax which the
preprocessor then compiles to standard CSS.

Scss, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten, many bugs have been fixed and it
has been extensively extended to support almost the full range of Sass' Scss
syntax and functionality.

Support
========
pyScss has most of the funcitonality in Sass 3.2 ...it supports:

    * **Compass**: Compass 0.11 Support
    * **Nested rules**
    * **Keyword arguments**
    * **Mixins**: `@mixin`, `@include`
    * **Functions**: `@function`, `@return`
    * **Inheritance**: `@extend`
    * **Conditions**: `@if`, `@else if`, `@else`
    * **Loops**: `@for`, `@each`
    * **Variables**: `$`, `@variables`, `@vars`
    * **Sprites**: `sprite-map()`, `sprite()`, `sprite-position()`, `sprite-url()`, ...
    * **Images**: `image-url()`, `image-width()`, `image-height()`, ...
    * **Embedded (inline) images**: `inline-image()`
    * **Colors handling**: `adjust-color()`, `scale-color()`, `opacify()`/`transparentize()`, `lighten()`/`darken()`, `mix()`, ...
    * **Math functions**: `sin()`, `cos()`, `tan()`, `round()`, `ceil()`, `floor()`, `pi()`, ...
    * **CSS Compression**: `@option compress:yes;`

Usage
=====
Usage example::

    from scss import Scss
    css = Scss()
    css.compile("a { color: red + green; }")

Or compile from the command line::

    python scss.py < file.scss

Interactive mode::

    python scss.py -i

Examples
========
#. **Nested Rules**
    Example::

	@options compress: no;
	.selector {
	    a {
		display: block;
	    }
	    strong {
		color: blue;
	    }
	}

    ...produces::

	.selector a {
	    display: block;
	}
	.selector strong {
	    color: #00f;
	}

#. **Variables**
    Example::

	@options compress: no;
	$main-color: #ce4dd6;
	$style: solid;
	$side: bottom;
	#navbar {
	  border-#{$side}: {
	    color: $main-color;
	    style: $style;
	  }
	}

    ...produces::

	#navbar {
		border-bottom-color: #ce4dd6;
		border-bottom-style: solid;
	}

#. **Mixins**
    Example::

	@options compress: no;
	@mixin rounded($side, $radius: 10px) {
	  border-#{$side}-radius: $radius;
	  -moz-border-radius-#{$side}: $radius;
	  -webkit-border-#{$side}-radius: $radius;
	}
	#navbar li { @include rounded(top); }
	#footer { @include rounded(top, 5px); }
	#sidebar { @include rounded(left, 8px); }

    ...produces::

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

#. **Extend** (using `@extend`)
    Example::

	@options compress: no;
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

    ...produces::

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


#. **Sprites** (using `sprite-map()`)
    Example::

	@options compress: no;
	$icons: sprite-map("images/sociable/*.png"); // contains images/sociable/facebook.png among others.

	div {
		background: $icons;
	}

	div .facebook {
		width: image-width(sprite-file($icons, facebook));
		height: image-height(sprite-file($icons, facebook));
		background-position: sprite-position($icons, facebook);
	}

	div .twitter {
		width: image-width(sprite-file($icons, twitter));
		height: image-height(sprite-file($icons, twitter));
		background-position: sprite-position($icons, twitter);
	}

    ...generates a new sprite file and produces something like::

	div {
		background: url('/media/assets/eli2Rxy5MXpWj4uWPAHn5w.png?_=1297402328') 0 0 no-repeat;
	}

	div .facebook {
		width: 32px;
		height: 32px;
		background-position: -128px 0;
	}

	div .twitter {
		width: 32px;
		height: 32px;
		background-position: -224px 0;
	}

#. **Interactive mode**
    Example::

	$ python scss.py -i
	>>> @import compass/css
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
	>>> _

Sass Sassy CSS
==============
pyScss is a Scss (Sass) implementation for Python.
Currently it implements @mixin, @include, @if, @else, @for, and @import... it
also implements many of the Sass functions including colors function like
hsla(), hsl(), darken(), lighten(), mix(), opacify(), transparentize(),
saturate(), desaturate(), etc.) as well as sprite-map(), sprite-file(),
image-width(), image-height() and the others.

In the file `scss.py`, by the top, configure the LOAD_PATHS to point to your
Compass framework path (I have `frameworks/compass/*.scss` and
`framework/blueprint/*.scss` files in my project directory:
`/usr/local/www/project/`, so I have that set for that path by default)

I have succesfully compiled some Compass using `python scss.py < myfile.css` the
following `myfile.css`::

	@options compress: no;

	$blueprint-grid-columns : 24;
	$blueprint-grid-width   : 30px;
	$blueprint-grid-margin  : 10px;
	$font-color	     : #333;

	@import "compass/reset";
	@import "compass/utilities";
	@import "blueprint";

	// Stuff goes here...

Benchmarks
==========
    pyScss has been optimized for speed. Compiling **Compass 0.11.beta.2**
    (`compass/doc-src/content/stylesheets/screen.scss`)
    
    ...using **Sass 3.1.0.alpha.221**::

	Compilation took 2.683s (w/o cache)
	Compilation took 1.35s  (cached)
    
    ...using **pyScss 1.0 beta**::

	Compilation took 0.614s

License
=======
MIT License. See *LICENSE* for details.
http://www.opensource.org/licenses/mit-license.php

Copyright
=========
	Copyright (c) 2011 German M. Bravo (Kronuz)
	*Bits of code in pyScss come from various projects:*

	Compass:
	    (c) 2009 Christopher M. Eppstein
	    http://compass-style.org/
	Sass:
	    (c) 2006-2009 Hampton Catlin and Nathan Weizenbaum
	    http://sass-lang.com/
	xCSS:
	    (c) 2010 Anton Pawlik
	    http://xcss.antpaw.org/docs/
