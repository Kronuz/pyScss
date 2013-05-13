"""py.test plugin configuration."""

import glob
import os.path
import re

FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')

test_file_pairs = None  # edited below
def pytest_configure(config):
    """Scan for test files.  Done here because other hooks tend to run once
    *per test*, and there's no reason to do this work more than once.
    """
    global test_file_pairs

    scss_files = glob.glob(os.path.join(FILES_DIR, '*/*.scss'))
    test_file_filter = config.getoption('test_file_filter')
    if test_file_filter:
        file_filters = [
            re.compile(filt)
            for filt in test_file_filter.split(',')
        ]

        filtered_scss_files = []
        for fn in scss_files:
            relfn = os.path.relpath(fn, FILES_DIR)
            for rx in file_filters:
                if rx.search(relfn):
                    filtered_scss_files.append(fn)
                    break

        scss_files = filtered_scss_files

    test_file_pairs = [(fn, fn[:-5] + '.css') for fn in scss_files]

def pytest_generate_tests(metafunc):
    """Inject the test files as parametrizations.

    Relies on the command-line option `--test-file-filter`, set by the root
    conftest.py.
    """

    if 'scss_file_pair' in metafunc.fixturenames:
        metafunc.parametrize('scss_file_pair', test_file_pairs)
