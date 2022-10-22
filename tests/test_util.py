import pytest

from uonsx.util import strfmt, colorize


def test_strfmt(capfd):
    bad_data_str = '{"test_key":["test_item","test_item"],"test_key2":[]}'
    good_data_str = "{'test_key': ['test_item', 'test_item'], 'test_key2': []}"
    print(strfmt(bad_data_str))
    out, err = capfd.readouterr()
    assert out.strip() == good_data_str


def test_colorize_valid_color():
    message = colorize("test_message", "blue")
    assert message.startswith("\x1b[34m")


def test_colorize_invalid_color():
    message = colorize("test_message", "cat")
    assert message.startswith("test_")
