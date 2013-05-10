"""py.test plugin configuration."""

def pytest_addoption(parser):
    """Add an option for filtering the file tests run.

    This has to be done in the project root; py.test doesn't (and can't)
    recursively look for conftest.py files until after it's parsed the command
    line.
    """
    parser.addoption('--test-file-filter',
        help='comma-separated regexes to select test files',
        action='store',
        type='string',
        dest='test_file_filter',
        default=None,
    )
