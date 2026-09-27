# Instagram Bomber

A command-line Instagram direct-message sender built with
[`instagrapi`](https://github.com/subzeroid/instagrapi).

The application can:

- send the same direct message several times to one user;
- collect the followers or following list of a user;
- send one direct message to every collected user;
- reuse a saved Instagram session;
- use one proxy or rotate through several proxies;
- update its Git checkout from the main menu.

## Requirements

- Python 3.10 or newer
- Git, when using the built-in update command

## Installation

Create and activate a virtual environment:

```console
python -m venv .venv
```

On Windows:

```console
.venv\Scripts\activate
```

On Linux or macOS:

```console
source .venv/bin/activate
```

Install the dependencies:

```console
python -m pip install -r requirements.txt
```

## Usage

Run the application from the repository root:

```console
python bomber.py
```

The application opens in a full-screen terminal interface and runs `git pull`
on its startup screen.

## Terminal navigation

Each view replaces the previous one, so completed actions do not accumulate in
the terminal history. Input fields and their actions stay docked at the bottom
of the screen.

- Use the arrow keys and `Enter` to navigate menus.
- Click menu entries, fields, radio buttons, checkboxes, and buttons with the
  mouse.
- Use `Tab` to move between form controls.
- Press `Escape` to return to the main menu.
- Press `Ctrl+C` to close the application and restore the terminal.

The login prompt accepts either one account entered interactively or a text
file containing accounts. Each account must be on its own line:

```text
username:password
```

When an account file is used, one non-empty line is selected at random.

## Two-factor authentication

When Instagram's CAA login flow requests two-factor verification, the login
view is replaced by a dedicated verification screen. Enter the code from the
authenticator application, SMS, or Instagram prompt and select `Verify`.

An invalid or expired code keeps the verification screen open so another code
can be entered. The password and verification code are cleared from the UI
after success or when returning to the login screen.

## Proxies

Choose `Configure Proxies` from the main menu. Enter either one proxy directly:

```text
http://username:password@proxy.example:8080
```

Or enter the path to a text file containing one proxy per line:

```text
http://proxy-one.example:8080
http://proxy-two.example:8080
```

The application offers two rotation modes:

- `Rotate for every recipient` uses the next proxy before each new direct
  message recipient;
- `Rotate after an Instagram error` retries a failed login, lookup, collection,
  or message operation with the next configured proxy.

The first configured proxy is always applied before login. Select `Disable` in
the proxy configuration screen to stop using proxies. Proxy passwords are
hidden in terminal messages, but the complete proxy addresses are stored in the
local `config.json`.

A failed message may have reached Instagram before the client received the
error. Retrying it with another proxy can therefore produce a duplicate.

## Configuration

The application creates a local `config.json` automatically from the defaults
in [`config.example.json`](config.example.json). The runtime file is ignored by
Git because it stores credentials and account data:

- `version`: the version displayed in the header;
- `sessionId`: the Instagram session reused on the next login;
- `userList`: the numeric IDs collected from followers or following users;
- `proxies`: the configured proxy addresses;
- `proxyMode`: either `per_recipient` or `on_error`.

The session ID grants access to the associated account. Keep `config.json`
private and do not force-add it to Git.

## Tests

The test suite does not connect to Instagram. It also runs the terminal UI in
headless mode to exercise keyboard navigation, mouse clicks, screen replacement,
compact-terminal layout, and password masking:

```console
python -m unittest discover -s tests -v
```

This project uses Instagram's unofficial private API. Automated direct
messages may be rate-limited and may lead to account restrictions.
