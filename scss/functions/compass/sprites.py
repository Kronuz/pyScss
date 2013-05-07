"""Functions used for generating CSS sprites.

These are ported from the Compass sprite library:
http://compass-style.org/reference/compass/utilities/sprites/
"""

from __future__ import absolute_import

import base64
import glob
import hashlib
import logging
import os.path
import tempfile
import time

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except:
        Image = None

from scss import config
from scss.functions.compass import _image_size_cache
from scss.functions.compass.layouts import PackedSpritesLayout, HorizontalSpritesLayout, VerticalSpritesLayout, DiagonalSpritesLayout
from scss.functions.library import FunctionLibrary
from scss.types import ColorValue, ListValue, NumberValue, QuotedStringValue, StringValue
from scss.util import escape

log = logging.getLogger(__name__)

MAX_SPRITE_MAPS = 4096
KEEP_SPRITE_MAPS = int(MAX_SPRITE_MAPS * 0.8)

COMPASS_SPRITES_LIBRARY = FunctionLibrary()
register = COMPASS_SPRITES_LIBRARY.register


# ------------------------------------------------------------------------------
# Compass-like functionality for sprites and images

sprite_maps = {}


@register('sprite-map', 1)
def sprite_map(g, **kwargs):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.
    """
    if not Image:
        raise Exception("Images manipulation require PIL")

    now_time = time.time()

    g = StringValue(g).value

    if g in sprite_maps:
        sprite_maps[glob]['*'] = now_time
    elif '..' not in g:  # Protect against going to prohibited places...
        if callable(config.STATIC_ROOT):
            glob_path = g
            rfiles = files = sorted(config.STATIC_ROOT(g))
        else:
            glob_path = os.path.join(config.STATIC_ROOT, g)
            files = glob.glob(glob_path)
            files = sorted((f, None) for f in files)
            rfiles = [(rf[len(config.STATIC_ROOT):], s) for rf, s in files]

        if not files:
            log.error("Nothing found at '%s'", glob_path)
            return StringValue(None)

        map_name = os.path.normpath(os.path.dirname(g)).replace('\\', '_').replace('/', '_')
        key = list(zip(*files)[0]) + [repr(kwargs), config.ASSETS_URL]
        key = map_name + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + '.png'
        ASSETS_ROOT = config.ASSETS_ROOT or os.path.join(config.STATIC_ROOT, 'assets')
        asset_path = os.path.join(ASSETS_ROOT, asset_file)
        cache_path = os.path.join(config.CACHE_ROOT or ASSETS_ROOT, asset_file + '.cache')

        try:
            save_time, asset, map, sizes = pickle.load(open(cache_path))
            sprite_maps[asset] = map
        except:
            save_time = 0
            map = None

        for file_, storage in files:
            if storage is not None:
                d_obj = storage.modified_time(file_)
                _time = time.mktime(d_obj.timetuple())
            else:
                _time = os.path.getmtime(file_)
            if save_time < _time:
                if _time > now_time:
                    log.warning("File '%s' has a date in the future (cache ignored)" % file_)
                map = None  # Invalidate cached sprite map
                break

        if map is None:
            direction = kwargs.get('direction', config.SPRTE_MAP_DIRECTION)
            repeat = StringValue(kwargs.get('repeat', 'no-repeat'))
            collapse_x = collapse_y = int(NumberValue(kwargs.get('collapse', 0)).value)
            if 'collapse_x' in kwargs:
                collapse_x = int(NumberValue(kwargs['collapse_x']).value)
            if 'collapse_y' in kwargs:
                collapse_y = int(NumberValue(kwargs['collapse_y']).value)

            position = NumberValue(kwargs.get('position', 0))
            if position.units.get('_') != '%' and position.value > 1:
                position = position.value / 100.0
            else:
                position = position.value
            if position < 0:
                position = 0.0
            elif position > 1:
                position = 1.0

            spacing = kwargs.get('spacing', 0)
            if isinstance(spacing, ListValue):
                spacing = [int(NumberValue(v).value) for n, v in spacing.items()]
            else:
                spacing = [int(NumberValue(spacing).value)]
            spacing = (spacing * 4)[:4]

            dst_colors = kwargs.get('dst_color')
            if isinstance(dst_colors, ListValue):
                dst_colors = [list(ColorValue(v).value[:3]) for n, v in dst_colors.items() if v]
            else:
                dst_colors = [list(ColorValue(dst_colors).value[:3])] if dst_colors else []

            src_colors = kwargs.get('src_color')
            if isinstance(src_colors, ListValue):
                src_colors = [tuple(ColorValue(v).value[:3]) if v else (0, 0, 0) for n, v in src_colors.items()]
            else:
                src_colors = [tuple(ColorValue(src_colors).value[:3]) if src_colors else (0, 0, 0)]

            len_colors = max(len(dst_colors), len(src_colors))
            dst_colors = (dst_colors * len_colors)[:len_colors]
            src_colors = (src_colors * len_colors)[:len_colors]

            def images(f=lambda x: x):
                for file_, storage in f(files):
                    if storage is not None:
                        _file = storage.open(file_)
                    else:
                        _file = file_
                    _image = Image.open(_file)
                    yield _image

            names = tuple(os.path.splitext(os.path.basename(file_))[0] for file_, storage in files)

            spacings = []

            for name in names:
                name = name.replace('-', '_')

                _spacing = kwargs.get(name + '_spacing')
                if _spacing is None:
                    _spacing = spacing
                else:
                    if isinstance(_spacing, ListValue):
                        _spacing = [int(NumberValue(v).value) for n, v in _spacing.items()]
                    else:
                        _spacing = [int(NumberValue(_spacing).value)]
                    _spacing = (_spacing * 4)[:4]
                spacings.append(_spacing)

            sizes = tuple((collapse_x or i.size[0], collapse_y or i.size[1]) for i in images())

            if direction == 'horizontal':
                layout = HorizontalSpritesLayout(sizes, spacings, position=position)
            elif direction == 'vertical':
                layout = VerticalSpritesLayout(sizes, spacings, position=position)
            elif direction == 'diagonal':
                layout = DiagonalSpritesLayout(sizes, spacings)
            elif direction == 'smart':
                layout = PackedSpritesLayout(sizes, spacings)
            else:
                raise Exception("Invalid direction %s" % direction)
            layout_positions = list(layout)

            new_image = Image.new(
                mode='RGBA',
                size=(layout.width, layout.height),
                color=(0, 0, 0, 0)
            )

            offsets_x = []
            offsets_y = []
            for i, image in enumerate(images()):
                x, y, width, height, cssx, cssy, cssw, cssh = layout_positions[i]
                iwidth, iheight = image.size

                if iwidth != width or iheight != height:
                    cy = 0
                    while cy < iheight:
                        cx = 0
                        while cx < iwidth:
                            cropped_image = image.crop((cx, cy, cx + width, cy + height))
                            new_image.paste(cropped_image, (x, y), cropped_image)
                            cx += width
                        cy += height
                else:
                    new_image.paste(image, (x, y))
                offsets_x.append(cssx)
                offsets_y.append(cssy)

            if dst_colors:
                useless = True
                pixdata = new_image.load()
                for _y in xrange(layout.height):
                    for _x in xrange(layout.width):
                        pixel = pixdata[_x, _y]
                        rgb = pixel[:3]
                        a = pixel[3]
                        for i, dst_color in enumerate(dst_colors):
                            if rgb == src_colors[i]:
                                if a:
                                    new_color = tuple([int(c) for c in dst_color] + [a])
                                    if pixel != new_color:
                                        pixdata[_x, _y] = new_color
                                        useless = False
                                break
                if useless:
                    log.warning("Useless use of dst_color in sprite map for files at '%s' (never used)" % glob_path)

            try:
                new_image.save(asset_path)
            except IOError:
                log.exception("Error while saving image")

            filetime = int(now_time)
            url = '%s%s?_=%s' % (config.ASSETS_URL, asset_file, filetime)
            asset = 'url("%s") %s' % (escape(url), repeat)

            # Add the new object:
            map = dict(zip(names, zip(sizes, rfiles, offsets_x, offsets_y)))
            map['*'] = now_time
            map['*f*'] = asset_file
            map['*k*'] = key
            map['*n*'] = map_name
            map['*t*'] = filetime

            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=ASSETS_ROOT)
            pickle.dump((now_time, asset, map, zip(files, sizes)), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, cache_path)

            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(sprite_maps) > MAX_SPRITE_MAPS:
                for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['*'], reverse=True)[KEEP_SPRITE_MAPS:]:
                    del sprite_maps[a]
                log.warning("Exceeded maximum number of sprite maps (%s)" % MAX_SPRITE_MAPS)
            sprite_maps[asset] = map
        for file_, size in sizes:
            _image_size_cache[file_] = size
    ret = StringValue(asset)
    return ret


@register('sprite-map-name', 1)
def sprite_map_name(map):
    """
    Returns the name of a sprite map The name is derived from the folder than
    contains the sprites.
    """
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        return StringValue(sprite_map['*n*'])
    return StringValue(None)


@register('sprite-file', 2)
def sprite_file(map, sprite):
    """
    Returns the relative path (from the images directory) to the original file
    used when construction the sprite. This is suitable for passing to the
    image_width and image_height helpers.
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        return QuotedStringValue(sprite[1][0])
    return StringValue(None)


