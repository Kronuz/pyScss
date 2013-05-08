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


def alpha_composite(im1, im2, offset=None, box=None, opacity=1):
    im1size = im1.size
    im2size = im2.size
    if offset is None:
        offset = (0, 0)
    if box is None:
        box = (0, 0) + im2size
    o1x, o1y = offset
    o2x, o2y, o2w, o2h = box
    width = o2w - o2x
    height = o2h - o2y
    im1_data = im1.load()
    im2_data = im2.load()
    for y in xrange(height):
        for x in xrange(width):
            pos1 = o1x + x, o1y + y
            if pos1[0] >= im1size[0] or pos1[1] >= im1size[1]:
                continue
            pos2 = o2x + x, o2y + y
            if pos2[0] >= im2size[0] or pos2[1] >= im2size[1]:
                continue
            dr, dg, db, da = im1_data[pos1]
            sr, sg, sb, sa = im2_data[pos2]
            da /= 255.0
            sa /= 255.0
            sa *= opacity
            ida = da * (1 - sa)
            oa = (sa + ida)
            if oa:
                pixel = (
                    int(round((sr * sa + dr * ida)) / oa),
                    int(round((sg * sa + dg * ida)) / oa),
                    int(round((sb * sa + db * ida)) / oa),
                    int(round(255 * oa))
                )
            else:
                pixel = (0, 0, 0, 0)
            im1_data[pos1] = pixel
    return im1


