# Contributing

Thanks for helping improve Instagram Bomber.

Before starting a large change, open or comment on a GitHub issue so the scope
can be discussed. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) in all
project spaces. Report vulnerabilities through the process described in the
[Security Policy](SECURITY.md), not in a public issue.

## Development setup

Fork and clone the repository, then create a virtual environment:

```console
python -m venv .venv
```

Activate it on Windows:

```console
.venv\Scripts\activate
```

Or on Linux and macOS:

```console
source .venv/bin/activate
```

Install the pinned dependencies:

```console
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the application from the repository root:

```console
python bomber.py
```

## Development guidelines

- Put application code in the `instagram_bomber` package. Keep the root
  modules as compatibility entry points.
- Keep direct dependencies limited and pinned in `requirements.txt`. Explain
  why a new dependency is needed in the pull request.
- Keep Instagram calls behind the service layer and use fakes in automated
  tests. The test suite must not contact live accounts.
- Preserve keyboard and mouse navigation when changing the terminal UI. Check
  that sensitive fields remain masked and usable in a compact terminal.
- Never commit `config.json`, passwords, session IDs, two-factor codes, account
  lists, message contents, proxy credentials, or Sentry payloads.
- Update the README when setup steps or user-visible behavior changes.

## Tests

Run the complete test suite before opening a pull request:

```console
python -m unittest discover -s tests -v
```

Add or update focused tests when behavior changes. Tests should be deterministic
and must not require a network connection, an Instagram account, or real
credentials.

## Pull requests

1. Branch from `master` and keep the change focused.
2. Use short [Conventional Commit](https://www.conventionalcommits.org/) messages.
3. Describe the problem, the resulting behavior, and how the change was checked.
4. Include tests for changed behavior and documentation for user-facing changes.
5. Confirm that no generated files, local configuration, or secrets are included.

Maintainers handle release versions and publishing unless they explicitly ask a
contributor to do so.
