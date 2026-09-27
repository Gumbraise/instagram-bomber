from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import RichLog, Static

from ..service import InstagramService

if TYPE_CHECKING:
    from .app import BomberApp


def error_message(error: Exception) -> str:
    message = str(error).strip()
    return message or error.__class__.__name__


class BomberScreen(Screen[None]):
    BINDINGS = [Binding("escape", "go_back", "Back", show=False)]
    busy = False

    @property
    def bomber_app(self) -> BomberApp:
        return cast("BomberApp", self.app)

    @property
    def service(self) -> InstagramService:
        return self.bomber_app.service

    def header(self, section: str) -> Static:
        proxy = self.service.proxy_pool.label()
        return Static(
            f"[b]IG BOMBER[/b]  [dim]v{self.service.version}[/dim]"
            f"    [#9aa7b4]{section}[/#9aa7b4]"
            f"    [dim]proxy: {proxy}[/dim]",
            id="app-header",
        )

    def action_go_back(self) -> None:
        if not self.busy:
            self.bomber_app.show_main()

    def report_from_thread(self, message: str) -> None:
        self.app.call_from_thread(self.write_activity, message)

    def write_activity(self, message: str) -> None:
        logs = self.query(RichLog)
        if logs:
            logs.first().write(message)
