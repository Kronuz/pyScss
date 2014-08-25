"""
Disables cache_buster on sprite_map for sprite_import test
"""

from scss import compiler, types

sprite_map_0 = compiler.sprite_map

def sprite_map_patch(g, **kwargs):
    global sprite_map_0
    kwargs.setdefault('cache_buster', types.Boolean(False))
    return sprite_map_0(g, **kwargs)


def setUp():
    compiler.sprite_map = sprite_map_patch


def tearDown():
    compiler.sprite_map = sprite_map_0
