# chill-out-action

![chill-out-action](https://github.com/dusktreader/chill-out/blob/main/docs/source/images/chill-action-600.png?raw=true)

_Run chill-out in CI to catch zero-day supply chain threats before they land in production._

`chill-out-action` is a composite GitHub Action that wraps the
[chill-out](https://github.com/dusktreader/chill-out) CLI. It reads your lockfile,
asks the registry when each package was published, and fails the job if any entry is
still inside your cooldown window. It can also apply fixes automatically.


## Quick start

```yaml
- uses: dusktreader/chill-out-action@v1
```

That's it. The action auto-detects your ecosystem (Python or npm), installs chill-out
via `uvx`, runs `chill-out check`, and exits non-zero if any cooldown violations are found.


## `check` example

Block a PR if any dependency is too fresh to trust.

```yaml
name: Cooldown check

on:
  pull_request:

jobs:
  chill-out:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dusktreader/chill-out-action@v1
        with:
          command: check
```


## `fix` example

Run on a schedule, pin any violations, and open a PR automatically.

```yaml
name: Cooldown fix

on:
  schedule:
    - cron: "0 9 * * 1"  # every Monday morning
  workflow_dispatch:

jobs:
  chill-out:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: dusktreader/chill-out-action@v1
        with:
          command: fix
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

When violations are found, `fix` creates a `fix/chill-out-<timestamp>` branch, commits
the pinned lockfile to it, and opens a PR against the default branch. If a chill-out fix
PR is already open, it reuses the existing branch and updates it instead.


## Inputs

### Global

| Input              | Default  | Description                                                                           |
| ------------------ | -------- | ------------------------------------------------------------------------------------- |
| `command`          | `check`  | `check` (read-only, fails on violations) or `fix` (pins violations and opens a PR).   |
| `version`          | `latest` | Version of chill-out to use. Accepts any specifier accepted by `uvx` (e.g. `0.1.0`).  |
| `root`             | `.`      | Path to the project root containing the lockfile.                                     |
| `ecosystem`        | _(auto)_ | Force `pypi` or `npm`; auto-detected when omitted.                                    |
| `uv-version`       | `latest` | Version of uv to install (e.g. `0.5.0`).                                              |
| `setup-uv-version` | `v6`     | Version of the `astral-sh/setup-uv` action to use (e.g. `v5`).                        |


### `check`

| Input  | Default | Description                                                                        |
| ------ | ------- | ---------------------------------------------------------------------------------- |
| `fast` | `false` | Skip the safe-version lookup. Faster, but no fix suggestions shown.                |


### `fix`

| Input            | Default     | Description                                                                                                                     |
| ---------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `fix-style`      | _(config)_  | Override the configured [fix style](https://dusktreader.github.io/chill-out/configuration/#fix-style): `exact` or `compatible`. |
| `recheck`        | `true`      | Re-run `check` after applying fixes to confirm they took.                                                                       |
| `cleanup`        | `true`      | Remove expired managed pins before computing fresh fixes.                                                                       |
| `base-branch`    | _(default)_ | Branch the fix PR targets. Defaults to the repository's default branch.                                                         |
| `commit-message` | _(below)_   | Commit message and PR title. Defaults to `fix: pin cooldown violations [chill-out]`.                                            |
| `github-token`   | _(token)_   | Token used to push the fix branch and open the PR. Defaults to `github.token`.                                                  |

----

## Outputs

| Output      | Description                                                                          |
| ----------- | ------------------------------------------------------------------------------------ |
| `exit-code` | Exit code returned by chill-out. `0` means all clear.                                |
| `pr-url`    | URL of the PR opened or updated by a `fix` run. Empty when no violations were found. |


## Exit codes

| Code | Meaning                                                   |
| ---- | --------------------------------------------------------- |
| `0`  | No violations found (or all fixes applied successfully).  |
| `1`  | General error (bad arguments, unreadable lockfile, etc.). |
| `2`  | Cooldown violation detected.                              |


## Configuring cooldown windows

You can configure cooldown windows for chill-out in several ways. See the
[chill-out configuration docs](https://dusktreader.github.io/chill-out/configuration/) for details.


## License

MIT