@register('sprites', 1)
@register('sprite-names', 1)
def sprites(map):
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map, {})
    return ListValue(sorted(s for s in sprite_map if not s.startswith('*')))


@register('sprite', 2)
@register('sprite', 3)
@register('sprite', 4)
def sprite(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the image and background position for use in a single shorthand
    property
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        url = '%s%s?_=%s' % (config.ASSETS_URL, sprite_map['*f*'], sprite_map['*t*'])
        x = NumberValue(offset_x or 0, 'px')
        y = NumberValue(offset_y or 0, 'px')
        if not x or (x <= -1 or x >= 1) and x.unit != '%':
            x -= sprite[2]
        if not y or (y <= -1 or y >= 1) and y.unit != '%':
            y -= sprite[3]
        pos = "url(%s) %s %s" % (escape(url), x, y)
        return StringValue(pos)
    return StringValue('0 0')


@register('sprite-url', 1)
def sprite_url(map):
    """
    Returns a url to the sprite image.
    """
    map = StringValue(map).value
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        url = '%s%s?_=%s' % (config.ASSETS_URL, sprite_map['*f*'], sprite_map['*t*'])
        url = "url(%s)" % escape(url)
        return StringValue(url)
    return StringValue(None)


@register('sprite-position', 2)
@register('sprite-position', 3)
@register('sprite-position', 4)
def sprite_position(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the position for the original image in the sprite.
    This is suitable for use as a value to background-position.
    """
    map = StringValue(map).value
    sprite_name = StringValue(sprite).value
    sprite_map = sprite_maps.get(map)
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        x = None
        if offset_x is not None and not isinstance(offset_x, NumberValue):
            x = str(offset_x)
        if x not in ('left', 'right', 'center'):
            if x:
                offset_x = None
            x = NumberValue(offset_x or 0, 'px')
            if not x or (x <= -1 or x >= 1) and x.unit != '%':
                x -= sprite[2]
        y = None
        if offset_y is not None and not isinstance(offset_y, NumberValue):
            y = str(offset_y)
        if y not in ('top', 'bottom', 'center'):
            if y:
                offset_y = None
            y = NumberValue(offset_y or 0, 'px')
            if not y or (y <= -1 or y >= 1) and y.unit != '%':
                y -= sprite[3]
        pos = '%s %s' % (x, y)
        return StringValue(pos)
    return StringValue('0 0')
