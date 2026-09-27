from textual.app import App
from textual.binding import Binding
from textual.screen import Screen

from ..service import InstagramService
from ..telemetry import SentryReporter
from .actions import GrabScreen, SendScreen
from .auth import LoginScreen
from .startup import BootScreen, ConsentScreen, MainMenuScreen


class BomberApp(App[None]):
    CSS_PATH = "styles.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [Binding("ctrl+c", "quit", "Quit")]

    def __init__(
        self,
        service: InstagramService | None = None,
        reporter: SentryReporter | None = None,
        *,
        auto_update: bool = True,
    ) -> None:
        super().__init__()
        self.service = service if service is not None else InstagramService()
        self.reporter = reporter if reporter is not None else SentryReporter()
        self.auto_update = auto_update
        self.authenticated = False
        self.startup_message = "Ready"

    def on_mount(self) -> None:
        consent = self.service.analytics_consent
        if consent is None:
            self.push_screen(ConsentScreen())
            return
        self.apply_analytics_consent(consent)
        self.start_application()

    def start_application(self) -> None:
        if self.auto_update:
            self.push_screen(BootScreen())
        else:
            self.push_screen(MainMenuScreen())

    def apply_analytics_consent(self, consent: bool) -> None:
        if consent:
            self.reporter.enable(f"instagram-bomber@{self.service.version}")
        else:
            self.reporter.disable()

    def set_analytics_consent(self, consent: bool) -> None:
        self.service.set_analytics_consent(consent)
        self.apply_analytics_consent(consent)

    def finish_initial_consent(self, consent: bool) -> None:
        self.set_analytics_consent(consent)
        self.switch_screen(BootScreen() if self.auto_update else MainMenuScreen())

    def show_main(self) -> None:
        self.switch_screen(MainMenuScreen())

    def require_login(self, destination: str) -> None:
        if self.authenticated:
            self.show_destination(destination)
        else:
            self.switch_screen(LoginScreen(destination))

    def show_destination(self, destination: str) -> None:
        screens: dict[str, Screen[None]] = {
            "send": SendScreen(),
            "grab": GrabScreen(),
        }
        self.switch_screen(screens[destination])
