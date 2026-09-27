from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, LoadingIndicator, OptionList, Static
from textual.widgets.option_list import Option

from .base import BomberScreen, error_message


class BootScreen(BomberScreen):
    BINDINGS: list[Binding] = []

    def compose(self) -> ComposeResult:
        yield self.header("Starting")
        with Vertical(id="boot-body"):
            yield Static("[b]Preparing workspace[/b]", classes="screen-title")
            yield LoadingIndicator()
            yield Static("Checking the Git repository…", id="boot-status")
        yield Static("Ctrl+C  Quit", id="prompt-bar")

    def on_mount(self) -> None:
        self.update_workspace()

    @work(thread=True, exclusive=True)
    def update_workspace(self) -> None:
        try:
            self.service.update_repository(self.report_from_thread)
            message = "Workspace is up to date"
        except Exception as error:
            message = f"Update skipped: {error_message(error)}"
        self.app.call_from_thread(self.finish, message)

    def write_activity(self, message: str) -> None:
        self.query_one("#boot-status", Static).update(message)

    def finish(self, message: str) -> None:
        self.bomber_app.startup_message = message
        self.bomber_app.show_main()


class ConsentScreen(BomberScreen):
    BINDINGS: list[Binding] = []

    def compose(self) -> ComposeResult:
        yield self.header("Privacy choice")
        with Vertical(id="consent-body"):
            yield Static("Help improve IG Bomber", classes="screen-title")
            yield Static(
                "Allow filtered error reports to be sent to Sentry?\n\n"
                "Reports contain the app version, Python and operating-system "
                "details, exception types, and stack traces. Passwords, session "
                "IDs, verification codes, proxy credentials, message content, "
                "local variables, and absolute paths are removed before sending.\n\n"
                "Sentry's US endpoint receives the connection IP address.\n\n"
                "You can change this choice later from Error reporting.",
                id="consent-description",
            )
        with Vertical(id="prompt-panel", classes="consent-panel"):
            with Horizontal(classes="button-row"):
                yield Button("Allow", id="consent-allow", variant="primary")
                yield Button("Decline", id="consent-decline")
            yield Static(
                "Tab  Choose    Enter  Confirm    Ctrl+C  Quit",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#consent-allow", Button).focus()

    @on(Button.Pressed, "#consent-allow")
    def allow(self) -> None:
        self.bomber_app.finish_initial_consent(True)

    @on(Button.Pressed, "#consent-decline")
    def decline(self) -> None:
        self.bomber_app.finish_initial_consent(False)


class MainMenuScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Command center")
        with Vertical(id="menu-body"):
            yield Static("What do you want to do?", classes="screen-title")
            yield Static(
                self.bomber_app.startup_message,
                id="startup-status",
                classes="muted",
            )
            yield OptionList(
                Option("Send messages", id="send"),
                Option("Collect users", id="grab"),
                Option("Configure proxies", id="proxy"),
                Option("Update repository", id="update"),
                Option("Error reporting", id="telemetry"),
                Option("Exit", id="exit"),
                id="main-menu",
            )
        yield Static(
            "↑↓  Navigate    Enter  Select    Mouse  Click    Ctrl+C  Quit",
            id="prompt-bar",
        )

    def on_mount(self) -> None:
        self.query_one("#main-menu", OptionList).focus()

    @on(OptionList.OptionSelected, "#main-menu")
    def select_menu_option(self, event: OptionList.OptionSelected) -> None:
        destination = event.option_id
        if destination == "send":
            self.bomber_app.require_login("send")
        elif destination == "grab":
            self.bomber_app.require_login("grab")
        elif destination == "proxy":
            from .settings import ProxyScreen

            self.app.switch_screen(ProxyScreen())
        elif destination == "update":
            from .settings import UpdateScreen

            self.app.switch_screen(UpdateScreen())
        elif destination == "telemetry":
            from .settings import PrivacyScreen

            self.app.switch_screen(PrivacyScreen())
        elif destination == "exit":
            self.app.exit()
