# Security Policy

## Supported versions

Security fixes are applied to the current `master` branch and the latest
release only. Older versions are not maintained.

| Version | Supported |
| --- | --- |
| Current `master` / latest release | Yes |
| Older versions | No |

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose users,
credentials, sessions, or private data.

Use [GitHub private vulnerability reporting][private-report] when it is
available. If it is unavailable, contact the maintainer through a private
contact method listed on the [Gumbraise GitHub profile][maintainer]. Include:

- the affected version or commit;
- the steps required to reproduce the issue;
- the expected and observed behavior;
- the security impact and any suggested mitigation.

Never include real Instagram passwords, session IDs, two-factor codes, account
lists, message contents, proxy credentials, Sentry data, or other secrets in a
report. Replace them with clearly marked test values.

The maintainers will review the report, confirm its scope, and coordinate a fix
and disclosure with the reporter. Please allow time for a patch before sharing
the vulnerability publicly.

For ordinary bugs and feature requests, use the public [issue tracker][issues].

[private-report]: https://github.com/Gumbraise/instagram-bomber/security/advisories/new
[maintainer]: https://github.com/Gumbraise
[issues]: https://github.com/Gumbraise/instagram-bomber/issues
