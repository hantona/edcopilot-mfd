from pathlib import Path


def test_file_path(file):
    """Returns the qualified path of a test data file

    Unit tests are run with a different working directory depending on how they are started.
    When a single test is run, the working directory is the test's location.
    When a directory of tests is run, the working directory can be a parent directory.
    Resolving the path relative to this file makes the tests work in all cases.
    """
    current_file_path = Path(__file__).resolve()
    return current_file_path.parent.parent.parent / "test_data" / file


def temp_path():
    """Return the path of a temp directory in the project root"""
    current_file_path = Path(__file__).resolve()
    return current_file_path.parent.parent.parent / "temp"
