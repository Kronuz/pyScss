from __future__ import absolute_import

from scss.functions.library import FunctionLibrary

from scss.functions.compass.configuration import ns
from scss.functions.compass.sprites import COMPASS_SPRITES_LIBRARY
from scss.functions.compass.gradients import COMPASS_GRADIENTS_LIBRARY
from scss.functions.compass.helpers import COMPASS_HELPERS_LIBRARY
from scss.functions.compass.images import COMPASS_IMAGES_LIBRARY


COMPASS_LIBRARY = FunctionLibrary()
COMPASS_LIBRARY.inherit(
    COMPASS_GRADIENTS_LIBRARY,
    COMPASS_HELPERS_LIBRARY,
    COMPASS_IMAGES_LIBRARY,
    COMPASS_SPRITES_LIBRARY,
    ns,
)
