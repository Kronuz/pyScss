"""Tests for miscellaneous features that should maybe be broken out into their
own files, maybe.
"""

from scss import Scss


def test_extend_across_files():
    compiler = Scss(scss_opts=dict(compress=0))
    compiler._scss_files = {}
    compiler._scss_files['first.css'] = '''
    @option compress:no, short_colors:yes, reverse_colors:yes;
    .specialClass extends .basicClass {
        padding: 10px;
        font-size: 14px;
    }
    '''
    compiler._scss_files['second.css'] = '''
    @option compress:no, short_colors:yes, reverse_colors:yes;
    .basicClass {
        padding: 20px;
        background-color: #FF0000;
    }
    '''
    actual = compiler.compile()
    expected = """\
.basicClass, .specialClass {
  padding: 20px;
  background-color: #FF0000;
}
.specialClass {
  padding: 10px;
  font-size: 14px;
}
"""

    assert expected == actual
