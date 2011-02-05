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
frameworks like as Sass. It's build on top of the original PHP xCSS codebase
structure but it's been completely rewritten and many bugs have been fixed.

Usage
=====
# **Nested Rules**
    Example::

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

# **Variables**
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

    ...produces::

	#navbar {
		border-bottom-color: #ce4dd6;
		border-bottom-style: solid;
	}

# **Mixins**
    Example::

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

# **Extend** (using `@extend`)
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

Usage
=====
   Usage example::

	from xcss import xCSS
	css = xCSS()
	css.compile("a { color: red + green; }")

Installation Notes
==================
It requires the Pyparsing module from:
http://pyparsing.wikispaces.com/

License
=======
MIT License. See *LICENSE* for details.
http://www.opensource.org/licenses/mit-license.php
