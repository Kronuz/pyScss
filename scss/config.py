################################################################################
# Configuration:

import os
PROJECT_ROOT = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
# Sass @import load_paths:
LOAD_PATHS = os.path.join(PROJECT_ROOT, 'sass/frameworks')
# Assets path, where new sprite files are created:
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
# Assets path, where new sprite files are created (defaults to STATIC_ROOT + '/assets'):
ASSETS_ROOT = None
# Cache files path, where cache files are saved (defaults to ASSETS_ROOT):
CACHE_ROOT = None
# Urls for the static and assets:
STATIC_URL = 'static/'
ASSETS_URL = 'static/assets/'
FONTS_ROOT = STATIC_ROOT
FONTS_URL = STATIC_URL
IMAGES_ROOT = STATIC_ROOT
IMAGES_URL = STATIC_URL
VERBOSITY = True
STYLE = 'nested'
FATAL_UNDEFINED = True
DEBUG = 0

SPRTE_MAP_DIRECTION = 'vertical'
