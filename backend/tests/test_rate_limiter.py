import pytest
import asyncio
from aegis.core.rate_limiter import SlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    key = "test_ip_192.168.1.10"
    limit = 3
    window = 1  # 1 second window for fast testing

    await limiter.reset(key)

    # 1st request -> allowed
    allowed1, count1, retry1 = await limiter.check_velocity(key, limit=limit, window_seconds=window)
    assert allowed1 is True
    assert count1 == 1

    # 2nd request -> allowed
    allowed2, count2, retry2 = await limiter.check_velocity(key, limit=limit, window_seconds=window)
    assert allowed2 is True
    assert count2 == 2

    # 3rd request -> allowed
    allowed3, count3, retry3 = await limiter.check_velocity(key, limit=limit, window_seconds=window)
    assert allowed3 is True
    assert count3 == 3

    # 4th request -> blocked (exceeded limit 3)
    allowed4, count4, retry4 = await limiter.check_velocity(key, limit=limit, window_seconds=window)
    assert allowed4 is False
    assert count4 == 4
    assert retry4 >= 0.0

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Request after window expires -> allowed again
    allowed5, count5, retry5 = await limiter.check_velocity(key, limit=limit, window_seconds=window)
    assert allowed5 is True
    assert count5 == 1
