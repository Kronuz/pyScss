import re


# color literals
_colors = {
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgreen': '#006400',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgreen': '#90ee90',
    'lightgrey': '#d3d3d3',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32'
}

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
# Built-in CSS function regex

# Known function names
FUNCTIONS_CSS2 = 'attr counter counters url rgb rect'
## CSS3
FUNCTIONS_UNITS = 'calc min max cycle'  # http://www.w3.org/TR/css3-values/
FUNCTIONS_COLORS = 'rgba hsl hsla'  # http://www.w3.org/TR/css3-color/
FUNCTIONS_FONTS = 'local format'  # http://www.w3.org/TR/css3-fonts/
# http://www.w3.org/TR/css3-images
FUNCTIONS_IMAGES = 'image element linear-gradient radial-gradient '\
                   'repeating-linear-gradient repeating-radial-gradient'
# http://www.w3.org/TR/css3-2d-transforms/
FUNCTIONS_2D = 'matrix translate translateX translateY scale '\
               'scale scaleX scaleY rotate skew skewX skewY'
# http://www.w3.org/TR/css3-3d-transforms/
FUNCTIONS_3D = 'matrix3d translate3d translateZ scale3d scaleZ rotate3d '\
               'rotateX rotateY rotateZ skew perspective'
# http://www.w3.org/TR/css3-transitions/
FUNCTIONS_TRANSITIONS = 'cubic-bezier'
# http://www.w3.org/TR/css3-animations/
FUNCTIONS_ANIMATIONS = ''  # has 'from' and 'to' block selectors, but no new function
FUNCTIONS_FILTER = 'grayscale blur sepia saturate opacity brightness contrast hue-rotate invert'
FUNCTIONS_OTHERS = 'from to color-stop mask'
VENDORS = '-[^-]+-.+'

_css_functions_re = re.compile(r'^(%s)$' % (
    '|'.join(set(' '.join([
        FUNCTIONS_CSS2,
        FUNCTIONS_UNITS,
        FUNCTIONS_COLORS,
        FUNCTIONS_FONTS,
        FUNCTIONS_IMAGES,
        FUNCTIONS_2D,
        FUNCTIONS_3D,
        FUNCTIONS_TRANSITIONS,
        FUNCTIONS_ANIMATIONS,
        FUNCTIONS_FILTER,
        FUNCTIONS_OTHERS,
        VENDORS,
    ]).split()))))


# ------------------------------------------------------------------------------
# Bits and pieces of grammar, as regexen

SEPARATOR = '\x00'

_short_color_re = re.compile(r'(?<!\w)#([a-f0-9])\1([a-f0-9])\2([a-f0-9])\3\b', re.IGNORECASE)
_long_color_re = re.compile(r'(?<!\w)#([a-f0-9]){2}([a-f0-9]){2}([a-f0-9]){2}\b', re.IGNORECASE)
_reverse_colors = dict((v, k) for k, v in _colors.items())
for long_k, v in _colors.items():
    # Calculate the different possible representations of a color:
    short_k = _short_color_re.sub(r'#\1\2\3', v).lower()
    rgb_k = _long_color_re.sub(lambda m: 'rgb(%d, %d, %d)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
    rgba_k = _long_color_re.sub(lambda m: 'rgba(%d, %d, %d, 1)' % (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)), v)
    # get the shortest of all to use it:
    k = min([short_k, long_k, rgb_k, rgba_k], key=len)
    _reverse_colors[long_k] = k
    _reverse_colors[short_k] = k
    _reverse_colors[rgb_k] = k
    _reverse_colors[rgba_k] = k
_reverse_colors_re = re.compile(r'(?<![-\w.#$])(' + '|'.join(map(re.escape, _reverse_colors)) + r')(?![-\w])', re.IGNORECASE)
_colors_re = re.compile(r'(?<![-\w.#$])(' + '|'.join(map(re.escape, _colors)) + r')(?![-\w])', re.IGNORECASE)

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
_undefined_re = re.compile('^(?:\\$[-a-zA-Z0-9_]+|undefined)$')

_strings_re = re.compile(r'([\'"]).*?\1')

_has_placeholder_re = re.compile(r'(?<!\w)([a-z]\w*)?%')
_prop_split_re = re.compile(r'[:=]')
_skip_word_re = re.compile(r'-?[_\w\s#.,:%]*$|[-_\w#.,:%]*$', re.MULTILINE)
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
