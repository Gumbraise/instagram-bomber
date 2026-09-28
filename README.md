# Instagram Bomber

A full-screen command-line application for sending Instagram direct messages
with [instagrapi](https://github.com/subzeroid/instagrapi).

> Instagram Bomber uses an unofficial private API. Only contact recipients you
> are authorized to message. Automated activity can be rate-limited and may
> lead to account restrictions.

## Features

- Send a repeated message to one user.
- Collect followers or following accounts and message the resulting list.
- Log in with a username and password or a `username:password` text file.
- Resume saved sessions and handle two-factor verification in a dedicated view.
- Use one proxy or rotate several proxies per recipient or after an error.
- Navigate the full-screen interface with the keyboard or mouse.
- Choose whether filtered error reports are sent to Sentry.
- Update the Git checkout from the main menu.

## Requirements

- Python 3.10 or newer
- Git for cloning and the built-in updater

## Installation

```console
git clone https://github.com/Gumbraise/instagram-bomber.git
cd instagram-bomber
python -m venv .venv
```

Activate the virtual environment on Windows:

```console
.venv\Scripts\activate
```

Or on Linux and macOS:

```console
source .venv/bin/activate
```

Install the pinned dependencies:

```console
python -m pip install -r requirements.txt
```

## Usage

```console
python bomber.py
```

You can also run the package directly:

```console
python -m instagram_bomber
```

Use the arrow keys and `Enter`, click controls with the mouse, press `Tab` to
move between fields, and press `Escape` to return to the main menu.

The login screen offers a masked username/password form and an account-list
mode. In account-list mode, provide the file before any connection is made.
Place one account on each non-empty line:

```text
username:password
```

When Instagram requests two-factor authentication, the application opens a new
screen for the verification code. Sessions are saved in the local
`config.json` file and reused only when selected.

## Proxies

Open **Configure Proxies** from the main menu and enter either one proxy or the
path to a text file containing one proxy per line:

```text
http://username:password@proxy.example:8080
```

Choose whether to rotate proxies for every recipient or only after an Instagram
error. Proxy credentials are hidden in terminal messages, but complete proxy
addresses are stored locally in `config.json`.

## Privacy and security

On first launch, the application asks whether it may send filtered error
reports to Sentry. This choice can be changed later from **Error Reporting**.
The local `config.json` can contain a reusable session, account IDs, and proxy
credentials; it is ignored by Git and must be kept private.

Please report vulnerabilities according to [SECURITY.md](SECURITY.md).

## Contributing

[![List of contributors](https://contrib.rocks/image?repo=Gumbraise/instagram-bomber)](https://github.com/Gumbraise/instagram-bomber/graphs/contributors)

For local setup, tests, and pull-request expectations, see
[CONTRIBUTING.md](CONTRIBUTING.md). Please also follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Donations

If you would like to support this project, you can donate through:

- PayPal: [paypal.me/Gumbraise](https://www.paypal.me/Gumbraise)
- Bitcoin: `bc1qwurupha8n5m96x477l3j05nxgeqthp4y3ncagq`
- Ethereum / Polygon / Chainlink / USDT / USDC:
  `0xa46617B99Dc72E1138Bd4ccd8f60eA27fF2CfFe4`
- Solana / USDT / USDC:
  `GxBb3KJeBUqnftSNU2VBPTMM2vq6kcj5MPwCXbfy3B2P`
- Litecoin: `ltc1qq4glktdz4z4xvzf4dz8p56cf45cgcfqdsxv7j4`
- TRON: `TAUiCbBLftDRqurBzbbDxJ7Mov4Sn5Y6pj`

## License

Instagram Bomber is available under the [MIT License](LICENSE).
