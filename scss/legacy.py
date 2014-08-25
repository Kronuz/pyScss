from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import six

from scss.compiler import Compiler
import scss.config as config
from scss.functions import ALL_BUILTINS_LIBRARY
from scss.expression import Calculator
from scss.namespace import Namespace
from scss.scss_meta import (
    BUILD_INFO, PROJECT, VERSION, REVISION, URL, AUTHOR, AUTHOR_EMAIL, LICENSE,
)
from scss.source import SourceFile
from scss.types import String


_default_scss_vars = {
    '$BUILD-INFO': String.unquoted(BUILD_INFO),
    '$PROJECT': String.unquoted(PROJECT),
    '$VERSION': String.unquoted(VERSION),
    '$REVISION': String.unquoted(REVISION),
    '$URL': String.unquoted(URL),
    '$AUTHOR': String.unquoted(AUTHOR),
    '$AUTHOR-EMAIL': String.unquoted(AUTHOR_EMAIL),
    '$LICENSE': String.unquoted(LICENSE),

    # unsafe chars will be hidden as vars
    '$--doubleslash': String.unquoted('//'),
    '$--bigcopen': String.unquoted('/*'),
    '$--bigcclose': String.unquoted('*/'),
    '$--doubledot': String.unquoted(':'),
    '$--semicolon': String.unquoted(';'),
    '$--curlybracketopen': String.unquoted('{'),
    '$--curlybracketclosed': String.unquoted('}'),
}


# TODO move this to a back-compat module so init is finally empty
# TODO using this should spew an actual deprecation warning
class Scss(object):
    """Original programmatic interface to the compiler.

    This class is now DEPRECATED.  See :mod:`scss.compiler` for the
    replacement.
    """
    def __init__(
            self, scss_vars=None, scss_opts=None, scss_files=None,
            super_selector='', live_errors=False,
            library=ALL_BUILTINS_LIBRARY, func_registry=None,
            search_paths=None):

        self.super_selector = super_selector

        self._scss_vars = {}
        if scss_vars:
            calculator = Calculator()
            for var_name, value in scss_vars.items():
                if isinstance(value, six.string_types):
                    scss_value = calculator.evaluate_expression(value)
                    if scss_value is None:
                        # TODO warning?
                        scss_value = String.unquoted(value)
                else:
                    scss_value = value
                self._scss_vars[var_name] = scss_value

        self._scss_opts = scss_opts or {}
        self._scss_files = scss_files
        # NOTE: func_registry is backwards-compatibility for only one user and
        # has never existed in a real release
        self._library = func_registry or library
        self._search_paths = search_paths

        # If true, swallow compile errors and embed them in the output instead
        self.live_errors = live_errors

    def compile(
            self, scss_string=None, scss_file=None, source_files=None,
            super_selector=None, filename=None, is_sass=None,
            line_numbers=True):
        """Compile Sass to CSS.  Returns a single CSS string.

        This method is DEPRECATED; see :mod:`scss.compiler` instead.
        """
        # Derive our root namespace
        self.scss_vars = _default_scss_vars.copy()
        if self._scss_vars is not None:
            self.scss_vars.update(self._scss_vars)

        root_namespace = Namespace(
            variables=self.scss_vars,
            functions=self._library,
        )

        # Figure out search paths.  Fall back from provided explicitly to
        # defined globally to just searching the current directory
        search_paths = ['.']
        if self._search_paths is not None:
            assert not isinstance(self._search_paths, six.string_types), \
                "`search_paths` should be an iterable, not a string"
            search_paths.extend(self._search_paths)
        else:
            if config.LOAD_PATHS:
                if isinstance(config.LOAD_PATHS, six.string_types):
                    # Back-compat: allow comma-delimited
                    search_paths.extend(config.LOAD_PATHS.split(','))
                else:
                    search_paths.extend(config.LOAD_PATHS)

            search_paths.extend(self._scss_opts.get('load_paths', []))

        # Normalize a few old styles of options
        output_style = self._scss_opts.get('style', config.STYLE)
        if output_style is True:
            output_style = 'compressed'
        elif output_style is False:
            output_style = 'legacy'

        # Build the compiler
        compiler = Compiler(
            namespace=root_namespace,
            search_path=search_paths,
            live_errors=self.live_errors,
            generate_source_map=self._scss_opts.get('debug_info', False),
            output_style=output_style,
            warn_unused_imports=self._scss_opts.get('warn_unused', False),
            super_selector=super_selector or self.super_selector,
        )
        # Gonna add the source files manually
        compilation = compiler.make_compilation()

        # Inject the files we know about
        # TODO how does this work with the expectation of absoluteness
        if source_files is not None:
            for source in source_files:
                compilation.add_source(source)
        elif scss_string is not None:
            source = SourceFile.from_string(
                scss_string,
                path=filename,
                is_sass=is_sass,
            )
            compilation.add_source(source)
        elif scss_file is not None:
            source = SourceFile.from_filename(
                scss_file,
                path=filename,
                is_sass=is_sass,
            )
            compilation.add_source(source)

        # Plus the ones from the constructor
        if self._scss_files:
            for name, contents in list(self._scss_files.items()):
                source = SourceFile.from_string(contents, path=name)
                compilation.add_source(source)

        return compiler.call_and_catch_errors(compilation.run)

    # Old, old alias
    Compilation = compile

    def get_scss_constants(self):
        scss_vars = self.root_namespace.variables
        return dict(
            (k, v) for k, v in scss_vars.items()
            if k and (not k.startswith('$') or k[1].isupper())
        )

    def get_scss_vars(self):
        scss_vars = self.root_namespace.variables
        return dict(
            (k, v) for k, v in scss_vars.items()
            if k and not (not k.startswith('$') and k[1].isupper())
        )
