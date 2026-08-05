"""HTTP retry helper tests."""

from datetime import datetime, timezone

from hudu_magic.helpers.http import (
    is_rate_limit_response,
    retry_delay_seconds,
    seconds_until_next_rate_limit_window,
)


def test_is_rate_limit_response_status_and_message():
    assert is_rate_limit_response(429, "slow down")
    assert is_rate_limit_response(503, "Retry later")
    assert is_rate_limit_response(500, "429 Too Many Requests")
    assert not is_rate_limit_response(422, "validation failed")


def test_seconds_until_next_rate_limit_window_at_window_start():
    now = datetime(2026, 7, 10, 10, 0, 30, tzinfo=timezone.utc)
    delay = seconds_until_next_rate_limit_window(
        window_seconds=300,
        now=now,
        jitter_min=2,
        jitter_max=2,
    )
    assert delay == 300 - 30 + 2


def test_retry_delay_seconds_rate_limit():
    delay = retry_delay_seconds(
        429,
        "Too Many Requests",
        retry_on_rate_limit=True,
        retry_on_error=True,
        rate_limit_window_seconds=300,
        error_retry_delay=5,
    )
    assert delay is not None
    assert delay >= 1


def test_retry_delay_seconds_generic_error():
    delay = retry_delay_seconds(
        500,
        "server error",
        retry_on_rate_limit=True,
        retry_on_error=True,
        rate_limit_window_seconds=300,
        error_retry_delay=5,
    )
    assert delay == 5.0


def test_retry_delay_seconds_skips_404():
    assert retry_delay_seconds(
        404,
        "Not Found",
        retry_on_rate_limit=True,
        retry_on_error=True,
        rate_limit_window_seconds=300,
        error_retry_delay=5,
    ) is None
