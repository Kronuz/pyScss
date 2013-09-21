Python API
==========

Compiling files
---------------

Very basic usage is simple enough::

    from scss import Scss
    css = Scss()
    css.compile("a { color: red + green; }")


Configuration
-------------

There are several configuration variables in the ``scss.config`` module that
you may wish to change.

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

.. warning::

    Configuration via monkeypatching is fraught with issues.  If you don't need
    the Compass sprite functionality, stick with passing ``search_paths`` to
    the ``Scss`` constructor, and don't touch these variables at all.

    The current plan is to introduce a new mechanism for Compass configuration
    in 1.3 with deprecation warnings, and remove ``scss.config`` entirely in
    2.0.


Django example
--------------

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


Extending pyScss
----------------

There is some support for adding custom functions from Python, but the API is
explicitly undocumented and subject to change.  Watch this space.

.. todo::

    Document the extension API once it's final.
