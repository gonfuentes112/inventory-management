import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError
from starlette.requests import Request

from app.core import rate_limit
from app.core.config import settings


class FakePipeline:
    def __init__(self, redis: "FakeRedis") -> None:
        self.redis = redis
        self.key = ""

    def incr(self, key: str) -> None:
        self.key = key

    def expire(self, key: str, seconds: int, nx: bool = False) -> None:
        pass

    def ttl(self, key: str) -> None:
        pass

    def execute(self) -> list:
        if self.redis.fail:
            raise RedisError("redis is down")
        count = self.redis.counts.get(self.key, 0) + 1
        self.redis.counts[self.key] = count
        return [count, True, 120]


class FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.counts: dict[str, int] = {}
        self.fail = fail

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)


def _request(ip: str) -> Request:
    """Build a real Starlette Request for a client at `ip` (minimal ASGI scope)."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users/login",
        "headers": [],
        "client": (ip, 50000),
    }
    return Request(scope)


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "redis_client", fake)
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 3)
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300)
    return fake


def test_allows_requests_up_to_the_limit_then_returns_429(fake_redis) -> None:
    request = _request("203.0.113.10")

    for _ in range(3):
        rate_limit.login_rate_limit(request)

    with pytest.raises(HTTPException) as exc_info:
        rate_limit.login_rate_limit(request)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers == {"Retry-After": "120"}


def test_each_client_ip_has_its_own_counter(fake_redis) -> None:
    for _ in range(3):
        rate_limit.login_rate_limit(_request("203.0.113.10"))

    # A different IP is unaffected.
    rate_limit.login_rate_limit(_request("203.0.113.11"))


def test_limit_of_zero_disables_rate_limiting(fake_redis, monkeypatch) -> None:
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 0)

    for _ in range(50):
        rate_limit.login_rate_limit(_request("203.0.113.10"))

    assert fake_redis.counts == {}


def test_fails_open_when_redis_is_unavailable(fake_redis) -> None:
    fake_redis.fail = True

    for _ in range(10):
        rate_limit.login_rate_limit(_request("203.0.113.10"))
