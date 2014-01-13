from scss.functions.library import FunctionLibrary
from scss.functions.compass.helpers import _font_url
from scss.functions.compass.images import _image_url


BOOTSTRAP_LIBRARY = FunctionLibrary()
register = BOOTSTRAP_LIBRARY.register


@register('twbs-font-path', 1)
def twbs_font_path(path):
    return _font_url(path, False, True, False)


@register('twbs-image-path', 1)
def twbs_image_path(path):
    return _image_url(path, False, True, None, None, False, None, None, None, None)
