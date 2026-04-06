import pytest

from hudu_magic.helpers.general import (
    ensure_https,
    is_version_greater_or_equal,
    parse_version,
    strip_string,
)


def test_strip_string_removes_substrings():
    assert strip_string("a-b-c", ["-", "b"]) == "ac"


def test_ensure_https_prepends_scheme():
    assert ensure_https("example.com") == "https://example.com"


def test_ensure_https_keeps_http_https():
    assert ensure_https("http://x") == "http://x"
    assert ensure_https("https://x") == "https://x"


def test_ensure_https_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        ensure_https("")


def test_parse_version():
    assert parse_version("2.10.0") == (2, 10, 0)


def test_is_version_greater_or_equal():
    assert is_version_greater_or_equal("2.0", "1.9")
    assert is_version_greater_or_equal("1.0", "1.0")
    assert not is_version_greater_or_equal("0.9", "1.0")
