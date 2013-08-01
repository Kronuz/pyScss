from math import pi
import re

# ------------------------------------------------------------------------------
# Built-in CSS color names
# See: http://www.w3.org/TR/css3-color/#svg-color

COLOR_NAMES = {
    'aliceblue': (240, 248, 255),
    'antiquewhite': (250, 235, 215),
    'aqua': (0, 255, 255),
    'aquamarine': (127, 255, 212),
    'azure': (240, 255, 255),
    'beige': (245, 245, 220),
    'bisque': (255, 228, 196),
    'black': (0, 0, 0),
    'blanchedalmond': (255, 235, 205),
    'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226),
    'brown': (165, 42, 42),
    'burlywood': (222, 184, 135),
    'cadetblue': (95, 158, 160),
    'chartreuse': (127, 255, 0),
    'chocolate': (210, 105, 30),
    'coral': (255, 127, 80),
    'cornflowerblue': (100, 149, 237),
    'cornsilk': (255, 248, 220),
    'crimson': (220, 20, 60),
    'cyan': (0, 255, 255),
    'darkblue': (0, 0, 139),
    'darkcyan': (0, 139, 139),
    'darkgoldenrod': (184, 134, 11),
    'darkgray': (169, 169, 169),
    'darkgreen': (0, 100, 0),
    'darkkhaki': (189, 183, 107),
    'darkmagenta': (139, 0, 139),
    'darkolivegreen': (85, 107, 47),
    'darkorange': (255, 140, 0),
    'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0),
    'darksalmon': (233, 150, 122),
    'darkseagreen': (143, 188, 143),
    'darkslateblue': (72, 61, 139),
    'darkslategray': (47, 79, 79),
    'darkturquoise': (0, 206, 209),
    'darkviolet': (148, 0, 211),
    'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255),
    'dimgray': (105, 105, 105),
    'dodgerblue': (30, 144, 255),
    'firebrick': (178, 34, 34),
    'floralwhite': (255, 250, 240),
    'forestgreen': (34, 139, 34),
    'fuchsia': (255, 0, 255),
    'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255),
    'gold': (255, 215, 0),
    'goldenrod': (218, 165, 32),
    'gray': (128, 128, 128),
    'green': (0, 128, 0),
    'greenyellow': (173, 255, 47),
    'honeydew': (240, 255, 240),
    'hotpink': (255, 105, 180),
    'indianred': (205, 92, 92),
    'indigo': (75, 0, 130),
    'ivory': (255, 255, 240),
    'khaki': (240, 230, 140),
    'lavender': (230, 230, 250),
    'lavenderblush': (255, 240, 245),
    'lawngreen': (124, 252, 0),
    'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230),
    'lightcoral': (240, 128, 128),
    'lightcyan': (224, 255, 255),
    'lightgoldenrodyellow': (250, 250, 210),
    'lightgreen': (144, 238, 144),
    'lightgrey': (211, 211, 211),
    'lightpink': (255, 182, 193),
    'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170),
    'lightskyblue': (135, 206, 250),
    'lightslategray': (119, 136, 153),
    'lightsteelblue': (176, 196, 222),
    'lightyellow': (255, 255, 224),
    'lime': (0, 255, 0),
    'limegreen': (50, 205, 50),
    'linen': (250, 240, 230),
    'magenta': (255, 0, 255),
    'maroon': (128, 0, 0),
    'mediumaquamarine': (102, 205, 170),
    'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211),
    'mediumpurple': (147, 112, 219),
    'mediumseagreen': (60, 179, 113),
    'mediumslateblue': (123, 104, 238),
    'mediumspringgreen': (0, 250, 154),
    'mediumturquoise': (72, 209, 204),
    'mediumvioletred': (199, 21, 133),
    'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250),
    'mistyrose': (255, 228, 225),
    'moccasin': (255, 228, 181),
    'navajowhite': (255, 222, 173),
    'navy': (0, 0, 128),
    'oldlace': (253, 245, 230),
    'olive': (128, 128, 0),
    'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0),
    'orangered': (255, 69, 0),
    'orchid': (218, 112, 214),
    'palegoldenrod': (238, 232, 170),
    'palegreen': (152, 251, 152),
    'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147),
    'papayawhip': (255, 239, 213),
    'peachpuff': (255, 218, 185),
    'peru': (205, 133, 63),
    'pink': (255, 192, 203),
    'plum': (221, 160, 221),
    'powderblue': (176, 224, 230),
    'purple': (128, 0, 128),
    'red': (255, 0, 0),
    'rosybrown': (188, 143, 143),
    'royalblue': (65, 105, 225),
    'saddlebrown': (139, 69, 19),
    'salmon': (250, 128, 114),
    'sandybrown': (244, 164, 96),
    'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238),
    'sienna': (160, 82, 45),
    'silver': (192, 192, 192),
    'skyblue': (135, 206, 235),
    'slateblue': (106, 90, 205),
    'slategray': (112, 128, 144),
    'snow': (255, 250, 250),
    'springgreen': (0, 255, 127),
    'steelblue': (70, 130, 180),
    'tan': (210, 180, 140),
    'teal': (0, 128, 128),
    'thistle': (216, 191, 216),
    'tomato': (255, 99, 71),
    'turquoise': (64, 224, 208),
    'violet': (238, 130, 238),
    'wheat': (245, 222, 179),
    'white': (255, 255, 255),
    'whitesmoke': (245, 245, 245),
    'yellow': (255, 255, 0),
    'yellowgreen': (154, 205, 50)
}
COLOR_LOOKUP = dict((v, k) for (k, v) in COLOR_NAMES.items())

