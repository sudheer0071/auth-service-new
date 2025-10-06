"""Redis client helpers with Azure-friendly defaults."""

from __future__ import annotations

import redis

try:
    from redis.cluster import RedisCluster
except ImportError:  # pragma: no cover - redis<4 without cluster extras
    RedisCluster = None

from . import config


def _should_use_ssl(url: str | None) -> bool:
    if url:
        return url.startswith("rediss://")
    # Azure managed Redis typically enforces TLS on 6380/10000
    return config.REDIS_PORT in (6380, 10000)


def get_redis_client() -> redis.Redis:
    """Get Redis client with appropriate configuration for FastAPI app."""
    common_kwargs = {
        "decode_responses": True,
        "socket_connect_timeout": config.REDIS_SOCKET_CONNECT_TIMEOUT,
        "socket_timeout": config.REDIS_SOCKET_TIMEOUT,
        "health_check_interval": config.REDIS_HEALTH_CHECK_INTERVAL,
        "socket_keepalive": True,
        "retry_on_timeout": True,
    }

    ssl_kwargs = {}
    if _should_use_ssl(config.REDIS_URL):
        ssl_kwargs["ssl_cert_reqs"] = None
        if not config.REDIS_URL:
            ssl_kwargs["ssl"] = True

    if config.REDIS_CLUSTER_MODE:
        if RedisCluster is None:
            raise RuntimeError(
                "Redis cluster mode requested but redis-py cluster support is unavailable."
            )
        cluster_kwargs = {
            **common_kwargs,
            **ssl_kwargs,
            "password": config.REDIS_PASSWORD,
            "skip_full_coverage_check": True,
        }
        if config.REDIS_USERNAME:
            cluster_kwargs["username"] = config.REDIS_USERNAME

        if config.REDIS_URL:
            return RedisCluster.from_url(
                config.REDIS_URL,
                **cluster_kwargs,
            )

        return RedisCluster(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            **cluster_kwargs,
        )

    if config.REDIS_URL:
        # use URL form (TLS via rediss://)
        return redis.from_url(
            config.REDIS_URL,
            **common_kwargs,
            **ssl_kwargs,
        )

    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=config.REDIS_PASSWORD,
        username=config.REDIS_USERNAME,
        **common_kwargs,
        **ssl_kwargs,
    )