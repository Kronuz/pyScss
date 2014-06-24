"""
Disables cache_buster on sprite_map for sprite_import test
"""

import scss

sprite_map_0 = scss.sprite_map

def sprite_map_patch(g, **kwargs):
    global sprite_map_0
    kwargs.setdefault('cache_buster', scss.types.Boolean(False))
    return sprite_map_0(g, **kwargs)

scss.sprite_map = sprite_map_patch
