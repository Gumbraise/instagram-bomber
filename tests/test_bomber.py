import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from instagrapi.exceptions import ClientError, TwoFactorRequired

from bomber import (
    PROXY_MODE_ON_ERROR,
    PROXY_MODE_PER_RECIPIENT,
    ConfigStore,
    InstagramService,
    ProxyPool,
)


class FakeClient:
    def __init__(self) -> None:
        self.username = "sender"
        self.sessionid = "new-session"
        self.sent: list[tuple[str, list[int]]] = []
        self.sessions: list[str] = []
        self.proxies: list[str | None] = []
        self.logins: list[tuple[str, str, str]] = []
        self.send_failures = 0

    def direct_send(self, message: str, user_ids: list[int]) -> None:
        if self.send_failures:
            self.send_failures -= 1
            raise ClientError("temporary failure")
        self.sent.append((message, user_ids))

    def login_by_sessionid(self, session_id: str) -> None:
        self.sessions.append(session_id)

    def login(
        self,
        username: str,
        password: str,
        verification_code: str = "",
    ) -> None:
        self.logins.append((username, password, verification_code))

    def set_proxy(self, proxy: str | None) -> None:
        self.proxies.append(proxy)


class FakeConfig:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    def load(self) -> dict[str, object]:
        return self.data

    def update(self, key: str, value: object) -> None:
        self.data[key] = value

    def update_many(self, values: dict[str, object]) -> None:
        self.data.update(values)


class ConfigStoreTests(unittest.TestCase):
    def test_creates_missing_runtime_config(self) -> None:
        path = Path(__file__).with_name(".new-test-config.json")
        self.addCleanup(path.unlink, missing_ok=True)

        data = ConfigStore(path).load()

        self.assertTrue(path.exists())
        self.assertEqual(data["sessionId"], "")
        self.assertEqual(data["proxies"], [])

    def test_loads_defaults_and_persists_updates(self) -> None:
        path = Path(__file__).with_name(".test-config.json")
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text('{"version": "2.0"}', encoding="utf-8")
        store = ConfigStore(path)

        self.assertEqual(store.load()["sessionId"], "")
        self.assertEqual(store.load()["userList"], [])
        self.assertEqual(store.load()["proxies"], [])
        self.assertEqual(store.load()["proxyMode"], PROXY_MODE_ON_ERROR)

        store.update("userList", [10, 20])

        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["userList"], [10, 20])


class InstagramBomberTests(unittest.TestCase):
    def test_reuses_saved_session(self) -> None:
        client = FakeClient()
        config = FakeConfig({"sessionId": "saved-session"})
        service = InstagramService(client=client, config=config)

        restored = service.login_saved_session()

        self.assertTrue(restored)
        self.assertEqual(client.sessions, ["saved-session"])

    def test_sends_each_message_to_expected_recipient(self) -> None:
        client = FakeClient()
        app = InstagramService(client=client, config=FakeConfig({}))

        with redirect_stdout(StringIO()):
            count = app._send("hello", [(10, "first"), (20, "second")])

        self.assertEqual(count, 2)
        self.assertEqual(
            client.sent,
            [("hello", [10]), ("hello", [20])],
        )

    def test_normalizes_saved_user_ids(self) -> None:
        app = InstagramService(
            client=FakeClient(),
            config=FakeConfig({"userList": ["10", 20]}),
        )

        self.assertEqual(app._saved_user_ids(), [10, 20])

    def test_rotates_proxy_for_each_recipient(self) -> None:
        client = FakeClient()
        config = FakeConfig(
            {
                "proxies": ["http://proxy-one:8000", "http://proxy-two:8000"],
                "proxyMode": PROXY_MODE_PER_RECIPIENT,
            }
        )
        app = InstagramService(client=client, config=config)

        with redirect_stdout(StringIO()):
            app._send("hello", [(10, "first"), (20, "second"), (30, "third")])

        self.assertEqual(
            client.proxies,
            [
                "http://proxy-one:8000",
                "http://proxy-two:8000",
                "http://proxy-one:8000",
            ],
        )

    def test_retries_with_next_proxy_after_client_error(self) -> None:
        client = FakeClient()
        client.send_failures = 1
        config = FakeConfig(
            {
                "proxies": ["http://proxy-one:8000", "http://proxy-two:8000"],
                "proxyMode": PROXY_MODE_ON_ERROR,
            }
        )
        app = InstagramService(client=client, config=config)

        with redirect_stdout(StringIO()):
            count = app._send("hello", [(10, "first")])

        self.assertEqual(count, 1)
        self.assertEqual(
            client.proxies,
            ["http://proxy-one:8000", "http://proxy-two:8000"],
        )
        self.assertEqual(client.sent, [("hello", [10])])

    def test_hides_proxy_credentials_in_label(self) -> None:
        pool = ProxyPool(["http://username:password@proxy.example:8080"])

        self.assertEqual(pool.label(), "proxy.example:8080")

    def test_passes_verification_code_to_instagram(self) -> None:
        client = FakeClient()
        config = FakeConfig({})
        service = InstagramService(client=client, config=config)

        service.login_credentials(
            "username",
            "password",
            verification_code="123456",
        )

        self.assertEqual(
            client.logins,
            [("username", "password", "123456")],
        )
        self.assertEqual(config.data["sessionId"], "new-session")

    def test_does_not_rotate_proxy_for_two_factor_prompt(self) -> None:
        client = FakeClient()
        config = FakeConfig(
            {
                "proxies": ["http://proxy-one:8000", "http://proxy-two:8000"],
                "proxyMode": PROXY_MODE_ON_ERROR,
            }
        )
        service = InstagramService(client=client, config=config)

        def require_verification() -> None:
            raise TwoFactorRequired("verification required")

        with self.assertRaises(TwoFactorRequired):
            service._instagram_call(require_verification)

        self.assertEqual(client.proxies, ["http://proxy-one:8000"])


if __name__ == "__main__":
    unittest.main()
