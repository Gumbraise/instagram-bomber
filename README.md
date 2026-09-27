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

Install the dependency:

```console
python -m pip install -r requirements.txt
```

## Usage

Run the application from the repository root:

```console
python bomber.py
```

The application runs `git pull` at startup, then displays its menu. Press
`Ctrl+C` at any time to stop it.

The login prompt accepts either one account entered interactively or a text
file containing accounts. Each account must be on its own line:

```text
username:password
```

When an account file is used, one non-empty line is selected at random.

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

The first configured proxy is always applied before login. Enter an empty value
in the proxy configuration screen to disable proxies. Proxy passwords are
hidden in terminal messages, but the complete proxy addresses are stored in
`config.json`.

A failed message may have reached Instagram before the client received the
error. Retrying it with another proxy can therefore produce a duplicate.

## Configuration

[`config.json`](config.json) stores:

- `version`: the version displayed in the header;
- `sessionId`: the Instagram session reused on the next login;
- `userList`: the numeric IDs collected from followers or following users;
- `proxies`: the configured proxy addresses;
- `proxyMode`: either `per_recipient` or `on_error`.

The session ID grants access to the associated account. Keep the configuration
file private and clear `sessionId` before sharing it.

## Tests

The test suite does not connect to Instagram:

```console
python -m unittest discover -s tests -v
```

This project uses Instagram's unofficial private API. Automated direct
messages may be rate-limited and may lead to account restrictions.
