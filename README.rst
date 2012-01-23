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

.. image:: http://pledgie.com/campaigns/16513.png?skin_name=chrome
   :alt: Click here to lend your support to pyScss and make a donation at pledgie.com!
   :target: http://pledgie.com/campaigns/16513

Support
========
pyScss is fully compatible with SCSS (Sass) 3.2 ...it has:

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

Requirements
============
	* python >= 2.5

Installation
============
pyScss should be installed using pip or setuptools::

	pip install pyScss

	easy_install pyScss

Usage
=====
Usage example::

	from scss import Scss
	css = Scss()
	css.compile("a { color: red + green; }")

Or compile from the command line::

	python scss.py < file.scss

Interactive mode::

	python scss.py --interactive

Examples
========
#. **Nested Rules**
	Example::

		@option compress: no;
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

		@option compress: no;
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

		@option compress: no;
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

		@option compress: no;
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

		@option compress: no;
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

#. **Interactive mode**
	Example::

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

Sass Sassy CSS
==============
pyScss is a Scss (Sass) implementation for Python.
Currently it implements @mixin, @include, @if, @else, @for, and @import... it
also implements many of the Sass functions including color functions like
hsla(), hsl(), darken(), lighten(), mix(), opacify(), transparentize(),
saturate(), desaturate(), etc.) as well as sprite-map(), sprite-file(),
image-width(), image-height() and the others.

In the file `scss.py`, by the top, you can configure the LOAD_PATHS to point to
your Sass frameworks path (I have `sass/frameworks/compass/*.scss` and
`sass/framework/blueprint/*.scss` files in my project directory:
`/usr/local/www/project/`, where `scss.py` lives, so it defaults to use the
`sass/framework/` path, relative to the `scss.py` file) or configure using the
command line `--load-path` option, see `python scss.py --help`.

I have succesfully compiled some Compass using `python scss.py < myfile.css` the
following `myfile.css`::

	@option compress: no;

	$blueprint-grid-columns : 24;
	$blueprint-grid-width   : 30px;
	$blueprint-grid-margin  : 10px;
	$font-color             : #333;

	@import "compass/reset";
	@import "compass/utilities";
	@import "blueprint";

	// Stuff goes here...

Django Example
==============
The following shows some code that can be used with django::

	.. code-block:: python
		
		import os
		import fnmatch
		
		import scss
		
		from django.conf import settings
		from django.utils.datastructures import SortedDict
		from django.contrib.staticfiles import finders
		
		
		def finder(glob):
		    """
		    Finds all files in the django finders for a given glob,
		    returns the file path, if available, and the django storage object.
		    storage objects must implement the File storage API:
		    https://docs.djangoproject.com/en/dev/ref/files/storage/
		    """
		    for finder in finders.get_finders():
		        for path, storage in finder.list([]):
		            if fnmatch.fnmatchcase(path, glob):
		                yield path, storage
		
		
		# STATIC_ROOT is where pyScss looks for images and static data.
		# STATIC_ROOT can be either a fully qualified path name or a "finder"
		# iterable function that receives a filename or glob and returns a tuple
		# of the file found and its file storage object for each matching file.
		# (https://docs.djangoproject.com/en/dev/ref/files/storage/)
		scss.STATIC_ROOT = finder
		scss.STATIC_URL = settings.STATIC_URL
		
		# ASSETS_ROOT is where the pyScss outputs the generated files such as spritemaps
		# and compile cache:
		scss.ASSETS_ROOT = os.path.join(settings.MEDIA_ROOT, 'assets/')
		scss.ASSETS_URL = settings.MEDIA_URL + 'assets/'
		
		# These are the paths pyScss will look ".scss" files on. This can be the path to
		# the compass framework or blueprint or compass-recepies, etc.
		scss.LOAD_PATHS = [
		    '/usr/local/www/sass/frameworks/',
		    '/Library/Ruby/Gems/1.8/gems/compass-0.11.5/frameworks/compass/stylesheets/',
		    '/Library/Ruby/Gems/1.8/gems/compass-0.11.5/frameworks/blueprint/stylesheets/',
		]
		
		# This creates the Scss object used to compile SCSS code. In this example,
		# _scss_vars will hold the context variables:
		_scss_vars = {}
		_scss = scss.Scss(
		    scss_vars=_scss_vars,
		    scss_opts={
		        'compress': True,
		        'debug_info': True,
		    }
		)
		
		# 1. Compile from a string:
		compiled_css_from_string = _scss.compile('@import "file2"; a {color: red + green; }')
		
		# 2. Compile from a file:
		compiled_css_from_file = _scss.compile(scss_file='file1.scss')
		
		# 3. Compile from a set of files (use SortedDict or collections.OrderedDict to
		# maintain the compile order):
		_scss._scss_files = SortedDict((
		    ('file2.scss', open('file2.scss').read()),
		    ('file3.scss', open('file3.scss').read()),
		    ('file4.scss', open('file4.scss').read()),
		))
		compiled_css_from_files = _scss.compile()


Bug tracker
===========
If you have any suggestions, bug reports or annoyances please report them to the
issue tracker at http://github.com/Kronuz/pyScss/issues


Changelog
=========

1.1.4 ???
	+ Added ``--debug-info`` command line option (for *FireSass* output).
	+ Added compass helper function ``reject()``.
	+ Added ``undefined`` keyword for undefined variables.

1.1.3 Jan 9, 2012
	+ Support for the new Sass 3.2.0 features (``@content`` and placeholder selectors)
	+ Fixed bug with line numbers throwing an exception.

1.1.2 Jan 3, 2012
	+ Regression bug fixed from 1.1.1

1.1.1 Jan 2, 2012
	+ Added optional C speedup module for an amazing boost in scanning speed!
	+ Added ``headings``, ``stylesheet-url``, ``font-url``, ``font-files``, ``inline-font-files`` and ``sprite-names``.

1.1.0 - Dec 22, 2011
	+ Added ``min()`` and ``max()`` for lists.
	+ Removed exception raise.

1.0.9 - Dec 22, 2011
	+ Optimizations in the scanner.
	+ Added ``background-noise()`` for compass-recipes support.
	+ ``enumerate()`` and ``range()`` can go backwards. Ex.: ``range(3, 0)`` goes from 3 to 0.
	+ Added line numbers and files for errors.
	+ Added support for *Firebug* with *FireSass*.
	+ ``nth(n)`` is round (returns the ``nth mod len`` item of the list).
	+ ``--watch`` added to the command line.
	+ Several bugs fixed.

1.0.8 - May 13, 2011
    + Changed source color (``$src-color``) default to black.
    + Moved the module filename to ``__init__.py`` and module renamed back to scss.


Contributing
============
Development of pyScss happens at github: https://github.com/Kronuz/pyScss


License
=======
MIT License. See *LICENSE* for details.
http://www.opensource.org/licenses/mit-license.php


Copyright
=========
Copyright (c) 2012 German M. Bravo (Kronuz)
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
