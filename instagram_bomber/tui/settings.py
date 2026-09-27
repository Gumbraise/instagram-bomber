from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    LoadingIndicator,
    RadioButton,
    RadioSet,
    RichLog,
    Static,
)

from ..proxies import PROXY_MODE_ON_ERROR, PROXY_MODE_PER_RECIPIENT
from .base import BomberScreen, error_message


class ProxyScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Proxy configuration")
        with Vertical(id="screen-body"):
            yield Static("Network route", classes="screen-title")
            yield Static(id="proxy-summary")
            yield Static(
                "Enter one proxy address or a path containing one proxy per line.",
                classes="muted",
            )
        with Vertical(id="prompt-panel", classes="proxy-panel"):
            yield Input(placeholder="Proxy address or list path", id="proxy-source")
            yield RadioSet(
                RadioButton("Rotate for each recipient", id="per-recipient"),
                RadioButton("Rotate after an error", value=True, id="on-error"),
                id="proxy-mode",
            )
            with Horizontal(classes="button-row"):
                yield Button("Apply", id="proxy-submit", variant="primary")
                yield Button("Disable", id="proxy-disable", variant="warning")
                yield Button("Back", id="back")
            yield Static(
                "Tab  Change field    Enter  Apply    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        if self.service.proxy_pool.mode == PROXY_MODE_PER_RECIPIENT:
            self.query_one("#proxy-mode", RadioSet).pressed_index = 0
        self.refresh_summary()
        self.query_one("#proxy-source", Input).focus()

    def refresh_summary(self, message: str = "") -> None:
        count = len(self.service.proxy_pool.proxies)
        mode = self.service.proxy_pool.mode.replace("_", " ")
        summary = (
            f"[b]{count} proxy(s)[/b] configured    "
            f"current: {self.service.proxy_pool.label()}    mode: {mode}"
        )
        if message:
            summary = f"{summary}\n\n{message}"
        self.query_one("#proxy-summary", Static).update(summary)

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#proxy-submit")
    @on(Input.Submitted, "#proxy-source")
    def submit(self) -> None:
        source = self.query_one("#proxy-source", Input).value.strip()
        mode = (
            PROXY_MODE_PER_RECIPIENT
            if self.query_one("#proxy-mode", RadioSet).pressed_index == 0
            else PROXY_MODE_ON_ERROR
        )
        try:
            count = self.service.configure_proxies_from_source(source, mode)
        except Exception as error:
            self.refresh_summary(
                f"[red]Could not apply proxies:[/red] {error_message(error)}"
            )
        else:
            self.refresh_summary(f"[green]Loaded {count} proxy(s)[/green]")

    @on(Button.Pressed, "#proxy-disable")
    def disable(self) -> None:
        self.service.disable_proxies()
        self.refresh_summary("[green]Proxies disabled[/green]")


class UpdateScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Repository update")
        with Vertical(id="boot-body"):
            yield Static("[b]Updating repository[/b]", classes="screen-title")
            yield LoadingIndicator(id="update-loading")
            yield RichLog(id="activity-log", wrap=True, markup=False)
            yield Static("Running git pull…", id="update-status")
            yield Button("Back", id="back")
        yield Static("Esc  Back    Ctrl+C  Quit", id="prompt-bar")

    def on_mount(self) -> None:
        self.busy = True
        self.query_one("#back", Button).disabled = True
        self.update_workspace()

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @work(thread=True, exclusive=True)
    def update_workspace(self) -> None:
        try:
            self.service.update_repository(self.report_from_thread)
        except Exception as error:
            self.app.call_from_thread(
                self.finish_update,
                error_message(error),
                True,
            )
        else:
            self.app.call_from_thread(
                self.finish_update,
                "Repository is up to date",
                False,
            )

    def finish_update(self, message: str, error: bool) -> None:
        self.busy = False
        self.query_one("#update-loading", LoadingIndicator).display = False
        style = "red" if error else "green"
        self.query_one("#update-status", Static).update(
            f"[{style}]{message}[/{style}]"
        )
        back = self.query_one("#back", Button)
        back.disabled = False
        back.focus()


class PrivacyScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Error reporting")
        with Vertical(id="consent-body"):
            yield Static("Sentry error reporting", classes="screen-title")
            yield Static(
                "Filtered crash diagnostics help identify application errors. "
                "Sensitive account and message data is removed before sending.",
                id="privacy-description",
            )
            yield Static(id="privacy-status")
        with Vertical(id="prompt-panel", classes="consent-panel"):
            with Horizontal(classes="button-row"):
                yield Button("Allow", id="privacy-allow", variant="primary")
                yield Button("Decline", id="privacy-decline")
                yield Button("Back", id="back")
            yield Static(
                "Tab  Choose    Enter  Apply    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.refresh_status()
        self.query_one("#privacy-allow", Button).focus()

    def refresh_status(self, message: str = "") -> None:
        enabled = self.service.analytics_consent is True
        state = "enabled" if enabled else "disabled"
        color = "green" if enabled else "yellow"
        text = f"Error reporting is [{color}]{state}[/{color}]"
        if message:
            text = f"{text}\n\n{message}"
        self.query_one("#privacy-status", Static).update(text)

    @on(Button.Pressed, "#privacy-allow")
    def allow(self) -> None:
        self.bomber_app.set_analytics_consent(True)
        self.refresh_status("[green]Preference saved[/green]")

    @on(Button.Pressed, "#privacy-decline")
    def decline(self) -> None:
        self.bomber_app.set_analytics_consent(False)
        self.refresh_status("[green]Preference saved[/green]")

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()
