"""
Functions used for generating custom fonts from SVG files.

"""
from __future__ import absolute_import
from __future__ import unicode_literals

import errno
import glob
import logging
import os
import time
import tempfile
import subprocess
import warnings

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import fontforge
except:
    fontforge = None

from scss import config
from scss.functions.library import FunctionLibrary
from scss.types import String, Boolean, List
from scss.util import getmtime, escape, make_data_url, make_filename_hash

log = logging.getLogger(__name__)

TTFAUTOHINT_EXECUTABLE = 'ttfautohint'
TTF2EOT_EXECUTABLE = 'ttf2eot'

MAX_FONT_SHEETS = 4096
KEEP_FONT_SHEETS = int(MAX_FONT_SHEETS * 0.8)

FONTS_LIBRARY = FunctionLibrary()
register = FONTS_LIBRARY.register

FONT_TYPES = ('eot', 'woff', 'ttf', 'svg')  # eot should be first for IE support

FONT_MIME_TYPES = {
    'ttf': 'application/x-font-ttf',
    'svg': 'image/svg+xml',
    'woff': 'application/x-font-woff',
    'eot': 'application/vnd.ms-fontobject',
}

FONT_FORMATS = {
    'ttf': "format('truetype')",
    'svg': "format('svg')",
    'woff': "format('woff')",
    'eot': "format('embedded-opentype')",
}

# Offset to work around Chrome Windows bug
GLYPH_START = 0xf100

font_sheets = {}
_font_sheet_cache = {}


