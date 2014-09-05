"""Extension providing Compass support."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scss.extension import Extension
from scss.namespace import Namespace


# Global cache of image sizes, shared between sprites and images libraries.
# TODO put on the extension, somehow.
_image_size_cache = {}


class CompassExtension(Extension):
    name = 'compass'
    namespace = Namespace()


# Listing the child modules in __all__ will automatically import them, which in
# turn will import CompassExtension (without a circular import!) and add to its
# namespace
__all__ = ['CompassExtension', 'gradients', 'helpers', 'images', 'sprites']
