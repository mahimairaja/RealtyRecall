"""Unit tests for the widget-guard rate limiter (pure, no app or async)."""

from src.core.widget_guard import RateLimiter


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_rate_limiter_allows_under_limit_and_blocks_over():
    rl = RateLimiter(max_per_min=2, clock=_Clock())
    assert rl.allow("ip") is True
    assert rl.allow("ip") is True
    assert rl.allow("ip") is False


def test_rate_limiter_window_slides():
    clock = _Clock()
    rl = RateLimiter(max_per_min=1, clock=clock)
    assert rl.allow("ip") is True
    assert rl.allow("ip") is False
    clock.t = 61.0
    assert rl.allow("ip") is True


def test_rate_limiter_keys_are_independent():
    rl = RateLimiter(max_per_min=1, clock=_Clock())
    assert rl.allow("a") is True
    assert rl.allow("b") is True
    assert rl.allow("a") is False


def test_rate_limiter_evicts_at_exactly_60s():
    clock = _Clock()
    rl = RateLimiter(max_per_min=1, clock=clock)
    assert rl.allow("ip") is True
    clock.t = 59.9
    assert rl.allow("ip") is False
    # now - t == 60 is NOT < 60, so the prior hit is evicted and this is allowed
    clock.t = 60.0
    assert rl.allow("ip") is True


def test_rate_limiter_zero_denies_all():
    rl = RateLimiter(max_per_min=0)
    assert rl.allow("ip") is False
