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

    def before_import(self):
        pass


class NamespaceAdapterExtension(Extension):
    """Trivial wrapper that adapts a bare :class:`scss.namespace.Namespace`
    into a full extension.
    """

    def __init__(self, namespace):
        self.namespace = namespace
