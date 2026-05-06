# Security Policy

## API keys

Do not paste real J-Quants API keys into GitHub issues, pull requests, CI logs, screenshots, or test fixtures.

`jrr` accepts API keys in three ways:

- `JQUANTS_API_KEY`
- local config written by `jrr config set-api-key` or `jrr rank --save-api-key`
- hidden terminal prompt or TUI input

The TUI uses an entered API key only for the current session and does not save it. Saved config files are written with user-only permissions where the operating system supports it.

## Reporting vulnerabilities

Open a GitHub issue with a minimal reproduction and redact secrets from all logs. If the report contains a real secret, rotate that key before sharing any details.
