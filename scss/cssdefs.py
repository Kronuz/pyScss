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


__elements_of_type_block = 'address, article, aside, blockquote, center, dd, details, dir, div, dl, dt, fieldset, figcaption, figure, footer, form, frameset, h1, h2, h3, h4, h5, h6, header, hgroup, hr, isindex, menu, nav, noframes, noscript, ol, p, pre, section, summary, ul'
__elements_of_type_inline = 'a, abbr, acronym, audio, b, basefont, bdo, big, br, canvas, cite, code, command, datalist, dfn, em, embed, font, i, img, input, kbd, keygen, label, mark, meter, output, progress, q, rp, rt, ruby, s, samp, select, small, span, strike, strong, sub, sup, textarea, time, tt, u, var, video, wbr'
__elements_of_type_table = 'table'
__elements_of_type_list_item = 'li'
__elements_of_type_table_row_group = 'tbody'
__elements_of_type_table_header_group = 'thead'
__elements_of_type_table_footer_group = 'tfoot'
__elements_of_type_table_row = 'tr'
__elements_of_type_table_cel = 'td, th'
__elements_of_type_html5_block = 'article, aside, details, figcaption, figure, footer, header, hgroup, menu, nav, section, summary'
__elements_of_type_html5_inline = 'audio, canvas, command, datalist, embed, keygen, mark, meter, output, progress, rp, rt, ruby, time, video, wbr'
__elements_of_type_html5 = 'article, aside, audio, canvas, command, datalist, details, embed, figcaption, figure, footer, header, hgroup, keygen, mark, menu, meter, nav, output, progress, rp, rt, ruby, section, summary, time, video, wbr'
__elements_of_type = {
    'block': dict(enumerate(sorted(__elements_of_type_block.replace(' ', '').split(',')))),
    'inline': dict(enumerate(sorted(__elements_of_type_inline.replace(' ', '').split(',')))),
    'table': dict(enumerate(sorted(__elements_of_type_table.replace(' ', '').split(',')))),
    'list-item': dict(enumerate(sorted(__elements_of_type_list_item.replace(' ', '').split(',')))),
    'table-row-group': dict(enumerate(sorted(__elements_of_type_table_row_group.replace(' ', '').split(',')))),
    'table-header-group': dict(enumerate(sorted(__elements_of_type_table_header_group.replace(' ', '').split(',')))),
    'table-footer-group': dict(enumerate(sorted(__elements_of_type_table_footer_group.replace(' ', '').split(',')))),
    'table-row': dict(enumerate(sorted(__elements_of_type_table_footer_group.replace(' ', '').split(',')))),
    'table-cell': dict(enumerate(sorted(__elements_of_type_table_footer_group.replace(' ', '').split(',')))),
    'html5-block': dict(enumerate(sorted(__elements_of_type_html5_block.replace(' ', '').split(',')))),
    'html5-inline': dict(enumerate(sorted(__elements_of_type_html5_inline.replace(' ', '').split(',')))),
    'html5': dict(enumerate(sorted(__elements_of_type_html5.replace(' ', '').split(',')))),
}
