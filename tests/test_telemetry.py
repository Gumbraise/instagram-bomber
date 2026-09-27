import unittest

from telemetry import FILTERED, SentryReporter, scrub_event


class FakeClient:
    def __init__(self) -> None:
        self.closed_with: list[int] = []

    @staticmethod
    def is_active() -> bool:
        return True

    def close(self, timeout: int) -> None:
        self.closed_with.append(timeout)


class FakeScope:
    def __init__(self) -> None:
        self.clients: list[object | None] = []

    def set_client(self, client=None) -> None:
        self.clients.append(client)


class FakeSdk:
    def __init__(self) -> None:
        self.init_options = {}
        self.client = FakeClient()
        self.scopes = [FakeScope(), FakeScope(), FakeScope()]

    def init(self, **options) -> None:
        self.init_options = options

    def get_client(self) -> FakeClient:
        return self.client

    def get_global_scope(self) -> FakeScope:
        return self.scopes[0]

    def get_isolation_scope(self) -> FakeScope:
        return self.scopes[1]

    def get_current_scope(self) -> FakeScope:
        return self.scopes[2]


class SentryReporterTests(unittest.TestCase):
    def test_enables_private_error_reporting(self) -> None:
        sdk = FakeSdk()
        reporter = SentryReporter(dsn="https://public@example.invalid/1", sdk=sdk)

        reporter.enable("instagram-bomber@2.1")

        self.assertTrue(reporter.active)
        self.assertEqual(sdk.init_options["dsn"], "https://public@example.invalid/1")
        self.assertFalse(sdk.init_options["send_default_pii"])
        self.assertFalse(sdk.init_options["include_local_variables"])
        self.assertEqual(sdk.init_options["traces_sample_rate"], 0.0)
        self.assertEqual(sdk.init_options["profiles_sample_rate"], 0.0)

    def test_disables_active_client_without_flushing(self) -> None:
        sdk = FakeSdk()
        reporter = SentryReporter(sdk=sdk)
        reporter.enable("instagram-bomber@2.1")

        reporter.disable()

        self.assertFalse(reporter.active)
        self.assertEqual(sdk.client.closed_with, [0])
        self.assertTrue(all(scope.clients == [None] for scope in sdk.scopes))

    def test_scrubs_sensitive_event_data(self) -> None:
        event = {
            "message": "login failed with password",
            "server_name": "private-computer",
            "user": {"username": "private-user"},
            "extra": {"sessionId": "private-session"},
            "contexts": {
                "runtime": {"name": "CPython"},
                "credentials": {"proxy_password": "private-password"},
            },
            "exception": {
                "values": [
                    {
                        "type": "RuntimeError",
                        "value": "account private-user failed",
                        "stacktrace": {
                            "frames": [
                                {
                                    "abs_path": "C:/Users/private-user/app.py",
                                    "filename": "app.py",
                                    "vars": {"password": "private-password"},
                                }
                            ]
                        },
                    }
                ]
            },
        }

        scrubbed = scrub_event(event, {})

        self.assertNotIn("message", scrubbed)
        self.assertNotIn("server_name", scrubbed)
        self.assertNotIn("user", scrubbed)
        self.assertNotIn("extra", scrubbed)
        self.assertEqual(
            scrubbed["contexts"]["credentials"]["proxy_password"],
            FILTERED,
        )
        exception = scrubbed["exception"]["values"][0]
        self.assertEqual(exception["value"], "Exception details removed")
        frame = exception["stacktrace"]["frames"][0]
        self.assertEqual(frame, {"filename": "app.py"})


if __name__ == "__main__":
    unittest.main()
