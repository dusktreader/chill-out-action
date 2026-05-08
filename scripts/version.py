#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich", "typer"]
# ///

import enum
import re
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.rule import Rule


console = Console()
app = typer.Typer(
    help=__doc__,
    add_completion=False,
    no_args_is_help=True,
)

ACTION_YML   = Path(__file__).parent.parent / "action.yml"
CHANGELOG_MD = Path(__file__).parent.parent / "CHANGELOG.md"
VERSION_RE   = re.compile(r"^(#\s*version:\s*)(\d+\.\d+\.\d+)", re.MULTILINE)
# Matches a Keep-a-Changelog-style level-2 heading whose first token is a version
# number, e.g. "## 1.0.0" or "## 1.0.0 — 2026-05-08".
ENTRY_RE     = re.compile(r"^##\s+(\d+\.\d+\.\d+)", re.MULTILINE)


class BumpType(str, enum.Enum):
    major = "major"
    minor = "minor"
    patch = "patch"


def _read_version(action_yml: Path) -> str:
    m = VERSION_RE.search(action_yml.read_text())
    if not m:
        console.print("[red]error:[/red] no [bold]# version: X.Y.Z[/bold] comment found in action.yml")
        raise typer.Exit(1)
    return m.group(2)


def _bump_version(version: str, bump_type: BumpType) -> str:
    major, minor, patch = (int(p) for p in version.split("."))
    if bump_type == BumpType.major:
        return f"{major + 1}.0.0"
    elif bump_type == BumpType.minor:
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def _run(cmd: list[str], *, dry_run: bool = False) -> str:
    console.print(f"  [dim]$ {' '.join(cmd)}[/dim]")
    if dry_run:
        return ""
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _extract_release_notes(version: str) -> str:
    """
    Extract the body of the changelog entry for the given version.

    Finds the level-2 heading whose first token matches `version`, then returns
    everything up to (but not including) the next level-2 heading or EOF.
    """
    if not CHANGELOG_MD.exists():
        return ""

    text = CHANGELOG_MD.read_text()
    matches = list(ENTRY_RE.finditer(text))

    for i, m in enumerate(matches):
        if m.group(1) != version:
            continue
        body_start = m.end()
        body_end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        return text[body_start:body_end].strip()

    return ""


@app.command()
def bump(
    bump_type: Annotated[
        BumpType,
        typer.Option("--type", help="Part of the version to increment.", show_default=False),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print what would change without writing anything."),
    ] = False,
) -> None:
    """Increment the version in action.yml."""
    text    = ACTION_YML.read_text()
    current = _read_version(ACTION_YML)
    next_v  = _bump_version(current, bump_type)

    console.print(Rule("chill-out-action bump"))
    console.print(f"  type    : [bold cyan]{bump_type.value}[/bold cyan]")
    console.print(f"  current : [dim]{current}[/dim]")
    console.print(f"  next    : [bold green]{next_v}[/bold green]")
    if dry_run:
        console.print("\n  [yellow]dry-run — action.yml will not be modified[/yellow]")
    console.print()

    if not dry_run:
        new_text = VERSION_RE.sub(lambda m: f"{m.group(1)}{next_v}", text)
        ACTION_YML.write_text(new_text)
        console.print("  [green]✓[/green] updated action.yml")

    console.print()
    console.print(Rule())
    if dry_run:
        console.print("[yellow]dry-run complete — nothing was written[/yellow]")
    else:
        console.print(f"[green]bumped {current} → {next_v}[/green]")


@app.command()
def publish(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print what would happen without making any changes."),
    ] = False,
) -> None:
    """Tag the release, push, and create the GitHub release from CHANGELOG.md."""
    version    = _read_version(ACTION_YML)
    semver_tag = f"v{version}"
    major_tag  = f"v{version.split('.')[0]}"

    console.print(Rule("chill-out-action release"))
    console.print(f"  version : [bold cyan]{version}[/bold cyan]")
    console.print(f"  tag     : [bold]{semver_tag}[/bold]")
    console.print(f"  floating: [bold]{major_tag}[/bold]")
    if dry_run:
        console.print("\n  [yellow]dry-run — nothing will be written or pushed[/yellow]")
    console.print()

    notes = _extract_release_notes(version)
    if notes:
        console.print("  [green]✓[/green] found release notes in CHANGELOG.md")
    else:
        console.print(
            f"  [red]error:[/red] no changelog entry found for {version}\n"
            f"  Add a '## {version}' section to CHANGELOG.md before publishing."
        )
        raise typer.Exit(1)

    try:
        _run(["git", "tag", semver_tag], dry_run=dry_run)
        console.print(f"  [green]✓[/green] created tag [bold]{semver_tag}[/bold]")

        _run(["git", "tag", "-f", major_tag], dry_run=dry_run)
        console.print(f"  [green]✓[/green] updated floating tag [bold]{major_tag}[/bold]")

        _run(["git", "push", "origin", semver_tag, major_tag, "--force"], dry_run=dry_run)
        console.print("  [green]✓[/green] pushed tags to origin")

        _run(
            ["gh", "release", "create", semver_tag, "--title", semver_tag, "--notes", notes, "--latest"],
            dry_run=dry_run,
        )
        console.print(f"  [green]✓[/green] created GitHub release [bold]{semver_tag}[/bold]")

    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]error:[/red] {e.stderr.strip() or e}")
        raise typer.Exit(1)

    console.print()
    console.print(Rule())
    if dry_run:
        console.print("[yellow]dry-run complete — nothing was changed[/yellow]")
    else:
        console.print(f"[green]released {semver_tag}[/green]")


if __name__ == "__main__":
    app()
