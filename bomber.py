from instagram_bomber import (
    PROXY_MODE_ON_ERROR,
    PROXY_MODE_PER_RECIPIENT,
    PROXY_MODES,
    ConfigStore,
    InstagramService,
    ProxyPool,
)
from instagram_bomber.cli import main

__all__ = [
    "ConfigStore",
    "InstagramService",
    "PROXY_MODE_ON_ERROR",
    "PROXY_MODE_PER_RECIPIENT",
    "PROXY_MODES",
    "ProxyPool",
    "main",
]
if __name__ == "__main__":
    raise SystemExit(main())
