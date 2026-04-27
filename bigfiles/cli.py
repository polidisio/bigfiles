"""
BigFiles - Interactive CLI tool to find large files on your Mac
"""
import os
import sys
import json
import csv
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

import click

from rich.console import Console

from .finder import BigFilesFinder, FileInfo, FileCategory, format_size, CategoryGroup
from .formatters import (
    create_results_table,
    create_category_summary,
    create_header_panel,
    create_help_panel,
    EnhancedProgress,
    get_theme,
    set_theme,
    Theme,
    detect_dark_mode,
)
from .filters import parse_spotlight_query, apply_filters, filter_to_description
from .notifier import send_scan_complete_notification
console = Console()


async def run_scan(
    directory: str,
    min_size: int,
    max_size: Optional[int],
    extensions: Optional[List[str]],
    exclude: Optional[List[str]],
    sort_by: str,
    limit: int,
    show_bars: bool = True,
    group_by_category: bool = False,
    dark: Optional[bool] = None,
    filters: Optional[List] = None,
    output_format: Optional[str] = None,
    export_file: Optional[str] = None,
    notify: bool = False
):
    """Run the scan and display results"""

    # Set theme
    set_theme(dark)

    # Apply Spotlight filters to extensions if present
    filter_descriptions = []
    if filters:
        for f in filters:
            if f.filter_type.value == "type":
                # Map type filter to extensions
                type_to_exts = {
                    "video": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
                    "image": [".jpg", ".jpeg", ".png", ".gif", ".heic", ".bmp", ".tiff"],
                    "audio": [".mp3", ".wav", ".flac", ".aac", ".m4a"],
                    "document": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"],
                    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
                    "app": [".app", ".ipa", ".xcarchive"],
                    "code": [".py", ".js", ".ts", ".swift", ".java"],
                }
                exts = type_to_exts.get(f.value.lower(), [])
                if exts:
                    extensions = extensions or []
                    extensions.extend(exts)
            filter_descriptions.append(filter_to_description([f]))

    # Build description
    ext_desc = f" [{', '.join(extensions)}]" if extensions else ""
    max_desc = f" - {max_size}MB max" if max_size else ""
    exclude_desc = f" (excl: {', '.join(exclude)})" if exclude else ""
    filter_desc = f" [{', '.join(filter_descriptions)}]" if filter_descriptions else ""

    # Header
    theme = get_theme()
    console.print(create_header_panel(
        directory, min_size, max_size, extensions, exclude,
        sort_by, limit, dark=theme.dark
    ))
    console.print()

    # Scan
    finder = BigFilesFinder(
        directory,
        min_size,
        max_size,
        extensions,
        exclude
    )

    scan_start = asyncio.get_event_loop().time()

    with EnhancedProgress(console) as progress:
        scan_task = asyncio.create_task(finder.scan())

        # Update progress while scanning
        while not scan_task.done():
            await asyncio.sleep(0.1)
            progress.update(
                scanned=finder.total_scanned,
                current_dir=finder.current_directory,
                found_count=len(finder.files),
                found_size=sum(f.size for f in finder.files)
            )

        await scan_task

    scan_duration = asyncio.get_event_loop().time() - scan_start

    # Apply Spotlight filters if any
    if filters:
        filtered_count_before = len(finder.files)
        finder.files = apply_filters(finder.files, filters)
        if finder.files:
            console.print(f"[dim]Filtered: {filtered_count_before} → {len(finder.files)} files[/dim]")

    console.print(f"\n[green]✓[/green] Scanned [bold]{finder.total_scanned:,}[/bold] files in {scan_duration:.1f}s")
    console.print(f"[green]✓[/green] Found [bold]{len(finder.files)}[/bold] files ≥ {min_size} MB{filter_desc}\n")

    if not finder.files:
        console.print("[yellow]No files found matching criteria.[/yellow]")
        return

    # Get results
    results = finder.get_results(sort_by, limit)

    # Handle output formats
    if output_format == "json":
        output_data = [
            {
                "name": f.name,
                "path": f.path,
                "size": f.size,
                "size_human": format_size(f.size),
                "modified": f.modified,
                "extension": f.extension,
                "category": f.category.value,
            }
            for f in results
        ]
        json_str = json.dumps(output_data, indent=2)
        if export_file:
            Path(export_file).write_text(json_str)
            console.print(f"[green]✓[/green] Exported to {export_file}")
        else:
            console.print(json_str)
        return

    elif output_format == "csv":
        if export_file:
            with open(export_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Name", "Path", "Size", "SizeHuman", "Modified", "Extension", "Category"])
                for f in results:
                    writer.writerow([
                        f.name,
                        f.path,
                        f.size,
                        format_size(f.size),
                        f.modified,
                        f.extension,
                        f.category.value,
                    ])
            console.print(f"[green]✓[/green] Exported to {export_file}")
        else:
            console.print("Name,Path,Size,SizeHuman,Modified,Extension,Category")
            for f in results:
                console.print(f"{f.name},{f.path},{f.size},{format_size(f.size)},{f.modified},{f.extension},{f.category.value}")
        return

    # Group by category if requested
    if group_by_category:
        groups = finder.group_by_category()
        console.print(create_category_summary(groups))
        console.print()

    # Display results table
    max_size_in_results = max(f.size for f in results) if results else 0
    table = create_results_table(results, show_bars=show_bars, max_size=max_size_in_results)
    console.print(table)

    # Summary
    total_size = sum(f.size for f in finder.files)
    console.print(
        f"\n[dim]Total: {len(finder.files)} files "
        f"({format_size(total_size)})[/dim]"
    )

    # Notifications
    if notify:
        send_scan_complete_notification(
            scanned_count=finder.total_scanned,
            found_count=len(finder.files),
            total_size=total_size,
            duration_seconds=scan_duration
        )


@click.command()
@click.option(
    "--dir", "-d",
    default=None,
    help="Directory to scan (default: ~)"
)
@click.option(
    "--min", "-m",
    default=None,
    type=int,
    help="Minimum size in MB (default: 100)"
)
@click.option(
    "--max", "-M",
    default=None,
    type=int,
    help="Maximum size in MB (optional)"
)
@click.option(
    "--ext", "-e",
    default=None,
    multiple=True,
    help='Filter by extensions (can use multiple: -e pdf -e zip) or Spotlight types: type:video'
)
@click.option(
    "--exclude", "-x",
    default=None,
    multiple=True,
    help="Exclude paths containing pattern"
)
@click.option(
    "--sort", "-s",
    type=click.Choice(["size", "name", "path", "modified"], case_sensitive=False),
    default=None,
    help="Sort by: size, name, path, modified (default: size)"
)
@click.option(
    "--limit", "-l",
    default=None,
    type=int,
    help="Maximum results to show (default: 50)"
)
@click.option(
    "--simple", "-S",
    is_flag=True,
    help="Simple list output (no formatting)"
)
@click.option(
    "--no-exclude-dirs",
    is_flag=True,
    help="Don't exclude common directories (.git, Caches, etc.)"
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Interactive TUI mode"
)
@click.option(
    "--notify",
    is_flag=True,
    help="Send notification when scan completes"
)
@click.option(
    "--output", "-o",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (json or csv)"
)
@click.option(
    "--export",
    "export_file",
    default=None,
    help="Export results to file (with --output)"
)
@click.option(
    "--group",
    is_flag=True,
    help="Group results by category"
)
@click.option(
    "--no-bars",
    is_flag=True,
    help="Hide size bars"
)
@click.option(
    "--dark",
    is_flag=True,
    help="Force dark mode"
)
@click.option(
    "--light",
    is_flag=True,
    help="Force light mode"
)
@click.option(
    "--filter", "-F",
    "filters",
    default=None,
    multiple=True,
    help="Spotlight-style filters: type:video, larger:1GB, newer:30d, name:backup"
)
def cli(
    dir: Optional[str],
    min: Optional[int],
    max: Optional[int],
    ext: tuple,
    exclude: tuple,
    sort: Optional[str],
    limit: Optional[int],
    simple: bool = False,
    no_exclude_dirs: bool = False,
    interactive: bool = False,
    notify: bool = False,
    output: Optional[str] = None,
    export_file: Optional[str] = None,
    group: bool = False,
    no_bars: bool = False,
    dark: bool = False,
    light: bool = False,
    filters: tuple = ()
):
    """
    🔍 BIGFILES - Find large files on your Mac

    Run without arguments to see help menu.

    Examples:

        bigfiles                    Show this help menu
        bigfiles -d ~/Downloads     Scan Downloads folder
        bigfiles -m 500             Files > 500MB
        bigfiles -m 100 -M 1000     Files between 100-1000MB
        bigfiles -e pdf -e zip     Only PDF and ZIP files
        bigfiles -s modified       Sort by date modified
        bigfiles -x node_modules    Exclude paths with 'node_modules'
        bigfiles --interactive      Interactive TUI mode
        bigfiles --notify           Send notification on completion
        bigfiles --output json      Output as JSON
    """

    # Determine theme
    theme_dark = None
    if dark:
        theme_dark = True
    elif light:
        theme_dark = False

    # Parse Spotlight-style filters
    spotlight_filters = []
    for f in filters:
        parsed = parse_spotlight_query(f)
        spotlight_filters.extend(parsed)

    # Show welcome/help if no arguments provided
    if (dir is None and min is None and max is None and not ext and not exclude
        and sort is None and limit is None and not interactive
        and not output and not filters):
        theme = get_theme(theme_dark)
        console.print(create_help_panel(dark=theme.dark))
        console.print()
        return

    # Use defaults for None values
    if min is None:
        min = 100
    if sort is None:
        sort = "size"
    if limit is None:
        limit = 50
    if dir is None:
        dir = "~"

    # Convert tuples to lists
    extensions = list(ext) if ext else None
    exclude_list = list(exclude) if exclude else None

    directory = Path(dir).expanduser().resolve()

    if not directory.exists():
        console.print(f"[red]✗[/red] Directory not found: {directory}")
        sys.exit(1)

    # Check for interactive mode
    if interactive:
        try:
            from .tui import run_tui
            asyncio.run(run_tui(
                directory=str(directory),
                min_size=min,
                max_size=max,
                extensions=extensions,
                exclude=exclude_list,
                sort_by=sort,
                limit=limit,
                dark=theme_dark,
                notify=notify
            ))
        except ImportError:
            console.print("[yellow]Interactive mode requires textual library.[/yellow]")
            console.print("Install with: pip install bigfiles[interactive]")
            sys.exit(1)
        return

    if simple:
        # Simple list mode
        console.print(f"Scanning {directory}...")
        finder = BigFilesFinder(
            str(directory),
            min,
            max,
            extensions,
            exclude_list
        )
        asyncio.run(finder.scan())
        results = finder.get_results(sort, limit)

        # Apply filters if any
        if spotlight_filters:
            results = apply_filters(results, spotlight_filters)

        for i, f in enumerate(results, 1):
            print(f"{i}. {format_size(f.size).strip():>10} {f.path}")
    else:
        # Rich interactive mode
        asyncio.run(run_scan(
            str(directory),
            min,
            max,
            extensions,
            exclude_list,
            sort,
            limit,
            show_bars=not no_bars,
            group_by_category=group,
            dark=theme_dark,
            filters=spotlight_filters,
            output_format=output,
            export_file=export_file,
            notify=notify
        ))


def run():
    cli()


if __name__ == "__main__":
    run()
