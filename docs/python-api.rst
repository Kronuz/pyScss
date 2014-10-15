Python API
==========

Legacy API
----------

.. warning::

    This API is still supported while the new API below is worked out, but it's
    slated for deprecation and eventual removal.  If you don't need any of the
    features not yet available with the new API, consider porting as soon as
    possible.


Compiling files
***************

Very basic usage is simple enough::

    from scss import Scss
    css = Scss()
    css.compile("a { color: red + green; }")


Configuration
*************

There are several configuration variables in the :py:mod:`scss.config` module
that you may wish to change.

``PROJECT_ROOT``: Root of your entire project.  Used only to construct defaults
for other variables.  Defaults to the root of the pyScss installation, which is
probably not what you want.

``LOAD_PATHS``: An iterable of paths to search when using``@import``.

``STATIC_ROOT``: Used for finding sprite files.  Defaults to
``$PROJECT_ROOT/static``.

``ASSETS_ROOT``: Generated sprites are saved here.  Defaults to
``$STATIC_ROOT/assets``.

``CACHE_ROOT``: Used for storing cached sprite information.  Defaults to
``ASSETS_ROOT``.

``STATIC_URL``: URL equivalent to ``STATIC_ROOT``.  Defaults to ``static/``.

``ASSETS_URL``: URL equivalent to ``ASSETS_ROOT``.  Defaults to ``static/assets/``.

``SPRTE_MAP_DIRECTION``: Direction in which to arrange sprites in a
spritesheet.  Defaults to ``vertical``; may be changed to ``horizontal``,
``diagonal``, or ``smart``.

``VERBOSITY``: Increase spew from the compiler.  Defaults to ``1``.

``DEBUG``: Set to true to make parse errors fatal.  Defaults to false.


Django example
**************

A rough example of using pyScss with Django::

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
    scss.config.STATIC_ROOT = finder
    scss.config.STATIC_URL = settings.STATIC_URL
    
    # ASSETS_ROOT is where the pyScss outputs the generated files such as spritemaps
    # and compile cache:
    scss.config.ASSETS_ROOT = os.path.join(settings.MEDIA_ROOT, 'assets/')
    scss.config.ASSETS_URL = settings.MEDIA_URL + 'assets/'
    
    # These are the paths pyScss will look ".scss" files on. This can be the path to
    # the compass framework or blueprint or compass-recepies, etc.
    scss.config.LOAD_PATHS = [
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

.. note::

    The API here is likely to be improved in 1.3, to avoid the need for calling
    underscored functions.


New API
-------

The simplest example::

    from scss.compiler import compile_string

    print(compile_string("a { color: red + green; }"))

:py:func:`scss.compiler.compile_string` is just a simple wrapper around the
:py:class:`scss.compiler.Compiler` class::

    from scss.compiler import Compiler

    compiler = Compiler()
    print(compiler.compile_string("a { color: red + green; }"))

The most common arguments passed to `Compiler` are:

**search_path**
    A list of paths to search for ``@import``\ s.  May be either strings or
    :py:class:`pathlib.Path` objects.


Extending pyScss
----------------

A significant advantage to using pyScss is that you can inject Python values
and code into the Sass compilation process.

Injecting values
****************

You can define Sass values by creating and populating a :class:`scss.namespace.Namespace`::

    from scss.namespace import Namespace
    from scss.types import String

    namespace = Namespace()
    namespace.set_variable('$base-url', String('http://localhost/'))
    compiler = Compiler(namespace=namespace)
    compiler.compile_string('div { background: url($base-url); }')

Now, ``$base-url`` will be available to the compiled Sass code, just like any
other variable.  Note that the value given must be one of the Sass types
defined in :py:mod:`scss.types`.

Injecting functions
*******************

You can inject functions the same way::

    def square(x):
        return x * x

    namespace.set_function('square', 1, square)

This creates a function ``square`` for use in your Sass source.  Optional
arguments, keyword arguments, and slurpy arguments are all supported
automatically.  The arguments are Sass types, and the return value must be one
as well.

The second argument is the arity — the number of required arguments, or None if
any number of arguments is allowed.  Sass functions can be overloaded by arity,
so this is required.  For functions with optional arguments, adding the same
function multiple times can be tedious and error-prone, so the ``declare``
decorator is also available::

    @namespace.declare
    def square(x):
        return x * x

This will inspect the arguments for you and register the function with all
arities it accepts.  The function name is determined from the Python name:
underscores become hyphens, and trailing underscores are removed.  If you'd
prefer to be more explicit, there's also a ``declare_alias``::

    @namespace.declare_alias('square')
    def square(x):
        return x * x


API reference
-------------

scss.compiler
*************

.. automodule:: scss.compiler
    :members:

scss.namespace
**************

.. automodule:: scss.namespace
    :members:

scss.extension
**************

.. automodule:: scss.extension
    :members:
