from __future__ import annotations

from pathlib import Path
from typing import cast

from instagrapi.exceptions import TwoFactorRequired
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    LoadingIndicator,
    OptionList,
    RadioButton,
    RadioSet,
    RichLog,
    Static,
)
from textual.widgets.option_list import Option

from bomber import (
    PROXY_MODE_ON_ERROR,
    PROXY_MODE_PER_RECIPIENT,
    InstagramService,
)


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
                Option("Send messages\n", id="send"),
                Option("Collect users\n", id="grab"),
                Option("Configure proxies\n", id="proxy"),
                Option("Update repository\n", id="update"),
                Option("Exit\n", id="exit"),
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
            self.app.switch_screen(ProxyScreen())
        elif destination == "update":
            self.app.switch_screen(UpdateScreen())
        elif destination == "exit":
            self.app.exit()


class LoginScreen(BomberScreen):
    def __init__(self, destination: str) -> None:
        super().__init__()
        self.destination = destination

    def compose(self) -> ComposeResult:
        yield self.header("Authentication method")
        with Vertical(id="menu-body"):
            yield Static("How do you want to connect?", classes="screen-title")
            yield Static(
                "No connection is attempted until you choose and submit a method.",
                classes="muted",
            )
            yield OptionList(
                Option("Username and password\n", id="credentials"),
                Option("Account list (.txt)\n", id="account-list"),
                Option("Back\n", id="back"),
                id="login-methods",
            )
        yield Static(
            "↑↓  Navigate    Enter  Select    Mouse  Click    Esc  Back",
            id="prompt-bar",
        )

    def on_mount(self) -> None:
        self.query_one("#login-methods", OptionList).focus()

    @on(OptionList.OptionSelected, "#login-methods")
    def select_method(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "credentials":
            self.app.switch_screen(CredentialsLoginScreen(self.destination))
        elif event.option_id == "account-list":
            self.app.switch_screen(AccountListLoginScreen(self.destination))
        elif event.option_id == "back":
            self.action_go_back()


class CredentialsLoginScreen(BomberScreen):
    def __init__(self, destination: str) -> None:
        super().__init__()
        self.destination = destination

    def compose(self) -> ComposeResult:
        yield self.header("Username and password")
        with Vertical(id="screen-body"):
            yield Static("Connect to Instagram", classes="screen-title")
            yield Static(
                "Enter one account or explicitly resume its saved session.",
                classes="muted",
            )
            yield LoadingIndicator(id="login-loading")
            yield Static("Enter your account details below", id="login-status")
        with Vertical(id="prompt-panel", classes="credentials-panel"):
            yield Input(placeholder="Instagram username", id="login-username")
            yield Input(
                placeholder="Instagram password",
                password=True,
                id="login-password",
            )
            with Horizontal(classes="button-row"):
                yield Button("Connect", id="login-submit", variant="primary")
                yield Button(
                    "Use saved session",
                    id="session-submit",
                    disabled=not self.service.has_saved_session,
                )
                yield Button("Back", id="back")
            yield Static(
                "Tab  Next field    Enter  Submit    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#login-loading", LoadingIndicator).display = False
        self.query_one("#login-username", Input).focus()

    def action_go_back(self) -> None:
        if not self.busy:
            self.app.switch_screen(LoginScreen(self.destination))

    def set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.query_one("#login-status", Static).update(message)
        self.query_one("#login-loading", LoadingIndicator).display = busy
        for widget in self.query("#prompt-panel Input, #prompt-panel Button"):
            widget.disabled = busy
        self.query_one("#session-submit", Button).disabled = (
            busy or not self.service.has_saved_session
        )

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#login-submit")
    def submit_credentials(self) -> None:
        username = self.query_one("#login-username", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        self.set_busy(True, "Connecting…")
        self.login_with_credentials(username, password)

    @on(Button.Pressed, "#session-submit")
    def submit_saved_session(self) -> None:
        self.set_busy(True, "Restoring saved session…")
        self.restore_session()

    @on(Input.Submitted, "#login-password")
    def submit_password_input(self) -> None:
        self.submit_credentials()

    @work(thread=True, exclusive=True, group="login")
    def restore_session(self) -> None:
        try:
            restored = self.service.login_saved_session(self.report_from_thread)
            if not restored:
                raise ValueError("no saved session is available")
        except Exception as error:
            self.app.call_from_thread(self.login_failed, error_message(error))
        else:
            self.app.call_from_thread(self.login_succeeded)

    @work(thread=True, exclusive=True, group="login")
    def login_with_credentials(self, username: str, password: str) -> None:
        try:
            self.service.login_credentials(
                username,
                password,
                status=self.report_from_thread,
            )
        except TwoFactorRequired:
            self.app.call_from_thread(
                self.verification_required,
                username,
                password,
            )
        except Exception as error:
            self.app.call_from_thread(self.login_failed, error_message(error))
        else:
            self.app.call_from_thread(self.login_succeeded)

    def write_activity(self, message: str) -> None:
        self.query_one("#login-status", Static).update(message)

    def login_failed(self, message: str) -> None:
        self.set_busy(False, f"[red]Connection failed:[/red] {message}")
        self.query_one("#login-username", Input).focus()

    def login_succeeded(self) -> None:
        self.query_one("#login-password", Input).value = ""
        self.bomber_app.authenticated = True
        self.bomber_app.show_destination(self.destination)

    def verification_required(self, username: str, password: str) -> None:
        self.query_one("#login-password", Input).value = ""
        self.busy = False
        self.app.switch_screen(
            VerificationScreen(
                self.destination,
                username,
                password,
                origin="credentials",
            )
        )


class AccountListLoginScreen(BomberScreen):
    def __init__(self, destination: str) -> None:
        super().__init__()
        self.destination = destination

    def compose(self) -> ComposeResult:
        yield self.header("Account list")
        with Vertical(id="screen-body"):
            yield Static("Connect from a text file", classes="screen-title")
            yield Static(
                "The file is read only after you submit its path.",
                classes="muted",
            )
            yield LoadingIndicator(id="account-loading")
            yield Static("Enter the path to your account list", id="account-status")
        with Vertical(id="prompt-panel", classes="account-panel"):
            yield Input(
                placeholder="Account list path (.txt)",
                id="account-file",
            )
            with Horizontal(classes="button-row"):
                yield Button("Connect", id="account-submit", variant="primary")
                yield Button("Back", id="back")
            yield Static(
                "Enter  Submit    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#account-loading", LoadingIndicator).display = False
        self.query_one("#account-file", Input).focus()

    def action_go_back(self) -> None:
        if not self.busy:
            self.app.switch_screen(LoginScreen(self.destination))

    def set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.query_one("#account-status", Static).update(message)
        self.query_one("#account-loading", LoadingIndicator).display = busy
        for widget in self.query("#prompt-panel Input, #prompt-panel Button"):
            widget.disabled = busy

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#account-submit")
    @on(Input.Submitted, "#account-file")
    def submit_account_file(self) -> None:
        account_file = self.query_one("#account-file", Input).value.strip()
        if not account_file:
            self.login_failed("an account list path is required")
            return
        self.set_busy(True, "Reading account list…")
        self.login_with_account_file(account_file)

    @work(thread=True, exclusive=True, group="login")
    def login_with_account_file(self, account_file: str) -> None:
        username = ""
        password = ""
        try:
            username, password = self.service.credentials_from_account_file(
                Path(account_file)
            )
            self.service.login_credentials(
                username,
                password,
                status=self.report_from_thread,
            )
        except TwoFactorRequired:
            self.app.call_from_thread(
                self.verification_required,
                username,
                password,
            )
        except Exception as error:
            self.app.call_from_thread(self.login_failed, error_message(error))
        else:
            self.app.call_from_thread(self.login_succeeded)

    def write_activity(self, message: str) -> None:
        self.query_one("#account-status", Static).update(message)

    def login_failed(self, message: str) -> None:
        self.set_busy(False, f"[red]Connection failed:[/red] {message}")
        self.query_one("#account-file", Input).focus()

    def login_succeeded(self) -> None:
        self.bomber_app.authenticated = True
        self.bomber_app.show_destination(self.destination)

    def verification_required(self, username: str, password: str) -> None:
        self.busy = False
        self.app.switch_screen(
            VerificationScreen(
                self.destination,
                username,
                password,
                origin="account-list",
            )
        )


class VerificationScreen(BomberScreen):
    def __init__(
        self,
        destination: str,
        username: str,
        password: str,
        *,
        origin: str,
    ) -> None:
        super().__init__()
        self.destination = destination
        self.username = username
        self.password = password
        self.origin = origin

    def compose(self) -> ComposeResult:
        yield self.header("Two-factor verification")
        with Vertical(id="screen-body"):
            yield Static("Verification required", classes="screen-title")
            yield Static(
                f"Instagram requested a verification code for @{self.username}.",
                classes="muted",
            )
            yield LoadingIndicator(id="verification-loading")
            yield Static(
                "Enter the code from your authenticator, SMS, or Instagram prompt.",
                id="verification-status",
            )
        with Vertical(id="prompt-panel", classes="verification-panel"):
            yield Input(
                placeholder="Verification code",
                id="verification-code",
            )
            with Horizontal(classes="button-row"):
                yield Button("Verify", id="verification-submit", variant="primary")
                yield Button("Back", id="back")
            yield Static(
                "Enter  Verify    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#verification-loading", LoadingIndicator).display = False
        self.query_one("#verification-code", Input).focus()

    def action_go_back(self) -> None:
        if not self.busy:
            self.password = ""
            if self.origin == "account-list":
                screen = AccountListLoginScreen(self.destination)
            else:
                screen = CredentialsLoginScreen(self.destination)
            self.app.switch_screen(screen)

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#verification-submit")
    @on(Input.Submitted, "#verification-code")
    def submit(self) -> None:
        code = self.query_one("#verification-code", Input).value.strip()
        if not code:
            self.finish_verification("A verification code is required", error=True)
            return

        self.set_busy(True, "Verifying code…")
        self.verify_code(code)

    def set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.query_one("#verification-status", Static).update(message)
        self.query_one("#verification-loading", LoadingIndicator).display = busy
        for widget in self.query("#prompt-panel Input, #prompt-panel Button"):
            widget.disabled = busy

    @work(thread=True, exclusive=True, group="verification")
    def verify_code(self, code: str) -> None:
        try:
            self.service.login_credentials(
                self.username,
                self.password,
                verification_code=code,
                status=self.report_from_thread,
            )
        except TwoFactorRequired as error:
            self.app.call_from_thread(
                self.finish_verification,
                error_message(error),
                True,
            )
        except Exception as error:
            self.app.call_from_thread(
                self.finish_verification,
                error_message(error),
                True,
            )
        else:
            self.app.call_from_thread(self.verification_succeeded)

    def write_activity(self, message: str) -> None:
        self.query_one("#verification-status", Static).update(message)

    def finish_verification(self, message: str, error: bool) -> None:
        self.set_busy(False, message)
        style = "red" if error else "green"
        self.query_one("#verification-status", Static).update(
            f"[{style}]{message}[/{style}]"
        )
        code = self.query_one("#verification-code", Input)
        code.value = ""
        code.focus()

    def verification_succeeded(self) -> None:
        self.password = ""
        self.query_one("#verification-code", Input).value = ""
        self.bomber_app.authenticated = True
        self.bomber_app.show_destination(self.destination)


class SendScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Send messages")
        with Vertical(id="screen-body"):
            yield Static("Message activity", classes="screen-title")
            yield RichLog(id="activity-log", wrap=True, markup=False)
            yield Static("Ready", id="send-status", classes="status-line")
        with Vertical(id="prompt-panel", classes="send-panel"):
            yield Checkbox("Use collected users", id="use-saved")
            yield Input(placeholder="Target username", id="target-username")
            yield Input(placeholder="Message", id="message")
            yield Input(value="1", placeholder="Count", type="integer", id="count")
            with Horizontal(classes="button-row"):
                yield Button("Send", id="send-submit", variant="primary")
                yield Button("Back", id="back")
            yield Static(
                "Tab  Next field    Enter  Send    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#target-username", Input).focus()

    @on(Checkbox.Changed, "#use-saved")
    def toggle_saved_users(self, event: Checkbox.Changed) -> None:
        self.query_one("#target-username", Input).disabled = event.value
        self.query_one("#count", Input).disabled = event.value
        if event.value:
            self.query_one("#message", Input).focus()

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#send-submit")
    def submit(self) -> None:
        use_saved = self.query_one("#use-saved", Checkbox).value
        username = self.query_one("#target-username", Input).value.strip()
        message = self.query_one("#message", Input).value
        count_value = self.query_one("#count", Input).value
        try:
            count = int(count_value)
        except ValueError:
            self.finish_send("Count must be an integer", error=True)
            return

        self.set_busy(True)
        self.query_one("#send-status", Static).update("Sending…")
        self.send_messages(use_saved, username, message, count)

    @on(Input.Submitted, "#count")
    @on(Input.Submitted, "#message")
    def submit_input(self) -> None:
        self.submit()

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        for widget in self.query("#prompt-panel Input, #prompt-panel Button, #prompt-panel Checkbox"):
            widget.disabled = busy

    @work(thread=True, exclusive=True, group="send")
    def send_messages(
        self,
        use_saved: bool,
        username: str,
        message: str,
        count: int,
    ) -> None:
        try:
            if use_saved:
                sent = self.service.send_to_saved_users(
                    message,
                    self.report_from_thread,
                )
            else:
                sent = self.service.send_to_username(
                    username,
                    message,
                    count,
                    self.report_from_thread,
                )
        except Exception as error:
            self.app.call_from_thread(
                self.finish_send,
                error_message(error),
                True,
            )
        else:
            self.app.call_from_thread(
                self.finish_send,
                f"Sent {sent} message(s)",
                False,
            )

    def finish_send(self, message: str, error: bool = False) -> None:
        self.set_busy(False)
        style = "red" if error else "green"
        self.query_one("#send-status", Static).update(
            f"[{style}]{message}[/{style}]"
        )
        self.query_one("#message", Input).focus()


class GrabScreen(BomberScreen):
    def compose(self) -> ComposeResult:
        yield self.header("Collect users")
        with Vertical(id="screen-body"):
            yield Static("Collection activity", classes="screen-title")
            yield RichLog(id="activity-log", wrap=True, markup=False)
            yield Static("Ready", id="grab-status", classes="status-line")
        with Vertical(id="prompt-panel", classes="grab-panel"):
            yield Input(placeholder="Instagram username", id="grab-username")
            yield RadioSet(
                RadioButton("Followers", value=True, id="followers"),
                RadioButton("Following", id="following"),
                id="relation",
            )
            with Horizontal(classes="button-row"):
                yield Button("Collect", id="grab-submit", variant="primary")
                yield Button("Back", id="back")
            yield Static(
                "Tab  Change field    Enter  Collect    Esc  Back",
                classes="prompt-help",
            )

    def on_mount(self) -> None:
        self.query_one("#grab-username", Input).focus()

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.action_go_back()

    @on(Button.Pressed, "#grab-submit")
    @on(Input.Submitted, "#grab-username")
    def submit(self) -> None:
        username = self.query_one("#grab-username", Input).value.strip()
        relation = (
            "followers"
            if self.query_one("#relation", RadioSet).pressed_index == 0
            else "following"
        )
        self.set_busy(True)
        self.query_one("#grab-status", Static).update("Collecting…")
        self.collect_users(username, relation)

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        for widget in self.query("#prompt-panel Input, #prompt-panel Button, #prompt-panel RadioSet"):
            widget.disabled = busy

    @work(thread=True, exclusive=True, group="grab")
    def collect_users(self, username: str, relation: str) -> None:
        try:
            count = self.service.grab_users(
                username,
                relation,
                self.report_from_thread,
            )
        except Exception as error:
            self.app.call_from_thread(
                self.finish_grab,
                error_message(error),
                True,
            )
        else:
            self.app.call_from_thread(
                self.finish_grab,
                f"Saved {count} {relation}",
                False,
            )

    def finish_grab(self, message: str, error: bool) -> None:
        self.set_busy(False)
        style = "red" if error else "green"
        self.query_one("#grab-status", Static).update(
            f"[{style}]{message}[/{style}]"
        )
        self.query_one("#grab-username", Input).focus()


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
            self.refresh_summary(f"[red]Could not apply proxies:[/red] {error_message(error)}")
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


class BomberApp(App[None]):
    CSS_PATH = "tui.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [Binding("ctrl+c", "quit", "Quit")]

    def __init__(
        self,
        service: InstagramService | None = None,
        *,
        auto_update: bool = True,
    ) -> None:
        super().__init__()
        self.service = service if service is not None else InstagramService()
        self.auto_update = auto_update
        self.authenticated = False
        self.startup_message = "Ready"

    def on_mount(self) -> None:
        if self.auto_update:
            self.push_screen(BootScreen())
        else:
            self.push_screen(MainMenuScreen())

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


if __name__ == "__main__":
    BomberApp().run()
