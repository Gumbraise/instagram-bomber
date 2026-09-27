from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .proxies import PROXY_MODE_ON_ERROR


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
DEFAULT_CONFIG: dict[str, Any] = {
    "version": "2.1",
    "analyticsConsent": None,
    "sessionId": "",
    "userList": [],
    "proxies": [],
    "proxyMode": PROXY_MODE_ON_ERROR,
}


@dataclass
class ConfigStore:
    path: Path = CONFIG_PATH

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            with self.path.open(encoding="utf-8") as config_file:
                data = json.load(config_file)
        else:
            data = self._defaults()
            self._write(data)

        for key, value in self._defaults().items():
            data.setdefault(key, value)
        return data

    def update(self, key: str, value: Any) -> None:
        self.update_many({key: value})

    def update_many(self, values: dict[str, Any]) -> None:
        data = self.load()
        data.update(values)
        self._write(data)

    def _write(self, data: dict[str, Any]) -> None:
        temporary_path = self.path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as config_file:
            json.dump(data, config_file, indent=4)
            config_file.write("\n")
        temporary_path.replace(self.path)

    @staticmethod
    def _defaults() -> dict[str, Any]:
        return {
            **DEFAULT_CONFIG,
            "userList": [],
            "proxies": [],
        }
