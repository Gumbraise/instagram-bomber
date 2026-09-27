from pathlib import Path

from instagrapi.exceptions import TwoFactorRequired
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, LoadingIndicator, OptionList, Static
from textual.widgets.option_list import Option

from .base import BomberScreen, error_message


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
