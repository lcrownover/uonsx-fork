import pytest

from uonsx.util import colorize
from uonsx.debug import Debug


@pytest.fixture
def debug_1():
    d = Debug(1)
    return d


def test_debug_enabled(debug_1):
    assert debug_1.debug == True


def test_debug_bool(debug_1):
    assert bool(debug_1) == True


def test_debug_int(debug_1):
    assert int(debug_1) == 1


def test_debug_str(debug_1):
    assert str(debug_1) == "debug level: 1"


def test_debug_print(debug_1, capfd):
    debug_1.print(1, "test_message")
    out, err = capfd.readouterr()
    assert out.strip() == colorize("DEBUG[1]: test_message", "blue")
