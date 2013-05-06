"""Functions used for generating CSS sprites.

These are ported from the Compass sprite library:
http://compass-style.org/reference/compass/utilities/sprites/
"""

from __future__ import absolute_import

import base64
import datetime
import glob
import hashlib
import logging
import os.path
import pickle
import tempfile
import time

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except:
        Image = None

from scss import config
from scss.cssdefs import _units_weights
from scss.functions.compass import _image_size_cache
from scss.functions.library import FunctionLibrary
from scss.types import ColorValue, ListValue, NumberValue, QuotedStringValue, StringValue
from scss.util import escape

log = logging.getLogger(__name__)

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
    g = StringValue(g).value

    if not Image:
        raise Exception("Images manipulation require PIL")

    if g in sprite_maps:
        sprite_maps[glob]['*'] = datetime.datetime.now()
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
        asset_path = os.path.join(config.ASSETS_ROOT, asset_file)

        times = {}
        max_time = 0

        try:
            max_time, asset, map, sizes = pickle.load(open(asset_path + '.cache'))
            sprite_maps[asset] = map
        except:
            map = None

        for file_, storage in files:
            if storage is not None:
                d_obj = storage.modified_time(file_)
                _time = time.mktime(d_obj.timetuple())
            else:
                _time = os.path.getmtime(file_)
            times[file_] = _time
            if max_time < _time:
                max_time = _time
                map = None  # Invalidate cached sprite map
                break

        if map is None:
            direction = kwargs.get('direction', 'vertical')
            repeat = StringValue(kwargs.get('repeat', 'no-repeat'))
            position = NumberValue(kwargs.get('position', 0))
            collapse_x = NumberValue(kwargs.get('collapse_x', 0))
            collapse_y = NumberValue(kwargs.get('collapse_y', 0))
            if position and position > -1 and position < 1:
                position.units = {'%': _units_weights.get('%', 1), '_': '%'}

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

            spacing = kwargs.get('spacing', 0)
            if isinstance(spacing, ListValue):
                spacing = [int(NumberValue(v).value) for n, v in spacing.items()]
            else:
                spacing = [int(NumberValue(spacing).value)]
            spacing = (spacing * 4)[:4]

            def images():
                for file_, storage in files:
                    if storage is not None:
                        _file = storage.open(file_)
                    else:
                        _file = file_
                    _image = Image.open(_file)
                    try:
                        _time = times[file_]
                    except KeyError:
                        if storage is not None:
                            d_obj = storage.modified_time(file_)
                            _time = time.mktime(d_obj.timetuple())
                        else:
                            _time = os.path.getmtime(file_)
                    times[file_] = _time
                    yield _time, _image

            names = tuple(os.path.splitext(os.path.basename(file_))[0] for file_, storage in files)
            positions = []
            spacings = []
            tot_spacings = []

            for name in names:
                name = name.replace('-', '_')
                _position = kwargs.get(name + '_position')
                if _position is None:
                    _position = position
                else:
                    _position = NumberValue(_position)
                    if _position and _position > -1 and _position < 1:
                        _position.units = {'%': _units_weights.get('%', 1), '_': '%'}
                positions.append(_position)
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
                if _position and _position.unit != '%':
                    if direction == 'vertical':
                        if _position > 0:
                            tot_spacings.append((_spacing[0], _spacing[1], _spacing[2], _spacing[3] + _position))
                    elif direction == 'horizontal':
                        if _position > 0:
                            tot_spacings.append((_spacing[0] + _position, _spacing[1], _spacing[2], _spacing[3]))
                    elif direction == 'diagonal':
                        if _position > 0:
                            tot_spacings.append((_spacing[0] + _position, _spacing[1], _spacing[2], _spacing[3] + _position))
                else:
                    tot_spacings.append(_spacing)

            sizes = tuple((collapse_x or i.size[0], collapse_y or i.size[1]) for t, i in images())

            _spacings = zip(*tot_spacings)
            if direction == 'vertical':
                width = max(zip(*sizes)[0]) + max(_spacings[1]) + max(_spacings[3])
                height = sum(zip(*sizes)[1]) + sum(_spacings[0]) + sum(_spacings[2])
            elif direction == 'horizontal':
                width = sum(zip(*sizes)[0]) + sum(_spacings[1]) + sum(_spacings[3])
                height = max(zip(*sizes)[1]) + max(_spacings[0]) + max(_spacings[2])
            elif direction == 'diagonal':
                width = sum(zip(*sizes)[0]) + sum(_spacings[1]) + sum(_spacings[3])
                height = sum(zip(*sizes)[1]) + sum(_spacings[0]) + sum(_spacings[2])
            else:
                raise NotImplementedError("Direction not implemented!")

            new_image = Image.new(
                mode='RGBA',
                size=(width, height),
                color=(0, 0, 0, 0)
            )

            offsets_x = []
            offsets_y = []
            offset_x = 0
            offset_y = 0
            for i, (im_time, image) in enumerate(images()):
                if max_time < im_time:
                    max_time = im_time
                spacing = spacings[i]
                position = positions[i]
                iwidth, iheight = image.size
                width, height = sizes[i]
                if direction == 'vertical':
                    if position and position.unit == '%':
                        x = width * position.value - (spacing[3] + height + spacing[1])
                    elif position.value < 0:
                        x = width + position.value - (spacing[3] + height + spacing[1])
                    else:
                        x = position.value
                    offset_y += spacing[0]
                    for i, dst_color in enumerate(dst_colors):
                        src_color = src_colors[i]
                        pixdata = image.load()
                        for _y in xrange(image.size[1]):
                            for _x in xrange(image.size[0]):
                                pixel = pixdata[_x, _y]
                                if pixel[:3] == src_color:
                                    pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                    if iwidth != width or iheight != height:
                        cy = 0
                        while cy < iheight:
                            cx = 0
                            while cx < iwidth:
                                cropped_image = image.crop((cx, cy, cx + width, cy + height))
                                new_image.paste(cropped_image, (int(x + spacing[3]), offset_y), cropped_image)
                                cx += width
                            cy += height
                    else:
                        new_image.paste(image, (int(x + spacing[3]), offset_y))
                    offsets_x.append(x)
                    offsets_y.append(offset_y - spacing[0])
                    offset_y += height + spacing[2]
                elif direction == 'horizontal':
                    if position and position.unit == '%':
                        y = height * position.value - (spacing[0] + height + spacing[2])
                    elif position.value < 0:
                        y = height + position.value - (spacing[0] + height + spacing[2])
                    else:
                        y = position.value
                    offset_x += spacing[3]
                    for i, dst_color in enumerate(dst_colors):
                        src_color = src_colors[i]
                        pixdata = image.load()
                        for _y in xrange(image.size[1]):
                            for _x in xrange(image.size[0]):
                                pixel = pixdata[_x, _y]
                                if pixel[:3] == src_color:
                                    pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                    if iwidth != width or iheight != height:
                        cy = 0
                        while cy < iheight:
                            cx = 0
                            while cx < iwidth:
                                cropped_image = image.crop((cx, cy, cx + width, cy + height))
                                new_image.paste(cropped_image, (offset_x, int(y + spacing[0])), cropped_image)
                                cx += width
                            cy += height
                    else:
                        new_image.paste(image, (offset_x, int(y + spacing[0])))
                    offsets_x.append(offset_x - spacing[3])
                    offsets_y.append(y)
                    offset_x += width + spacing[1]
                elif direction == 'diagonal':
                    offset_x += spacing[3]
                    offset_y += spacing[0]
                    for i, dst_color in enumerate(dst_colors):
                        src_color = src_colors[i]
                        pixdata = image.load()
                        for _y in xrange(image.size[1]):
                            for _x in xrange(image.size[0]):
                                pixel = pixdata[_x, _y]
                                if pixel[:3] == src_color:
                                    pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                    if iwidth != width or iheight != height:
                        cy = 0
                        while cy < iheight:
                            cx = 0
                            while cx < iwidth:
                                cropped_image = image.crop((cx, cy, cx + width, cy + height))
                                new_image.paste(cropped_image, (offset_x, offset_y), cropped_image)
                                cx += width
                            cy += height
                    else:
                        new_image.paste(image, (offset_x, offset_y))
                    offsets_x.append(offset_x - spacing[3])
                    offsets_y.append(offset_y - spacing[0])
                    offset_x += width + spacing[1]
                    offset_y += height + spacing[2]
            try:
                new_image.save(asset_path)
            except IOError:
                log.exception("Error while saving image")
            filetime = int(time.mktime(datetime.datetime.now().timetuple()))

            url = '%s%s?_=%s' % (config.ASSETS_URL, asset_file, filetime)
            asset = 'url("%s") %s' % (escape(url), repeat)
            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(sprite_maps) > 1000:
                for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['*'], reverse=True)[500:]:
                    del sprite_maps[a]
            # Add the new object:
            map = dict(zip(names, zip(sizes, rfiles, offsets_x, offsets_y)))
            map['*'] = datetime.datetime.now()
            map['*f*'] = asset_file
            map['*k*'] = key
            map['*n*'] = map_name
            map['*t*'] = filetime

            tmp_dir = config.ASSETS_ROOT
            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=tmp_dir)
            pickle.dump((max_time, asset, map, zip(files, sizes)), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, asset_path + '.cache')

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
