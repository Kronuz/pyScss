"""Extension providing Compass support."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scss.extension import Extension
from scss.namespace import Namespace


# Global cache of image sizes, shared between sprites and images libraries.
# TODO put on the extension, somehow.
_image_size_cache = {}


# Import all our children to register their functions
from .gradients import gradients_namespace
from .helpers import helpers_namespace
from .images import images_namespace
from .sprites import sprites_namespace


class CompassExtension(Extension):
    name = 'compass'
    namespace = Namespace.derive_from(
        gradients_namespace,
        helpers_namespace,
        images_namespace,
        sprites_namespace,
    )


__all__ = ['CompassExtension']
