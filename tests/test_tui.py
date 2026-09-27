import unittest

from instagrapi.exceptions import TwoFactorRequired
from textual.containers import Vertical
from textual.widgets import Input, OptionList

from bomber import PROXY_MODE_ON_ERROR
from tui import (
    AccountListLoginScreen,
    BomberApp,
    CredentialsLoginScreen,
    LoginScreen,
    MainMenuScreen,
    ProxyScreen,
    SendScreen,
    VerificationScreen,
)


class FakeProxyPool:
    proxies: list[str] = []
    mode = PROXY_MODE_ON_ERROR

    @staticmethod
    def label() -> str:
        return "disabled"


class FakeService:
    version = "2.1"
    username = "not connected"
    has_saved_session = False
    proxy_pool = FakeProxyPool()


class TwoFactorService(FakeService):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def login_credentials(
        self,
        username: str,
        password: str,
        verification_code: str = "",
        status=None,
    ) -> None:
        self.calls.append((username, password, verification_code))
        if verification_code != "123456":
            raise TwoFactorRequired("verification required")
        if status is not None:
            status("Verification accepted")


class AccountListService(FakeService):
    has_saved_session = True

    def __init__(self) -> None:
        self.events: list[tuple[str, ...]] = []

    def login_saved_session(self, status=None) -> bool:
        self.events.append(("saved-session",))
        return True

    def credentials_from_account_file(self, path) -> tuple[str, str]:
        self.events.append(("account-file", str(path)))
        return "file-user", "file-password"

    def login_credentials(
        self,
        username: str,
        password: str,
        verification_code: str = "",
        status=None,
    ) -> None:
        self.events.append(("credentials", username, password, verification_code))


class BomberAppTests(unittest.IsolatedAsyncioTestCase):
    async def test_keyboard_navigation_replaces_current_screen(self) -> None:
        app = BomberApp(service=FakeService(), auto_update=False)

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            self.assertIsInstance(app.screen, MainMenuScreen)
            self.assertEqual(len(app.screen_stack), 2)

            await pilot.press("home", "down", "down", "enter")

            self.assertIsInstance(app.screen, ProxyScreen)
            self.assertEqual(len(app.screen_stack), 2)

            await pilot.press("escape")

            self.assertIsInstance(app.screen, MainMenuScreen)
            self.assertEqual(len(app.screen_stack), 2)

    async def test_mouse_selects_menu_and_password_is_hidden(self) -> None:
        app = BomberApp(service=FakeService(), auto_update=False)

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.click("#main-menu", offset=(5, 2))

            self.assertIsInstance(app.screen, LoginScreen)
            methods = app.screen.query_one("#login-methods", OptionList)
            methods.highlighted = 0
            await pilot.press("enter")

            self.assertIsInstance(app.screen, CredentialsLoginScreen)
            password = app.screen.query_one("#login-password", Input)
            self.assertTrue(password.password)

    async def test_account_list_waits_for_path_before_login(self) -> None:
        service = AccountListService()
        app = BomberApp(service=service, auto_update=False)

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            menu = app.screen.query_one("#main-menu", OptionList)
            menu.highlighted = 0
            await pilot.press("enter")

            self.assertIsInstance(app.screen, LoginScreen)
            methods = app.screen.query_one("#login-methods", OptionList)
            methods.highlighted = 1
            await pilot.press("enter")
            await pilot.pause()

            self.assertIsInstance(app.screen, AccountListLoginScreen)
            self.assertEqual(service.events, [])

            app.screen.query_one("#account-file", Input).value = "accounts.txt"
            await pilot.click("#account-submit")
            await app.workers.wait_for_complete()
            await pilot.pause()

            self.assertIsInstance(app.screen, SendScreen)
            self.assertEqual(
                service.events,
                [
                    ("account-file", "accounts.txt"),
                    ("credentials", "file-user", "file-password", ""),
                ],
            )

    async def test_prompt_stays_below_screen_content(self) -> None:
        app = BomberApp(service=FakeService(), auto_update=False)
        app.authenticated = True

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            menu = app.screen.query_one("#main-menu", OptionList)
            menu.highlighted = 0
            await pilot.press("enter")

            self.assertIsInstance(app.screen, SendScreen)
            body = app.screen.query_one("#screen-body", Vertical)
            prompt = app.screen.query_one("#prompt-panel", Vertical)
            self.assertGreaterEqual(prompt.region.y, body.region.bottom)

    async def test_two_factor_prompt_retries_login_with_code(self) -> None:
        service = TwoFactorService()
        app = BomberApp(service=service, auto_update=False)

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            menu = app.screen.query_one("#main-menu", OptionList)
            menu.highlighted = 0
            await pilot.press("enter")

            self.assertIsInstance(app.screen, LoginScreen)
            methods = app.screen.query_one("#login-methods", OptionList)
            methods.highlighted = 0
            await pilot.press("enter")

            login = app.screen
            self.assertIsInstance(login, CredentialsLoginScreen)
            login.query_one("#login-username", Input).value = "username"
            login.query_one("#login-password", Input).value = "password"
            await pilot.click("#login-submit")
            await app.workers.wait_for_complete()
            await pilot.pause()

            verification = app.screen
            self.assertIsInstance(verification, VerificationScreen)
            self.assertEqual(len(app.screen_stack), 2)
            verification.query_one("#verification-code", Input).value = "000000"
            await pilot.click("#verification-submit")
            await app.workers.wait_for_complete()
            await pilot.pause()

            self.assertIs(app.screen, verification)
            self.assertEqual(
                verification.query_one("#verification-code", Input).value,
                "",
            )
            verification.query_one("#verification-code", Input).value = "123456"
            await pilot.click("#verification-submit")
            await app.workers.wait_for_complete()
            await pilot.pause()

            self.assertIsInstance(app.screen, SendScreen)
            self.assertTrue(app.authenticated)
            self.assertEqual(
                service.calls,
                [
                    ("username", "password", ""),
                    ("username", "password", "000000"),
                    ("username", "password", "123456"),
                ],
            )
            self.assertEqual(verification.password, "")


if __name__ == "__main__":
    unittest.main()
