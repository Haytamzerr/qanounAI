"""Checks on the test suite itself."""

# pytest stores the running test's id in the PYTEST_CURRENT_TEST environment variable, and Windows
# refuses variables longer than 32,767 characters. A large parameter (an 8 MB file) in an id ran
# on Linux CI but crashed the owner's Windows run. Long ids now fail everywhere, early.
MAX_ID = 1000


def pytest_collection_modifyitems(items):
    too_long = [item.nodeid[:120] for item in items if len(item.nodeid) > MAX_ID]
    if too_long:
        raise ValueError(f"test ids too long for Windows (give them ids=): {too_long}")
