import unittest

from textual.containers import Vertical
from textual.widgets import Input, OptionList

from bomber import PROXY_MODE_ON_ERROR
from tui import (
    BomberApp,
    LoginScreen,
    MainMenuScreen,
    ProxyScreen,
    SendScreen,
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
            password = app.screen.query_one("#login-password", Input)
            self.assertTrue(password.password)

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


if __name__ == "__main__":
    unittest.main()
