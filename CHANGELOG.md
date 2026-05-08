# Changelog

## 1.0.0 — 2026-05-08

### Added

- Initial release of `chill-out-action` as a composite GitHub Action.
- `check` command:
  - audits the lockfile
  - fails the job if any package is inside the cooldown window.
- `fix` command:
  - pins violating packages to the newest safe version
  - commits to a `fix/chill-out-<timestamp>` branch
  - opens a PR against the default branch
  - reuses an existing fix PR if one is already open.
