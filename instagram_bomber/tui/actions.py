from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    RadioButton,
    RadioSet,
    RichLog,
    Static,
)

from .base import BomberScreen, error_message


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
        for widget in self.query(
            "#prompt-panel Input, #prompt-panel Button, #prompt-panel Checkbox"
        ):
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
        for widget in self.query(
            "#prompt-panel Input, #prompt-panel Button, #prompt-panel RadioSet"
        ):
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