# ------------------------------------------------------------------------------
# Built-in CSS units
# See: http://www.w3.org/TR/2013/CR-css3-values-20130730/#numeric-types

# Maps units to a set of common units per type, with conversion factors
BASE_UNIT_CONVERSIONS = {
    # Lengths
    'mm': (1, 'mm'),
    'cm': (10, 'mm'),
    'in': (25.4, 'mm'),
    'px': (25.4 / 96, 'mm'),
    'pt': (25.4 / 72, 'mm'),
    'pc': (25.4 / 6, 'mm'),

    # Angles
    'deg': (1 / 360, 'turn'),
    'grad': (1 / 400, 'turn'),
    'rad': (pi / 2, 'turn'),
    'turn': (1, 'turn'),

    # Times
    'ms': (1, 'ms'),
    's':  (1000, 'ms'),

    # Frequencies
    'hz': (1, 'hz'),
    'khz': (1000, 'hz'),

    # Resolutions
    'dpi': (1, 'dpi'),
    'dpcm': (2.54, 'dpi'),
    'dppx': (96, 'dpi'),
}

def convert_units_to_base_units(units):
    """Convert a set of units into a set of "base" units.

    Returns a 2-tuple of `factor, new_units`.
    """
    total_factor = 1
    new_units = []
    for unit in units:
        if unit not in BASE_UNIT_CONVERSIONS:
            continue

        factor, new_unit = BASE_UNIT_CONVERSIONS[unit]
        total_factor *= factor
        new_units.append(new_unit)

    new_units.sort()
    return total_factor, tuple(new_units)


# A fixed set of units can be omitted when the value is 0
# See: http://www.w3.org/TR/2013/CR-css3-values-20130730/#lengths
ZEROABLE_UNITS = frozenset((
    # Relative lengths
    'em', 'ex', 'ch', 'rem',
    # Viewport
    'vw', 'vh', 'vmin', 'vmax',
    # Absolute lengths
    'cm', 'mm', 'in', 'px', 'pt', 'pc',
))

_units_weights = {
    'em': 10,
    'mm': 10,
    'ms': 10,
    'hz': 10,
    '%': 100,
}
_conv = {
    'size': {
        'em': 13.0,
        'px': 1.0
    },
    'length': {
        'mm':  1.0,
        'cm':  10.0,
        'in':  25.4,
        'pt':  25.4 / 72,
        'pc':  25.4 / 6
    },
    'time': {
        'ms':  1.0,
        's':   1000.0
    },
    'freq': {
        'hz':  1.0,
        'khz': 1000.0
    },
    'any': {
        '%': 1.0 / 100
    }
}

# units and conversions
_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc', 'deg', 'rad'
          'grad', 'ms', 's', 'hz', 'khz', '%']
