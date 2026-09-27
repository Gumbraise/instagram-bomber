import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from bomber import ConfigStore, InstagramBomber


class FakeClient:
    def __init__(self) -> None:
        self.username = "sender"
        self.sessionid = "new-session"
        self.sent: list[tuple[str, list[int]]] = []
        self.sessions: list[str] = []

    def direct_send(self, message: str, user_ids: list[int]) -> None:
        self.sent.append((message, user_ids))

    def login_by_sessionid(self, session_id: str) -> None:
        self.sessions.append(session_id)


class FakeConfig:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    def load(self) -> dict[str, object]:
        return self.data


class ConfigStoreTests(unittest.TestCase):
    def test_loads_defaults_and_persists_updates(self) -> None:
        path = Path(__file__).with_name(".test-config.json")
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text('{"version": "2.0"}', encoding="utf-8")
        store = ConfigStore(path)

        self.assertEqual(store.load()["sessionId"], "")
        self.assertEqual(store.load()["userList"], [])

        store.update("userList", [10, 20])

        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["userList"], [10, 20])


class InstagramBomberTests(unittest.TestCase):
    def test_reuses_saved_session(self) -> None:
        client = FakeClient()
        config = FakeConfig({"sessionId": "saved-session"})
        app = InstagramBomber(client=client, config=config)

        with patch("builtins.input", return_value=""), redirect_stdout(StringIO()):
            app.login()

        self.assertEqual(client.sessions, ["saved-session"])

    def test_sends_each_message_to_expected_recipient(self) -> None:
        client = FakeClient()
        app = InstagramBomber(client=client, config=FakeConfig({}))

        with redirect_stdout(StringIO()):
            count = app._send("hello", [(10, "first"), (20, "second")])

        self.assertEqual(count, 2)
        self.assertEqual(
            client.sent,
            [("hello", [10]), ("hello", [20])],
        )

    def test_normalizes_saved_user_ids(self) -> None:
        app = InstagramBomber(
            client=FakeClient(),
            config=FakeConfig({"userList": ["10", 20]}),
        )

        self.assertEqual(app._saved_user_ids(), [10, 20])


if __name__ == "__main__":
    unittest.main()
