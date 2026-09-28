# Changelog

Release notes are based on the repository's tagged releases and commit history.

## 3.0 — 2026-09-28

- **Breaking:** Removed the vendored Instagram client and switched to the
  pinned upstream `instagrapi` package.
- Limited the application to three pinned direct dependencies: `instagrapi`,
  `textual`, and `sentry-sdk`.
- Reorganized the application into dedicated configuration, proxy, Instagram
  service, telemetry, and terminal-interface modules while preserving the root
  compatibility entry points.
- Added a full-screen terminal interface with screen replacement, bottom-docked
  inputs, compact-terminal support, keyboard navigation, and mouse controls.
- Added explicit password or account-file login selection, masked credential
  entry, saved-session reuse, and a dedicated two-factor verification screen.
- Added single-proxy and proxy-list configuration with rotation per recipient
  or after an Instagram error.
- Added first-launch consent and in-app settings for filtered Sentry error
  reporting.
- Added offline automated tests, GitHub Actions validation, and project
  security, contribution, conduct, and licensing documents.
- Removed an unused legacy helper involved in issue #16 by @sabahmax-dev.

## 2.0 — 2022-04-12

- **Breaking:** Replaced the legacy `InstagramAPI` client with a vendored copy
  of `instagrapi` and moved direct messages to its client API.
- Added a menu-driven command-line workflow with message sending, user-list
  collection, updates, and exit actions.
- Added reusable session IDs and persisted recipient lists in `config.json`.
- Added follower and following collection, followed by sending one message to
  every stored user.
- Kept username/password and random `username:password` account-file login
  modes.
- Added Termux installation guidance by @yekdev.
- Pinned the legacy dependency set.
- Applied dependency maintenance updates by @dependabot[bot].

## 1.5-patch — 2021-03-25

- Fixed message status output when a recipient was entered as a numeric user ID.
- Published the same fix under the historical `1.5-patch` and `1.5-patched`
  tags.

## 1.5 — 2021-03-18

- Added a choice between recipient username lookup and direct user-ID entry.
- Reworked the login and sending loops to correct input and control-flow errors.
- Added validation help for numeric user IDs and improved ignored development
  files.

## 1.4 — 2020-12-05

- Simplified installation to the `InstagramAPI` and `urllib3` dependencies.
- Streamlined the message loop and adjusted proxy selection for account-file
  logins.
- Updated the README with the newer demonstration video.

## 1.3 — 2020-10-10

- Added a configurable delay between consecutive messages by @imtheaman.
- Cleaned the bundled legacy Instagram client and reduced its dependency list
  by @404notfound-3.

## 1.2 — 2020-09-11

- Added random account selection from a `username:password` text file by
  @jinxx0.
- Added optional proxy-list support and random proxy selection by @jinxx0.
- Restored recipient lookup by username.
- Masked password entry with `getpass` by @alexanderroquerodrigues.
- Corrected legacy response parsing and prevented infinite loops by
  @alexanderroquerodrigues.
- Added repeated message batches, input validation, and graceful interruption
  with `Ctrl+C`.
- Added `requirements.txt` and corrected additional legacy API errors.

## 1.1 — 2020-08-15

- Added direct numeric recipient-ID entry and simplified the initial sending
  flow by @jinxx0.
- Simplified the message-count prompts.
- Changed recipient resolution from the original search request to the profile
  JSON flow used by the following releases.
- Removed unused optional media imports from the bundled legacy client to avoid
  startup failures.

## 1.0 — 2019-09-26

- Added the initial command-line Instagram message sender.
- Added login with a username and password or an account-list file.
- Added username-to-ID lookup and repeated direct-message sending.
- Bundled the legacy `InstagramAPI` client and documented the original setup
  and demonstration video.