_zero_units = ['em', 'ex', 'px', 'cm', 'mm', 'in', 'pt', 'pc']  # units that can be zeroed
_conv_type = {}
_conv_factor = {}
for t, m in _conv.items():
    for k, f in m.items():
        _conv_type[k] = t
        _conv_factor[k] = f
del t, m, k, f


# ------------------------------------------------------------------------------
# Built-in CSS function reference

# Known function names
BUILTIN_FUNCTIONS = frozenset([
    # CSS2
    'attr', 'counter', 'counters', 'url', 'rgb', 'rect',

    # CSS3 values: http://www.w3.org/TR/css3-values/
    'calc', 'min', 'max', 'cycle',

    # CSS3 colors: http://www.w3.org/TR/css3-color/
    'rgba', 'hsl', 'hsla',

    # CSS3 fonts: http://www.w3.org/TR/css3-fonts/
    'local', 'format',

    # CSS3 images: http://www.w3.org/TR/css3-images/
    'image', 'element',
    'linear-gradient', 'radial-gradient',
    'repeating-linear-gradient', 'repeating-radial-gradient',

    # CSS3 transforms: http://www.w3.org/TR/css3-transforms/
    'perspective',
    'matrix', 'matrix3d',
    'rotate', 'rotateX', 'rotateY', 'rotateZ', 'rotate3d',
    'translate', 'translateX', 'translateY', 'translateZ', 'translate3d',
    'scale', 'scaleX', 'scaleY', 'scaleZ', 'scale3d',
    'skew', 'skewX', 'skewY',

    # CSS3 transitions: http://www.w3.org/TR/css3-transitions/
    'cubic-bezier', 'steps',

    # CSS filter effects:
    # https://dvcs.w3.org/hg/FXTF/raw-file/tip/filters/index.html
    'grayscale', 'sepia', 'saturate', 'hue-rotate', 'invert', 'opacity',
    'brightness', 'contrast', 'blur', 'drop-shadow', 'custom',

    # Others
    'color-stop',           # Older version of CSS3 gradients
    'mask',                 # ???
])


def is_builtin_css_function(name):
    """Returns whether the given `name` looks like the name of a builtin CSS
    function.

    Unrecognized functions not in this list produce warnings.
    """
    name = name.replace('_', '-')

    if name in BUILTIN_FUNCTIONS:
        return True

    # Vendor-specific functions (-foo-bar) are always okay
    if name[0] == '-' and '-' in name[1:]:
        return True

    return False

# ------------------------------------------------------------------------------
# Bits and pieces of grammar, as regexen

SEPARATOR = '\x00'

_expr_glob_re = re.compile(r'''
    \#\{(.*?)\}                   # Global Interpolation only
''', re.VERBOSE)

# XXX these still need to be fixed; the //-in-functions thing is a chumpy hack
_ml_comment_re = re.compile(r'\/\*(.*?)\*\/', re.DOTALL)
_sl_comment_re = re.compile(r'(?<!\burl[(])(?<!\w{2}:)\/\/.*')
_zero_units_re = re.compile(r'\b0(' + '|'.join(map(re.escape, _zero_units)) + r')(?!\w)', re.IGNORECASE)
_zero_re = re.compile(r'\b0\.(?=\d)')

_escape_chars_re = re.compile(r'([^-a-zA-Z0-9_])')
_interpolate_re = re.compile(r'(#\{\s*)?(\$[-\w]+)(?(1)\s*\})')
_spaces_re = re.compile(r'\s+')
_expand_rules_space_re = re.compile(r'\s*{')
_collapse_properties_space_re = re.compile(r'([:#])\s*{')
_variable_re = re.compile('^\\$[-a-zA-Z0-9_]+$')

_strings_re = re.compile(r'([\'"]).*?\1')

_has_placeholder_re = re.compile(r'(?<!\w)([a-z]\w*)?%')
_prop_split_re = re.compile(r'[:=]')
_has_code_re = re.compile('''
    (?:^|(?<=[{;}]))            # the character just before it should be a '{', a ';' or a '}'
    \s*                         # ...followed by any number of spaces
    (?:
        (?:
            \+
        | @include
        | @warn
        | @mixin
        | @function
        | @if
        | @else
        | @for
        | @each
        )
        (?![^(:;}]*['"])
    |
        @import
    )
''', re.VERBOSE)
