xCSS for Python
===============
:Authors:
    German M. Bravo (Kronuz) <german.mb@gmail.com>
    Based on some code from the original xCSS project by Anton Pawlik
    http://xcss.antpaw.org/about

About
=====
xCSS for Python is a superset of CSS that is more powerful, elegant and easier
to maintain than plain-vanilla CSS. The library works as a CSS source code
preprocesor which allows you to use variables, nested rules, mixins, and have
inheritance of rules, all with a CSS-compatible syntax which the preprocessor
then compiles to standard CSS.

xCSS, as an extension of CSS, helps keep large stylesheets well-organized. It
borrows concepts and functionality from projects such as OOCSS and other similar
frameworks like as Sass (Sassy CSS). It's build on top of the original PHP xCSS
codebase structure but it's been completely rewritten and many bugs have been
fixed. It now also implements much of the Sass functionality and even compiles
some Compass (`http://compass-style.org/`)

Usage
=====
    Usage example::

	from xcss import xCSS
	css = xCSS()
	css.compile("a { color: red + green; }")

    Or compile from the command line::

	python xcss.py < file.css

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
	$icons: sprite-map("images/sociable/*.png"); // contains icons/new.png among others.
	
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

Sass Sassy CSS
==============
xCSS is a Sass (Scss) implementation for Python.
Currently it implements @mixin, @include, @if, @else, @for, and @import... it
also implements many of the Sass functions including colors function like
hsla(), hsl(), darken(), lighten(), mix(), opacify(), transparentize(),
saturate(), desaturate(), etc.) as well as sprite-map(), sprite-file(),
image-width(), image-height() and the others.

In the file `xcss.py`, by the top, configure the LOAD_PATHS to point to your
Compass framework path (I have `frameworks/compass/*.scss` and
`framework/blueprint/*.scss` files in my project directory:
`/usr/local/www/project/`, so I have that set for that path by default)

I have succesfully compiled some Compass using `python xcss.py < myfile.css` the
following `myfile.css`::

	@options compress: no;
	
	$blueprint-grid-columns : 24;
	$blueprint-grid-width   : 30px;
	$blueprint-grid-margin  : 10px;
	$font-color             : #333;
	
	@import "compass/reset";
	@import "compass/utilities";
	@import "blueprint";
	
	// Stuff goes here...
    
Installation Notes
==================
It requires the Pyparsing module (a single pure python file) from:
http://pyparsing.wikispaces.com/

License
=======
MIT License. See *LICENSE* for details.
http://www.opensource.org/licenses/mit-license.php
