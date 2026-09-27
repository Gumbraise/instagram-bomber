from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from instagrapi import Client
from instagrapi.exceptions import ClientError, TwoFactorRequired

from .config import PROJECT_ROOT, ConfigStore
from .proxies import (
    PROXY_MODE_ON_ERROR,
    PROXY_MODE_PER_RECIPIENT,
    PROXY_MODES,
    ProxyPool,
)


ReturnType = TypeVar("ReturnType")
StatusCallback = Callable[[str], None]


class InstagramService:
    def __init__(
        self,
        client: Client | None = None,
        config: ConfigStore | None = None,
    ) -> None:
        self.client = client if client is not None else Client()
        self.config = config if config is not None else ConfigStore()
        self.proxy_pool = ProxyPool.from_config(self.config.load())
        self.proxy_pool.apply(self.client)

    @property
    def version(self) -> str:
        return str(self.config.load()["version"])

    @property
    def username(self) -> str:
        return str(self.client.username or "not connected")

    @property
    def has_saved_session(self) -> bool:
        return bool(self.config.load()["sessionId"])

    @property
    def analytics_consent(self) -> bool | None:
        consent = self.config.load()["analyticsConsent"]
        return consent if isinstance(consent, bool) else None

    def set_analytics_consent(self, consent: bool) -> None:
        self.config.update("analyticsConsent", consent)

    def login_saved_session(self, status: StatusCallback | None = None) -> bool:
        session_id = str(self.config.load()["sessionId"])
        if not session_id:
            return False

        self._report(status, "Restoring saved Instagram session…")
        self._instagram_call(
            lambda: self.client.login_by_sessionid(session_id),
            status,
        )
        self._report(status, f"Connected as {self.username}")
        return True

    def login_credentials(
        self,
        username: str,
        password: str,
        verification_code: str = "",
        status: StatusCallback | None = None,
    ) -> None:
        if not username or not password:
            raise ValueError("username and password are required")

        self._report(status, f"Connecting as {username}…")
        self._instagram_call(
            lambda: self.client.login(
                username,
                password,
                verification_code=verification_code,
            ),
            status,
        )
        self.config.update("sessionId", self.client.sessionid)
        self._report(status, f"Connected as {self.username}; session saved")

    def login_account_file(
        self,
        path: Path,
        status: StatusCallback | None = None,
    ) -> None:
        username, password = self.credentials_from_account_file(path)
        self.login_credentials(username, password, status=status)

    @staticmethod
    def credentials_from_account_file(path: Path) -> tuple[str, str]:
        accounts = [
            line
            for line in path.expanduser().read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not accounts:
            raise ValueError("the account file is empty")

        account = random.choice(accounts)
        username, password = account.split(":", maxsplit=1)
        username = username.strip()
        if not username or not password:
            raise ValueError("the selected account is invalid")
        return username, password

    def send_to_username(
        self,
        username: str,
        message: str,
        count: int,
        status: StatusCallback | None = None,
    ) -> int:
        if not username:
            raise ValueError("a target username is required")
        if not message:
            raise ValueError("a message is required")
        if count < 1:
            raise ValueError("the message count must be greater than zero")

        self._report(status, f"Looking up @{username}…")
        user = self._instagram_call(
            lambda: self.client.user_info_by_username(username),
            status,
        )
        user_id = int(user.pk)
        recipients = ((user_id, f"@{username}") for _ in range(count))
        return self._send(message, recipients, status)

    def send_to_saved_users(
        self,
        message: str,
        status: StatusCallback | None = None,
    ) -> int:
        if not message:
            raise ValueError("a message is required")

        user_ids = self._saved_user_ids()
        if not user_ids:
            raise ValueError("no collected users are available")
        recipients = ((user_id, str(user_id)) for user_id in user_ids)
        return self._send(message, recipients, status)

    def grab_users(
        self,
        username: str,
        relation: str,
        status: StatusCallback | None = None,
    ) -> int:
        if not username:
            raise ValueError("a username is required")
        if relation not in {"followers", "following"}:
            raise ValueError("relation must be followers or following")

        self._report(status, f"Looking up @{username}…")
        user = self._instagram_call(
            lambda: self.client.user_info_by_username(username),
            status,
        )
        user_id = int(user.pk)

        self._report(status, f"Loading {relation} for @{username}…")
        if relation == "followers":
            users = self._instagram_call(
                lambda: self.client.user_followers(user_id),
                status,
            )
        else:
            users = self._instagram_call(
                lambda: self.client.user_following(user_id),
                status,
            )

        user_ids = [int(grabbed_user_id) for grabbed_user_id in users]
        self.config.update("userList", user_ids)
        self._report(status, f"Saved {len(user_ids)} {relation} from @{username}")
        return len(user_ids)

    def configure_proxies(self, proxies: Iterable[str], mode: str) -> int:
        if mode not in PROXY_MODES:
            raise ValueError("invalid proxy mode")

        normalized = list(
            dict.fromkeys(proxy.strip() for proxy in proxies if proxy.strip())
        )
        if not normalized:
            raise ValueError("at least one proxy is required")

        self.proxy_pool = ProxyPool(proxies=normalized, mode=mode)
        self.proxy_pool.apply(self.client)
        self.config.update_many({"proxies": normalized, "proxyMode": mode})
        return len(normalized)

    def configure_proxies_from_source(self, source: str, mode: str) -> int:
        if not source.strip():
            raise ValueError("a proxy or proxy list path is required")

        source_path = Path(source).expanduser()
        proxies = (
            source_path.read_text(encoding="utf-8").splitlines()
            if source_path.is_file()
            else [source]
        )
        return self.configure_proxies(proxies, mode)

    def disable_proxies(self) -> None:
        self.proxy_pool = ProxyPool([])
        self.client.set_proxy(None)
        self.config.update_many(
            {"proxies": [], "proxyMode": PROXY_MODE_ON_ERROR}
        )

    def update_repository(self, status: StatusCallback | None = None) -> bool:
        self._report(status, "Checking for updates…")
        result = subprocess.run(
            ["git", "pull"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or result.stderr).strip()
        if output:
            self._report(status, output)
        if result.returncode != 0:
            raise RuntimeError("git pull failed")
        return True

    def _saved_user_ids(self) -> list[int]:
        saved_users = self.config.load()["userList"]
        if not isinstance(saved_users, list):
            raise ValueError("config.json userList must be a list")
        return [int(user_id) for user_id in saved_users]

    def _send(
        self,
        message: str,
        recipients: Iterable[tuple[int, str]],
        status: StatusCallback | None = None,
    ) -> int:
        sent = 0
        for sent, (user_id, label) in enumerate(recipients, start=1):
            if sent > 1 and self.proxy_pool.mode == PROXY_MODE_PER_RECIPIENT:
                if self.proxy_pool.rotate(self.client):
                    self._report(
                        status,
                        f"Proxy switched to {self.proxy_pool.label()}",
                    )
            self._instagram_call(
                lambda: self.client.direct_send(message, user_ids=[user_id]),
                status,
            )
            self._report(status, f"{sent}. {self.username} → {label}: {message}")
        return sent

    def _instagram_call(
        self,
        operation: Callable[[], ReturnType],
        status: StatusCallback | None = None,
    ) -> ReturnType:
        attempts = (
            len(self.proxy_pool.proxies)
            if self.proxy_pool.mode == PROXY_MODE_ON_ERROR
            else 1
        )
        attempts = max(attempts, 1)

        for attempt in range(attempts):
            try:
                return operation()
            except TwoFactorRequired:
                raise
            except ClientError:
                is_last_attempt = attempt == attempts - 1
                if is_last_attempt or not self.proxy_pool.rotate(self.client):
                    raise
                self._report(
                    status,
                    f"Request failed; switched to {self.proxy_pool.label()}",
                )

        raise RuntimeError("Instagram operation ended without a result")

    @staticmethod
    def _report(status: StatusCallback | None, message: str) -> None:
        if status is not None:
            status(message)