def ttfautohint(ttf):
    try:
        proc = subprocess.Popen(
            [TTFAUTOHINT_EXECUTABLE, '--hinting-limit=200', '--hinting-range-max=50', '--symbol'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    except OSError as e:
        if e.errno in (errno.EACCES, errno.ENOENT):
            warnings.warn('Could not autohint ttf font: The executable %s could not be run: %s' % (TTFAUTOHINT_EXECUTABLE, e))
            return None
        else:
            raise e
    output, output_err = proc.communicate(ttf)
    if proc.returncode != 0:
        warnings.warn("Could not autohint ttf font: Unknown error!")
        return None
    return output


def ttf2eot(ttf):
    try:
        proc = subprocess.Popen(
            [TTF2EOT_EXECUTABLE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    except OSError as e:
        if e.errno in (errno.EACCES, errno.ENOENT):
            warnings.warn('Could not generate eot font: The executable %s could not be run: %s' % (TTF2EOT_EXECUTABLE, e))
            return None
        else:
            raise e
    output, output_err = proc.communicate(ttf)
    if proc.returncode != 0:
        warnings.warn("Could not generate eot font: Unknown error!")
        return None
    return output


@register('font-sheet')
def font_sheet(g, **kwargs):
    if not fontforge:
        raise Exception("Fonts manipulation require fontforge")

    now_time = time.time()

    g = String(g, quotes=None).value

    if g in font_sheets:
        font_sheets[glob]['*'] = now_time
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
            return String.unquoted('')

        glyph_name = os.path.basename(os.path.dirname(g))
        key = [f for (f, s) in files] + [repr(kwargs), config.ASSETS_URL]
        key = glyph_name + '-' + make_filename_hash(key)
        asset_files = {
            'eot': key + '.eot',
            'woff': key + '.woff',
            'ttf': key + '.ttf',
            'svg': key + '.svg',
        }
        ASSETS_ROOT = config.ASSETS_ROOT or os.path.join(config.STATIC_ROOT, 'assets')
        asset_paths = dict((type_, os.path.join(ASSETS_ROOT, asset_file)) for type_, asset_file in asset_files.items())
        cache_path = os.path.join(config.CACHE_ROOT or ASSETS_ROOT, key + '.cache')

        inline = Boolean(kwargs.get('inline', False))

        font_sheet = None
        asset = None
        file_assets = {}
        inline_assets = {}
        if all(os.path.exists(asset_path) for asset_path in asset_paths.values()) or inline:
            try:
                save_time, file_assets, inline_assets, font_sheet, codepoints = pickle.load(open(cache_path))
                if file_assets:
                    file_asset = List([file_asset for file_asset in file_assets.values()], separator=",")
                    font_sheets[file_asset.render()] = font_sheet
                if inline_assets:
                    inline_asset = List([inline_asset for inline_asset in inline_assets.values()], separator=",")
                    font_sheets[inline_asset.render()] = font_sheet
                if inline:
                    asset = inline_asset
                else:
                    asset = file_asset
            except:
                pass

            if font_sheet:
                for file_, storage in files:
                    _time = getmtime(file_, storage)
                    if save_time < _time:
                        if _time > now_time:
                            log.warning("File '%s' has a date in the future (cache ignored)" % file_)
                        font_sheet = None  # Invalidate cached custom font
                        break

        if font_sheet is None or asset is None:
            cache_buster = Boolean(kwargs.get('cache_buster', True))
            autowidth = Boolean(kwargs.get('autowidth', True))
            autohint = Boolean(kwargs.get('autohint', True))

            font = fontforge.font()
            font.encoding = 'UnicodeFull'
            font.design_size = 16
            font.em = 512
            font.ascent = 448
            font.descent = 64
            font.fontname = glyph_name
            font.familyname = glyph_name
            font.fullname = glyph_name
            if autowidth:
                font.autoWidth(0, 0, 512)
            if autohint:
                font.autoHint()

            def glyphs(f=lambda x: x):
                for file_, storage in f(files):
                    if storage is not None:
                        _file = storage.open(file_)
                    else:
                        _file = open(file_)
                    svgtext = _file.read()
                    svgtext = svgtext.replace('<switch>', '')
                    svgtext = svgtext.replace('</switch>', '')
                    svgtext = svgtext.replace('<svg>', '<svg xmlns="http://www.w3.org/2000/svg">')
                    _glyph = tempfile.NamedTemporaryFile(delete=False, suffix=".svg")
                    _glyph.file.write(svgtext)
                    _glyph.file.close()
                    yield _glyph.name

            names = tuple(os.path.splitext(os.path.basename(file_))[0] for file_, storage in files)

            codepoints = []
            for i, glyph_filename in enumerate(glyphs()):
                codepoint = i + GLYPH_START
                codepoints.append(codepoint)
                glyph = font.createChar(codepoint, names[i])
                glyph.importOutlines(glyph_filename)
                os.unlink(glyph_filename)
                if autowidth:
                    glyph.left_side_bearing = glyph.right_side_bearing = 0
                    glyph.round()
                else:
                    glyph.width = 512

            filetime = int(now_time)

            # Generate font files
            if not inline:
                urls = {}
                for type_ in reversed(FONT_TYPES):
                    asset_path = asset_paths[type_]
                    try:
                        if type_ == 'eot':
                            ttf_path = asset_paths['ttf']
                            with open(ttf_path) as ttf_fh, open(asset_path, 'wb') as asset_fh:
                                contents = ttf2eot(ttf_fh.read())
                                if contents is None:
                                    continue
                                asset_fh.write(contents)
                        else:
                            font.generate(asset_path)
                            if type_ == 'ttf':
                                contents = None
                                with open(asset_path) as asset_fh:
                                    contents = ttfautohint(asset_fh.read())
                                if contents is not None:
                                    with open(asset_path, 'wb') as asset_fh:
                                        asset_fh.write(contents)
                        asset_file = asset_files[type_]
                        url = '%s%s' % (config.ASSETS_URL, asset_file)
                        params = []
                        if type_ == FONT_TYPES[0]:
                            params.append('#iefix')
                        if cache_buster:
                            params.append('v=%s' % filetime)
                        if type_ == 'svg':
                            params.append('#' + glyph_name)
                        if params:
                            url += '?' + '&'.join(params)
                        urls[type_] = url
                    except IOError:
                        inline = False

            if inline:
                urls = {}
                for type_ in reversed(FONT_TYPES):
                    contents = None
                    if type_ == 'eot':
                        ttf_path = asset_paths['ttf']
                        with open(ttf_path) as ttf_fh:
                            contents = ttf2eot(ttf_fh.read())
                            if contents is None:
                                continue
                    else:
                        _tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.' + type_)
                        _tmp.file.close()
                        font.generate(_tmp.name)
                        with open(_tmp.name) as asset_fh:
                            if type_ == 'ttf':
                                _contents = asset_fh.read()
                                contents = ttfautohint(_contents)
                            if contents is None:
                                contents = _contents
                    os.unlink(_tmp.name)
                    mime_type = FONT_MIME_TYPES[type_]
                    url = make_data_url(mime_type, contents)
                    urls[type_] = url

            assets = {}
            for type_, url in urls.items():
                format_ = FONT_FORMATS[type_]
                url = "url('%s')" % escape(url)
                if inline:
                    assets[type_] = inline_assets[type_] = List([String.unquoted(url), String.unquoted(format_)])
                else:
                    assets[type_] = file_assets[type_] = List([String.unquoted(url), String.unquoted(format_)])
            asset = List([assets[type_] for type_ in FONT_TYPES], separator=",")

            # Add the new object:
            font_sheet = dict(zip(names, zip(rfiles, codepoints)))
            font_sheet['*'] = now_time
            font_sheet['*f*'] = asset_files
            font_sheet['*k*'] = key
            font_sheet['*n*'] = glyph_name
            font_sheet['*t*'] = filetime

            codepoints = zip(files, codepoints)
            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=ASSETS_ROOT)
            pickle.dump((now_time, file_assets, inline_assets, font_sheet, codepoints), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, cache_path)

            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(font_sheets) > MAX_FONT_SHEETS:
                for a in sorted(font_sheets, key=lambda a: font_sheets[a]['*'], reverse=True)[KEEP_FONT_SHEETS:]:
                    del font_sheets[a]
                log.warning("Exceeded maximum number of font sheets (%s)" % MAX_FONT_SHEETS)
            font_sheets[asset.render()] = font_sheet
        for file_, codepoint in codepoints:
            _font_sheet_cache[file_] = codepoint
    # TODO this sometimes returns an empty list, or is never assigned to
    return asset


@register('glyphs', 1)
@register('glyph-names', 1)
def glyphs(sheet, remove_suffix=False):
    sheet = sheet.render()
    font_sheet = font_sheets.get(sheet, {})
    return List([String.unquoted(f) for f in sorted(set(f.rsplit('-', 1)[0] if remove_suffix else f for f in font_sheet if not f.startswith('*')))])


@register('glyph-classes', 1)
def glyph_classes(sheet):
    return glyphs(sheet, True)


@register('font-url', 2)
@register('font-url', 3)
def font_url(sheet, type_, only_path=False, cache_buster=True):
    font_sheet = font_sheets.get(sheet.render())
    type_ = String.unquoted(type_).render()
    if font_sheet:
        asset_files = font_sheet['*f*']
        asset_file = asset_files.get(type_)
        if asset_file:
            url = '%s%s' % (config.ASSETS_URL, asset_file)
            params = []
            # if type_ == 'eot':
            #     params.append('#iefix')
            if cache_buster:
                params.append('v=%s' % font_sheet['*t*'])
            if type_ == 'svg':
                params.append('#' + font_sheet['*n*'])
            if params:
                url += '?' + '&'.join(params)
            if not only_path:
                url = "url('%s')" % escape(url)
            return String.unquoted(url)
    return String.unquoted('')


@register('font-format', 3)
def font_format(type_):
    type_ = type_.render()
    if type_ in FONT_FORMATS:
            return String.unquoted(FONT_FORMATS[type_])
    return String.unquoted('')


@register('has-glyph', 2)
def has_glyph(sheet, glyph):
    sheet = sheet.render()
    font_sheet = font_sheets.get(sheet)
    glyph_name = String.unquoted(glyph).value
    glyph = font_sheet and font_sheet.get(glyph_name)
    if not font_sheet:
        log.error("No font sheet found: %s", sheet, extra={'stack': True})
    return Boolean(bool(glyph))


@register('glyph-code', 2)
def glyph_code(sheet, glyph):
    sheet = sheet.render()
    font_sheet = font_sheets.get(sheet)
    glyph_name = String.unquoted(glyph).value
    glyph = font_sheet and font_sheet.get(glyph_name)
    if not font_sheet:
        log.error("No font sheet found: %s", sheet, extra={'stack': True})
    elif not glyph:
        log.error("No glyph found: %s in %s", glyph_name, font_sheet['*n*'], extra={'stack': True})
    return String('\\%x' % glyph[1])
