from __future__ import annotations

import json
import os
import random
import subprocess
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Any, Iterable

from instagrapi import Client
from instagrapi.exceptions import ClientError, UserNotFound


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

HEADER = r"""
██╗ ██████╗       ██████╗  ██████╗ ███╗   ███╗██████╗ ███████╗██████╗
██║██╔════╝       ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝██╔══██╗
██║██║  ███╗█████╗██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
██║██║   ██║╚════╝██╔══██╗██║   ██║██║╚██╔╝██║██╔══██╗██╔══╝  ██╔══██╗
██║╚██████╔╝      ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝███████╗██║  ██║
╚═╝ ╚═════╝       ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
https://github.com/Gumbraise/instagram-bomber ╬ Ver. {version}
"""

MAIN_MENU = """
 1 | Instagram Bomber
 2 | Get User List
 3 | Update
 4 | Exit
"""

GRAB_MENU = """
 1 | Grab Followers
 2 | Grab Following
 3 | Back
"""


@dataclass
class ConfigStore:
    path: Path = CONFIG_PATH

    def load(self) -> dict[str, Any]:
        with self.path.open(encoding="utf-8") as config_file:
            data = json.load(config_file)

        data.setdefault("version", "2.0")
        data.setdefault("sessionId", "")
        data.setdefault("userList", [])
        return data

    def update(self, key: str, value: Any) -> None:
        data = self.load()
        data[key] = value

        temporary_path = self.path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as config_file:
            json.dump(data, config_file, indent=4)
            config_file.write("\n")
        temporary_path.replace(self.path)


class InstagramBomber:
    def __init__(
        self,
        client: Client | None = None,
        config: ConfigStore | None = None,
    ) -> None:
        self.client = client or Client()
        self.config = config or ConfigStore()

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        version = self.config.load()["version"]
        print(HEADER.format(version=version))

    def login(self) -> None:
        has_account_list = input(
            "Login | Do you have an account list? (y/N): "
        ).strip().lower()

        if has_account_list == "y":
            self._login_from_account_list()
            return

        session_id = str(self.config.load()["sessionId"])
        if session_id:
            try:
                self.client.login_by_sessionid(session_id)
                print("Login | Logged in by sessionId")
                return
            except ClientError as error:
                print(f"Login | Saved session rejected: {error}")

        self._login_with_credentials()

    def _login_with_credentials(self) -> None:
        while True:
            username = input("Login | Username: ").strip()
            password = getpass("Login | Password: ")

            try:
                self.client.login(username, password)
            except ClientError as error:
                print(f"Login | Failed: {error}")
                continue

            self.config.update("sessionId", self.client.sessionid)
            print(f"Login | Logged in as {self.client.username}")
            print("Login | sessionId saved")
            return

    def _login_from_account_list(self) -> None:
        while True:
            path = Path(input("Login | Path: ").strip()).expanduser()
            try:
                accounts = [
                    line
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                account = random.choice(accounts)
                username, password = account.split(":", maxsplit=1)
                username = username.strip()
                if not username or not password:
                    raise ValueError("empty username or password")
                print(f"Login | Username found: {username}")
                self.client.login(username, password)
                return
            except (OSError, ValueError, IndexError, ClientError) as error:
                print(f"Login | Could not use account list: {error}")

    def bomber(self) -> None:
        self.clear()
        self.login()

        while True:
            use_grabbed_users = input("| Use grabbed users? (y/N): ").strip().lower()

            try:
                if use_grabbed_users == "y":
                    user_ids = self._saved_user_ids()
                    message = input("| Message: ")
                    recipients = ((user_id, str(user_id)) for user_id in user_ids)
                else:
                    username, user_id = self._prompt_for_user("| Victim username: ")
                    message = input("| Message: ")
                    count = self._prompt_for_positive_integer("| How many?: ")
                    recipients = ((user_id, username) for _ in range(count))
                self._send(message, recipients)
            except (ClientError, ValueError) as error:
                print(f"Send | Failed: {error}")
                return

    def _saved_user_ids(self) -> list[int]:
        saved_users = self.config.load()["userList"]
        if not isinstance(saved_users, list):
            raise ValueError("config.json userList must be a list")
        if not saved_users:
            print("Send | No grabbed users found")
        return [int(user_id) for user_id in saved_users]

    def _prompt_for_user(self, prompt: str) -> tuple[str, int]:
        while True:
            username = input(prompt).strip()
            try:
                user_id = int(self.client.user_info_by_username(username).pk)
                return username, user_id
            except UserNotFound:
                print("User | Username not found")
            except ClientError as error:
                print(f"User | Lookup failed: {error}")

    def _send(self, message: str, recipients: Iterable[tuple[int, str]]) -> int:
        sent = 0
        for sent, (user_id, label) in enumerate(recipients, start=1):
            self.client.direct_send(message, user_ids=[user_id])
            print(f"({sent}) {self.client.username} > {label}: {message}")
        return sent

    def grab_users(self) -> None:
        self.clear()
        self.login()

        while True:
            print(GRAB_MENU)
            choice = self._prompt_for_choice("| ", {1, 2, 3})
            if choice == 3:
                return

            username, user_id = self._prompt_for_user("| Grabbed username: ")
            try:
                if choice == 1:
                    users = self.client.user_followers(user_id)
                    relation = "followers"
                else:
                    users = self.client.user_following(user_id)
                    relation = "following"
            except ClientError as error:
                print(f"Grab | Failed: {error}")
                continue

            user_ids = [int(grabbed_user_id) for grabbed_user_id in users]
            self.config.update("userList", user_ids)
            print(f"Grab | Saved {len(user_ids)} {relation} of {username}")
            input("Continue...")
            self.clear()

    def update_repository(self) -> None:
        result = subprocess.run(
            ["git", "pull"],
            cwd=BASE_DIR,
            check=False,
        )
        if result.returncode != 0:
            print("Update | git pull failed")

    def run(self) -> None:
        while True:
            print(MAIN_MENU)
            choice = self._prompt_for_choice("| ", {1, 2, 3, 4})

            if choice == 1:
                self.bomber()
            elif choice == 2:
                self.grab_users()
            elif choice == 3:
                self.update_repository()
            else:
                return

    @staticmethod
    def _prompt_for_choice(prompt: str, choices: set[int]) -> int:
        while True:
            try:
                choice = int(input(prompt))
            except ValueError:
                print("Wrong input")
                continue
            if choice in choices:
                return choice
            print("Wrong input")

    @staticmethod
    def _prompt_for_positive_integer(prompt: str) -> int:
        while True:
            try:
                value = int(input(prompt))
            except ValueError:
                print("Wrong number")
                continue
            if value > 0:
                return value
            print("Number must be greater than zero")


def main() -> int:
    app = InstagramBomber()
    print("Launching Instagram-Bomber...")
    app.update_repository()
    app.clear()

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nStopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
