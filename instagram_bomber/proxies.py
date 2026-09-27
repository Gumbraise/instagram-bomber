from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from instagrapi import Client


PROXY_MODE_PER_RECIPIENT = "per_recipient"
PROXY_MODE_ON_ERROR = "on_error"
PROXY_MODES = {PROXY_MODE_PER_RECIPIENT, PROXY_MODE_ON_ERROR}


@dataclass
class ProxyPool:
    proxies: list[str]
    mode: str = PROXY_MODE_ON_ERROR
    index: int = 0

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ProxyPool:
        configured_proxies = config.get("proxies", [])
        proxies = (
            [str(proxy).strip() for proxy in configured_proxies if str(proxy).strip()]
            if isinstance(configured_proxies, list)
            else []
        )
        mode = str(config.get("proxyMode", PROXY_MODE_ON_ERROR))
        if mode not in PROXY_MODES:
            mode = PROXY_MODE_ON_ERROR
        return cls(proxies=proxies, mode=mode)

    @property
    def current(self) -> str | None:
        if not self.proxies:
            return None
        return self.proxies[self.index]

    def apply(self, client: Client) -> bool:
        proxy = self.current
        if not proxy:
            return False
        client.set_proxy(proxy)
        return True

    def rotate(self, client: Client) -> bool:
        if len(self.proxies) < 2:
            return False
        self.index = (self.index + 1) % len(self.proxies)
        self.apply(client)
        return True

    def label(self) -> str:
        proxy = self.current or "disabled"
        return proxy.rsplit("@", maxsplit=1)[-1]