@register('sprite-map', 1)
def sprite_map(g, **kwargs):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.

    $direction - Sprite map layout. Can be `vertical` (default), `horizontal`, `diagonal` or `smart`.

    $position - For `horizontal` and `vertical` directions, the position of the sprite. (defaults to `0`)
    $<sprite>-position - Position of a given sprite.

    $margin, $spacing - Adds margins to sprites (top, right, bottom, left). (defaults to `0, 0, 0, 0`)
    $<sprite>-margin, $<sprite>-spacing - Margin for a given sprite.

    $dst-color - Together with `$src-color`, forms a map of source colors to be converted to destiny colors (same index of `$src-color` changed to `$dst-color`).
    $<sprite>-dst-color - Destiny colors for a given sprite. (defaults to `$dst-color`)

    $src-color - Selects source colors to be converted to the corresponding destiny colors. (defaults to `black`)
    $<sprite>-dst-color - Source colors for a given sprite. (defaults to `$src-color`)

    $collapse - Collapses every image in the sprite map to a fixed size (`x` and `y`).
    $collapse-x  - Collapses a size for `x`.
    $collapse-y  - Collapses a size for `y`.
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

        sprite_map = None
        if os.path.exists(asset_path):
            try:
                save_time, asset, sprite_map, sizes = pickle.load(open(cache_path))
                sprite_maps[asset] = sprite_map
            except:
                pass

            if sprite_map:
                for file_, storage in files:
                    if storage is not None:
                        d_obj = storage.modified_time(file_)
                        _time = time.mktime(d_obj.timetuple())
                    else:
                        _time = os.path.getmtime(file_)
                    if save_time < _time:
                        if _time > now_time:
                            log.warning("File '%s' has a date in the future (cache ignored)" % file_)
                        sprite_map = None  # Invalidate cached sprite map
                        break

        if sprite_map is None:
            direction = kwargs.get('direction', config.SPRTE_MAP_DIRECTION)
            repeat = StringValue(kwargs.get('repeat', 'no-repeat'))
            collapse = kwargs.get('collapse') or 0
            if isinstance(collapse, ListValue):
                collapse_x = int(NumberValue(collapse[0]).value)
                collapse_y = int(NumberValue(collapse[-1]).value)
            else:
                collapse_x = collapse_y = int(NumberValue(collapse).value)
            if 'collapse_x' in kwargs:
                collapse_x = int(NumberValue(kwargs['collapse_x']).value)
            if 'collapse_y' in kwargs:
                collapse_y = int(NumberValue(kwargs['collapse_y']).value)

            position = kwargs.get('position', 0)
            position = NumberValue(position)
            if position.units.get('_') != '%' and position.value > 1:
                position = position.value / 100.0
            else:
                position = position.value
            if position < 0:
                position = 0.0
            elif position > 1:
                position = 1.0

            margin = kwargs.get('margin', kwargs.get('spacing', 0))
            if isinstance(margin, ListValue):
                margin = [int(NumberValue(v).value) for n, v in margin.items()]
            else:
                margin = [int(NumberValue(margin).value)]
            margin = (margin * 4)[:4]

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

            has_dst_colors = False
            all_dst_colors = []
            all_src_colors = []
            all_positions = []
            all_margins = []

            for name in names:
                name = name.replace('-', '_')

                _position = kwargs.get(name + '_position')
                if _position is None:
                    _position = position
                else:
                    _position = NumberValue(_position)
                    if _position.units.get('_') != '%' and _position.value > 1:
                        _position = _position.value / 100.0
                    else:
                        _position = _position.value
                    if _position < 0:
                        _position = 0.0
                    elif _position > 1:
                        _position = 1.0
                all_positions.append(_position)

                _margin = kwargs.get(name + '_margin', kwargs.get(name + '_spacing'))
                if _margin is None:
                    _margin = margin
                else:
                    if isinstance(_margin, ListValue):
                        _margin = [int(NumberValue(v).value) for n, v in _margin.items()]
                    else:
                        _margin = [int(NumberValue(_margin).value)]
                    _margin = (_margin * 4)[:4]
                all_margins.append(_margin)

                _dst_colors = kwargs.get(name + '_dst_color')
                if _dst_colors is None:
                    _dst_colors = dst_colors
                    if dst_colors:
                        has_dst_colors = True
                else:
                    has_dst_colors = True
                    if isinstance(_dst_colors, ListValue):
                        _dst_colors = [list(ColorValue(v).value[:3]) for n, v in _dst_colors.items() if v]
                    else:
                        _dst_colors = [list(ColorValue(_dst_colors).value[:3])] if _dst_colors else []
                _src_colors = kwargs.get(name + '_src_color')
                if _src_colors is None:
                    _src_colors = src_colors
                else:
                    if isinstance(_src_colors, ListValue):
                        _src_colors = [tuple(ColorValue(v).value[:3]) if v else (0, 0, 0) for n, v in _src_colors.items()]
                    else:
                        _src_colors = [tuple(ColorValue(_src_colors).value[:3]) if _src_colors else (0, 0, 0)]
                _len_colors = max(len(_dst_colors), len(_src_colors))
                _dst_colors = (_dst_colors * _len_colors)[:_len_colors]
                _src_colors = (_src_colors * _len_colors)[:_len_colors]
                all_dst_colors.append(_dst_colors)
                all_src_colors.append(_src_colors)

            sizes = tuple((collapse_x or i.size[0], collapse_y or i.size[1]) for i in images())

            if direction == 'horizontal':
                layout = HorizontalSpritesLayout(sizes, all_margins, position=all_positions)
            elif direction == 'vertical':
                layout = VerticalSpritesLayout(sizes, all_margins, position=all_positions)
            elif direction == 'diagonal':
                layout = DiagonalSpritesLayout(sizes, all_margins)
            elif direction == 'smart':
                layout = PackedSpritesLayout(sizes, all_margins)
            else:
                raise Exception("Invalid direction %s" % direction)
            layout_positions = list(layout)

            new_image = Image.new(
                mode='RGBA',
                size=(layout.width, layout.height),
                color=(0, 0, 0, 0)
            )

            useless_dst_color = has_dst_colors

            offsets_x = []
            offsets_y = []
            for i, image in enumerate(images()):
                x, y, width, height, cssx, cssy, cssw, cssh = layout_positions[i]
                iwidth, iheight = image.size

                if has_dst_colors:
                    pixdata = image.load()
                    for _y in xrange(iheight):
                        for _x in xrange(iwidth):
                            pixel = pixdata[_x, _y]
                            a = pixel[3] if len(pixel) == 4 else 255
                            if a:
                                rgb = pixel[:3]
                                for j, dst_color in enumerate(all_dst_colors[i]):
                                    if rgb == all_src_colors[i][j]:
                                        new_color = tuple([int(c) for c in dst_color] + [a])
                                        if pixel != new_color:
                                            pixdata[_x, _y] = new_color
                                            useless_dst_color = False
                                        break

                if iwidth != width or iheight != height:
                    cy = 0
                    while cy < iheight:
                        cx = 0
                        while cx < iwidth:
                            new_image = alpha_composite(new_image, image, (x, y), (cx, cy, cx + width, cy + height))
                            cx += width
                        cy += height
                else:
                    new_image.paste(image, (x, y))
                offsets_x.append(cssx)
                offsets_y.append(cssy)

            if useless_dst_color:
                log.warning("Useless use of $dst-color in sprite map for files at '%s' (never used for)" % glob_path)

            try:
                new_image.save(asset_path)
            except IOError:
                log.exception("Error while saving image")

            filetime = int(now_time)
            url = '%s%s?_=%s' % (config.ASSETS_URL, asset_file, filetime)
            asset = 'url("%s") %s' % (escape(url), repeat)

            # Add the new object:
            sprite_map = dict(zip(names, zip(sizes, rfiles, offsets_x, offsets_y)))
            sprite_map['*'] = now_time
            sprite_map['*f*'] = asset_file
            sprite_map['*k*'] = key
            sprite_map['*n*'] = map_name
            sprite_map['*t*'] = filetime

            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=ASSETS_ROOT)
            pickle.dump((now_time, asset, sprite_map, zip(files, sizes)), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, cache_path)

            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(sprite_maps) > MAX_SPRITE_MAPS:
                for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['*'], reverse=True)[KEEP_SPRITE_MAPS:]:
                    del sprite_maps[a]
                log.warning("Exceeded maximum number of sprite maps (%s)" % MAX_SPRITE_MAPS)
            sprite_maps[asset] = sprite_map
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
