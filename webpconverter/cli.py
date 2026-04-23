"""CLI entry-point for webpconverter.

Commands
--------
  webpconverter plan  [--dir PATH] [--quality INT] [--output-dir PATH]
  webpconverter exec  PLAN_FILE
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich import box

from .converter import convert_file
from .planner import load_plan, write_plan
from .reporter import write_report
from .scanner import scan

console = Console()


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="webpconverter")
def main() -> None:
    """webpconverter — convert PNG and JPEG assets to optimized WebP."""


# ---------------------------------------------------------------------------
# plan sub-command
# ---------------------------------------------------------------------------

@main.command("plan")
@click.option(
    "--dir", "-d",
    "scan_dir",
    default=".",
    show_default=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Root directory to scan for image assets.",
)
@click.option(
    "--quality", "-q",
    default=85,
    show_default=True,
    type=click.IntRange(1, 100),
    help="WebP quality (1–100). 85 is an excellent balance of size and fidelity.",
)
@click.option(
    "--output-dir", "-o",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Where to write the plan file (default: current directory).",
)
def plan_cmd(scan_dir: Path, quality: int, output_dir: Path | None) -> None:
    """Scan a directory and generate a conversion plan markdown file."""

    console.print(Panel.fit(
        "[bold cyan]webpconverter[/bold cyan] — plan",
        subtitle=f"scanning [green]{scan_dir.resolve()}[/green]",
    ))

    with console.status("[bold]Scanning for image assets…[/bold]"):
        assets = scan(scan_dir)

    if not assets:
        console.print("[yellow]No convertible image files found.[/yellow]")
        raise SystemExit(0)

    console.print(f"[green]Found {len(assets)} file(s)[/green]")

    # Preview table
    table = Table(box=box.SIMPLE_HEAVY, show_footer=False)
    table.add_column("#", style="dim", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Type", justify="center")
    table.add_column("Size", justify="right")

    for idx, asset in enumerate(assets, start=1):
        kb = asset.size_bytes / 1024
        size_str = f"{kb:.1f} KB" if kb < 1024 else f"{kb / 1024:.2f} MB"
        table.add_row(str(idx), str(asset.path), asset.format_label, size_str)

    console.print(table)

    plan_path = write_plan(
        assets=assets,
        quality=quality,
        root=scan_dir.resolve(),
        output_dir=output_dir,
    )

    console.print(
        f"\n[bold green]Plan written:[/bold green] [cyan]{plan_path}[/cyan]"
    )
    console.print(
        f"\nRun [bold]webpconverter exec {plan_path.name}[/bold] to perform the conversions."
    )


# ---------------------------------------------------------------------------
# exec sub-command
# ---------------------------------------------------------------------------

@main.command("exec")
@click.argument(
    "plan_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def exec_cmd(plan_file: Path) -> None:
    """Execute conversions listed in PLAN_FILE."""

    console.print(Panel.fit(
        "[bold cyan]webpconverter[/bold cyan] — exec",
        subtitle=f"plan: [green]{plan_file.name}[/green]",
    ))

    try:
        file_paths, quality = load_plan(plan_file)
    except ValueError as exc:
        console.print(f"[bold red]Error reading plan:[/bold red] {exc}")
        raise SystemExit(1)

    if not file_paths:
        console.print("[yellow]Plan file contains no files to convert.[/yellow]")
        raise SystemExit(0)

    console.print(
        f"[green]{len(file_paths)} file(s)[/green] to convert at "
        f"quality [bold]{quality}[/bold]"
    )

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Converting…", total=len(file_paths))

        for path_str in file_paths:
            src = Path(path_str)
            progress.update(task, description=f"[cyan]{src.name}")
            result = convert_file(src, quality=quality)
            results.append(result)
            progress.advance(task)

    # Summary table
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    summary = Table(box=box.SIMPLE_HEAVY, show_footer=False, title="Conversion Summary")
    summary.add_column("File", style="cyan")
    summary.add_column("Status", justify="center")
    summary.add_column("Before", justify="right")
    summary.add_column("After", justify="right")
    summary.add_column("Saving", justify="right", style="green")

    def _kb(b: int) -> str:
        kb = b / 1024
        return f"{kb:.1f} KB" if kb < 1024 else f"{kb / 1024:.2f} MB"

    for r in results:
        if r.success:
            if r.saving_pct < 0:
                saving_cell = f"[yellow]+{abs(r.saving_pct):.1f}% larger[/yellow]"
            else:
                saving_cell = f"{r.saving_pct:.1f}%"
            summary.add_row(
                r.source_path.name,
                "[green]OK[/green]",
                _kb(r.original_bytes),
                _kb(r.converted_bytes),
                saving_cell,
            )
        else:
            summary.add_row(
                r.source_path.name,
                "[red]FAIL[/red]",
                _kb(r.original_bytes),
                "—",
                f"[red]{r.error[:60]}[/red]",
            )

    console.print(summary)

    report_path = write_report(
        results=results,
        plan_path=plan_file,
        quality=quality,
    )

    if succeeded:
        total_orig = sum(r.original_bytes for r in succeeded)
        total_conv = sum(r.converted_bytes for r in succeeded)
        total_pct = (total_orig - total_conv) / total_orig * 100 if total_orig else 0
        console.print(
            f"\n[bold green]Done![/bold green] "
            f"{len(succeeded)} converted, {len(failed)} failed. "
            f"Total saving: [bold]{total_pct:.1f}%[/bold] "
            f"([cyan]{_kb(total_orig - total_conv)}[/cyan])"
        )
    else:
        console.print("\n[bold red]All conversions failed.[/bold red]")

    console.print(
        f"\n[bold green]Report written:[/bold green] [cyan]{report_path}[/cyan]"
    )
