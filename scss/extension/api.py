"""Support for extending the Sass compiler."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class Extension(object):
    """An extension to the Sass compile process.  Subclass to add your own
    behavior.

    Methods are hooks, called by the compiler at certain points.  Each
    extension is considered in the order it's provided.
    """

    # TODO unsure how this could work given that we'd have to load modules for
    # it to be available
    name = None
    """A unique name for this extension, which will allow it to be referenced
    from the command line.
    """

    namespace = None
    """An optional :class:`scss.namespace.Namespace` that will be injected into
    the compiler.
    """

    def __init__(self):
        pass

    def handle_import(self, name, compilation, rule):
        """Attempt to resolve an import.  Called once for every Sass string
        listed in an ``@import`` statement.  Imports that Sass dictates should
        be converted to plain CSS imports do NOT trigger this hook.

        So this::

            @import url(foo), "bar", "baz";

        would call `handle_import` twice: once with "bar", once with "baz".

        Return a :class:`scss.source.SourceFile` if you want to handle the
        import, or None if you don't.  (This method returns None by default, so
        if you don't care about hooking imports, just don't implement it.)
        This method is tried on every registered `Extension` in order, until
        one of them returns successfully.

        A good example is the core Sass import machinery, which is implemented
        with this hook; see the source code of the core extension.
        """
        pass


class NamespaceAdapterExtension(Extension):
    """Trivial wrapper that adapts a bare :class:`scss.namespace.Namespace`
    into a full extension.
    """

    def __init__(self, namespace):
        self.namespace = namespace
