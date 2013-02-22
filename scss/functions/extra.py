"""Functions new to the pyScss library."""

from __future__ import absolute_import

import base64
import hashlib
import logging
import os.path
import random

from scss import config
from scss.functions.library import FunctionLibrary
from scss.types import ColorValue, NumberValue, StringValue
from scss.util import escape, to_str

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image, ImageDraw
except ImportError:
    try:
        import Image, ImageDraw
    except:
        Image = None

log = logging.getLogger(__name__)

EXTRA_LIBRARY = FunctionLibrary()
register = EXTRA_LIBRARY.register

# ------------------------------------------------------------------------------
# Image stuff

@register('background-noise', 0)
@register('background-noise', 1)
@register('background-noise', 2)
@register('background-noise', 3)
@register('background-noise', 4)
def background_noise(intensity=None, opacity=None, size=None, monochrome=False, inline=False):
    if not Image:
        raise Exception("Images manipulation require PIL")

    intensity = intensity and NumberValue(intensity).value
    if not intensity or intensity < 0 or intensity > 1:
        intensity = 0.5

    opacity = opacity and NumberValue(opacity).value
    if not opacity or opacity < 0 or opacity > 1:
        opacity = 0.08

    size = size and int(NumberValue(size).value)
    if not size or size < 1 or size > 512:
        size = 200

    monochrome = bool(monochrome)

    new_image = Image.new(
        mode='RGBA',
        size=(size, size)
    )

    pixdata = new_image.load()
    for i in range(0, int(round(intensity * size ** 2))):
        x = random.randint(1, size)
        y = random.randint(1, size)
        r = random.randint(0, 255)
        a = int(round(random.randint(0, 255) * opacity))
        color = (r, r, r, a) if monochrome else (r, random.randint(0, 255), random.randint(0, 255), a)
        pixdata[x - 1, y - 1] = color

    if not inline:
        key = (intensity, opacity, size, monochrome)
        asset_file = 'noise_%s%sx%s+%s+%s' % ('mono_' if monochrome else '', size, size, to_str(intensity).replace('.', '_'), to_str(opacity).replace('.', '_'))
        asset_file = asset_file + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = asset_file + '.png'
        asset_path = os.path.join(config.ASSETS_ROOT, asset_file)
        try:
            new_image.save(asset_path)
        except IOError:
            log.exception("Error while saving image")
            inline = True  # Retry inline version
        url = '%s%s' % (config.ASSETS_URL, asset_file)
    if inline:
        output = StringIO()
        new_image.save(output, format='PNG')
        contents = output.getvalue()
        output.close()
        url = 'data:image/png;base64,' + base64.b64encode(contents)

    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


@register('grid-image', 4)
@register('grid-image', 5)
def _grid_image(left_gutter, width, right_gutter, height, columns=1, grid_color=None, baseline_color=None, background_color=None, inline=False):
    if not Image:
        raise Exception("Images manipulation require PIL")
    if grid_color == None:
        grid_color = (120, 170, 250, 15)
    else:
        c = ColorValue(grid_color).value
        grid_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    if baseline_color == None:
        baseline_color = (120, 170, 250, 30)
    else:
        c = ColorValue(baseline_color).value
        baseline_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    if background_color == None:
        background_color = (0, 0, 0, 0)
    else:
        c = ColorValue(background_color).value
        background_color = (c[0], c[1], c[2], int(c[3] * 255.0))
    _height = int(height) if height >= 1 else int(height * 1000.0)
    _width = int(width) if width >= 1 else int(width * 1000.0)
    _left_gutter = int(left_gutter) if left_gutter >= 1 else int(left_gutter * 1000.0)
    _right_gutter = int(right_gutter) if right_gutter >= 1 else int(right_gutter * 1000.0)
    if _height <= 0 or _width <= 0 or _left_gutter <= 0 or _right_gutter <= 0:
        raise ValueError
    _full_width = (_left_gutter + _width + _right_gutter)
    new_image = Image.new(
        mode='RGBA',
        size=(_full_width * int(columns), _height),
        color=background_color
    )
    draw = ImageDraw.Draw(new_image)
    for i in range(int(columns)):
        draw.rectangle((i * _full_width + _left_gutter, 0, i * _full_width + _left_gutter + _width - 1, _height - 1),  fill=grid_color)
    if _height > 1:
        draw.rectangle((0, _height - 1, _full_width * int(columns) - 1, _height - 1),  fill=baseline_color)
    if not inline:
        grid_name = 'grid_'
        if left_gutter:
            grid_name += str(int(left_gutter)) + '+'
        grid_name += str(int(width))
        if right_gutter:
            grid_name += '+' + str(int(right_gutter))
        if height and height > 1:
            grid_name += 'x' + str(int(height))
        key = (columns, grid_color, baseline_color, background_color)
        key = grid_name + '-' + base64.urlsafe_b64encode(hashlib.md5(repr(key)).digest()).rstrip('=').replace('-', '_')
        asset_file = key + '.png'
        asset_path = os.path.join(config.ASSETS_ROOT, asset_file)
        try:
            new_image.save(asset_path)
        except IOError:
            log.exception("Error while saving image")
            inline = True  # Retry inline version
        url = '%s%s' % (config.ASSETS_URL, asset_file)
    if inline:
        output = StringIO()
        new_image.save(output, format='PNG')
        contents = output.getvalue()
        output.close()
        url = 'data:image/png;base64,' + base64.b64encode(contents)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)


@register('image-color', 1)
@register('image-color', 2)
@register('image-color', 3)
def image_color(color, width=1, height=1):
    if not Image:
        raise Exception("Images manipulation require PIL")
    c = ColorValue(color).value
    w = int(NumberValue(width).value)
    h = int(NumberValue(height).value)
    if w <= 0 or h <= 0:
        raise ValueError
    new_image = Image.new(
        mode='RGB' if c[3] == 1 else 'RGBA',
        size=(w, h),
        color=(c[0], c[1], c[2], int(c[3] * 255.0))
    )
    output = StringIO()
    new_image.save(output, format='PNG')
    contents = output.getvalue()
    output.close()
    mime_type = 'image/png'
    url = 'data:' + mime_type + ';base64,' + base64.b64encode(contents)
    inline = 'url("%s")' % escape(url)
    return StringValue(inline)
