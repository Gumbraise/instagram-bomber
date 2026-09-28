from __future__ import annotations

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


SENTRY_DSN = (
    "https://2b7000ec7273a2f7932493f00500a5e4"
    "@o476466.ingest.us.sentry.io/4512160433242112"
)
FILTERED = "[Filtered]"
SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "dsn",
    "pass",
    "proxy",
    "secret",
    "session",
    "token",
    "verification",
)


def _scrub_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        scrubbed: dict[Any, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower().replace("_", "")
            if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
                scrubbed[key] = FILTERED
            else:
                scrubbed[key] = _scrub_mapping(item)
        return scrubbed
    if isinstance(value, list):
        return [_scrub_mapping(item) for item in value]
    return value


def _scrub_stacktraces(value: Any) -> None:
    if isinstance(value, dict):
        value.pop("abs_path", None)
        value.pop("vars", None)
        for item in value.values():
            _scrub_stacktraces(item)
    elif isinstance(value, list):
        for item in value:
            _scrub_stacktraces(item)


def scrub_event(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    del hint
    scrubbed = _scrub_mapping(event)
    for key in (
        "breadcrumbs",
        "extra",
        "logentry",
        "message",
        "request",
        "server_name",
        "user",
    ):
        scrubbed.pop(key, None)

    exception = scrubbed.get("exception", {})
    if isinstance(exception, dict):
        values = exception.get("values", [])
        if isinstance(values, list):
            for value in values:
                if isinstance(value, dict) and "value" in value:
                    value["value"] = "Exception details removed"

    _scrub_stacktraces(scrubbed)
    return scrubbed


class SentryReporter:
    def __init__(self, dsn: str = SENTRY_DSN, sdk: Any = sentry_sdk) -> None:
        self.dsn = dsn
        self.sdk = sdk
        self.active = False

    def enable(self, release: str) -> None:
        if self.active:
            return
        self.sdk.init(
            dsn=self.dsn,
            release=release,
            environment="production",
            send_default_pii=False,
            include_local_variables=False,
            include_source_context=False,
            auto_session_tracking=False,
            auto_enabling_integrations=False,
            enable_logs=False,
            integrations=[
                LoggingIntegration(
                    level=None,
                    event_level=None,
                    sentry_logs_level=None,
                )
            ],
            traces_sample_rate=0.0,
            profiles_sample_rate=0.0,
            max_breadcrumbs=0,
            server_name="",
            before_send=scrub_event,
        )
        self.active = True

    def disable(self) -> None:
        if not self.active:
            return
        client = self.sdk.get_client()
        for getter_name in (
            "get_global_scope",
            "get_isolation_scope",
            "get_current_scope",
        ):
            getattr(self.sdk, getter_name)().set_client(None)
        if client.is_active():
            client.close(timeout=0)
        self.active = False
