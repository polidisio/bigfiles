"""
BigFiles - Interactive CLI tool to find large files on your Mac
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import asyncio
import fnmatch

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box
import click


console = Console()


@dataclass
class FileInfo:
    path: str
    size: int
    is_dir: bool
    modified: float


class BigFilesFinder:
    def __init__(
        self,
        directory: str,
        min_size_mb: int = 100,
        max_size_mb: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        exclude_dirs: bool = True
    ):
        self.directory = Path(directory).expanduser().resolve()
        self.min_size_bytes = min_size_mb * 1024 * 1024
        self.max_size_bytes = max_size_mb * 1024 * 1024 if max_size_mb else None
        self.extensions = [ext.lower() for ext in (extensions or [])]
        self.exclude_patterns = exclude_patterns or []
        self.exclude_dirs = exclude_dirs
        self.files: list[FileInfo] = []
        self.total_scanned = 0
        self.is_running = True

        # Default directories to skip
        self.default_excludes = [
            '.git', 'node_modules', '__pycache__', '.cache', 'Caches',
            '.npm', '.pip', '.cargo', 'vendor', '.cocoapods'
        ]

    def should_exclude(self, path: str) -> bool:
        """Check if path matches any exclude pattern"""
        path_lower = path.lower()
        
        # Check default excludes
        for exclude in self.default_excludes:
            if exclude in path_lower:
                return True
        
        # Check custom patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path_lower, f"*{pattern.lower()}*"):
                return True
        
        return False

    async def scan(self):
        """Scan directory for files matching criteria"""
        try:
            for root, dirs, filenames in os.walk(self.directory):
                if not self.is_running:
                    break
                
                # Skip hidden dirs and common cache dirs
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith('.')
                    and d not in self.default_excludes
                ]
                
                self.total_scanned += len(filenames)
                
                for filename in filenames:
                    if not self.is_running:
                        break
                    filepath = Path(root) / filename
                    try:
                        stat = filepath.stat()
                        
                        # Skip files matching exclude patterns
                        if self.should_exclude(str(filepath)):
                            continue
                        
                        # Check size constraints
                        if stat.st_size < self.min_size_bytes:
                            continue
                        if self.max_size_bytes and stat.st_size > self.max_size_bytes:
                            continue
                        
                        # Check extension filter
                        if self.extensions:
                            ext = filepath.suffix.lower()
                            if ext not in self.extensions and ext.lstrip('.') not in self.extensions:
                                if not any(ext == f".{e.lstrip('.')}" for e in self.extensions):
                                    continue
                        
                        self.files.append(FileInfo(
                            path=str(filepath),
                            size=stat.st_size,
                            is_dir=False,
                            modified=stat.st_mtime
                        ))
                    except (OSError, PermissionError):
                        pass
        except PermissionError:
            pass

    def stop(self):
        self.is_running = False

    def get_results(self, sort_by: str = "size", limit: int = 50) -> list[FileInfo]:
        """Get sorted results"""
        if sort_by == "size":
            self.files.sort(key=lambda x: x.size, reverse=True)
        elif sort_by == "name":
            self.files.sort(key=lambda x: x.name.lower())
        elif sort_by == "path":
            self.files.sort(key=lambda x: x.path.lower())
        elif sort_by == "modified":
            self.files.sort(key=lambda x: x.modified, reverse=True)
        
        return self.files[:limit]

    def format_size(self, size: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


def format_size(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def get_file_icon(path: str) -> str:
    """Get icon based on file extension"""
    ext = Path(path).suffix.lower()
    icons = {
        '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬', '.wmv': '🎬',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.heic': '🖼️',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.aac': '🎵', '.m4a': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        '.dmg': '💿', '.iso': '💿', '.img': '💿',
        '.pdf': '📄', '.doc': '📄', '.docx': '📄', '.txt': '📄', '.xls': '📄', '.xlsx': '📄',
        '.sql': '🗄️', '.db': '🗄️', '.sqlite': '🗄️', '.mdb': '🗄️',
        '.xcarchive': '📱', '.app': '📱', '.ipa': '📱',
        '.vm': '🖥️', '.vmdk': '🖥️', '.vdi': '🖥️', '.parallels': '🖥️',
        '.psd': '🎨', '.ai': '🎨', '.sketch': '🎨', '.fig': '🎨',
        '.py': '🐍', '.js': '📜', '.ts': '📜', '.java': '📜', '.swift': '📜',
        '.log': '📋', '.json': '📋', '.xml': '📋', '.csv': '📋',
    }
    return icons.get(ext, '📄')


async def run_scan(
    directory: str,
    min_size: int,
    max_size: Optional[int],
    extensions: Optional[List[str]],
    exclude: Optional[List[str]],
    sort_by: str,
    limit: int
):
    """Run the scan and display results"""
    
    console.clear()
    
    # Build description
    ext_desc = f" [{', '.join(extensions)}]" if extensions else ""
    max_desc = f" - {max_size}MB max" if max_size else ""
    exclude_desc = f" (excl: {', '.join(exclude)})" if exclude else ""
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]🔍 BIGFILES[/bold cyan] - Large File Finder\n"
        f"[dim]Directory:[/dim] {directory}\n"
        f"[dim]Size:[/dim] > {min_size}MB{max_desc}{ext_desc}{exclude_desc}\n"
        f"[dim]Sort:[/dim] {sort_by} | [dim]Limit:[/dim] {limit}",
        border_style="cyan",
        box=box.DOUBLE
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
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning...", total=None)
        
        scan_task = asyncio.create_task(finder.scan())
        
        # Update progress while scanning
        last_count = 0
        while not scan_task.done():
            await asyncio.sleep(0.1)
            if finder.total_scanned != last_count:
                progress.update(
                    task,
                    description=f"[cyan]Files scanned: {finder.total_scanned:,}"
                )
                last_count = finder.total_scanned
        
        await scan_task
    
    console.print(f"\n[green]✓[/green] Scanned [bold]{finder.total_scanned:,}[/bold] files")
    console.print(f"[green]✓[/green] Found [bold]{len(finder.files)}[/bold] files ≥ {min_size} MB\n")
    
    if not finder.files:
        console.print("[yellow]No files found matching criteria.[/yellow]")
        return
    
    # Display results
    results = finder.get_results(sort_by, limit)
    
    table = Table(
        title=f"📊 Top {len(results)} largest files",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("File", style="white")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Type", justify="center", style="dim", width=6)
    
    for i, file in enumerate(results, 1):
        icon = get_file_icon(file.path)
        name = Path(file.path).name
        parent = Path(file.path).parent.name
        ext = Path(file.path).suffix.upper() or "FILE"
        size_str = format_size(file.size)
        display_path = f"{icon} {parent}/{name}"
        table.add_row(str(i), display_path, size_str, ext.lstrip('.'))
    
    console.print(table)
    
    # Summary
    total_size = sum(f.size for f in finder.files)
    console.print(
        f"\n[dim]Total: {len(finder.files)} files "
        f"({format_size(total_size)})[/dim]"
    )


@click.command()
@click.option(
    '--dir', '-d',
    default=None,
    help='Directory to scan (default: ~)'
)
@click.option(
    '--min', '-m',
    default=None,
    type=int,
    help='Minimum size in MB (default: 100)'
)
@click.option(
    '--max', '-M',
    default=None,
    type=int,
    help='Maximum size in MB (optional)'
)
@click.option(
    '--ext', '-e',
    default=None,
    multiple=True,
    help='Filter by extensions (can use multiple: -e pdf -e zip)'
)
@click.option(
    '--exclude', '-x',
    default=None,
    multiple=True,
    help='Exclude paths containing pattern'
)
@click.option(
    '--sort', '-s',
    type=click.Choice(['size', 'name', 'path', 'modified'], case_sensitive=False),
    default=None,
    help='Sort by: size, name, path, modified (default: size)'
)
@click.option(
    '--limit', '-l',
    default=None,
    type=int,
    help='Maximum results to show (default: 50)'
)
@click.option(
    '--simple', '-S',
    is_flag=True,
    help='Simple list output (no formatting)'
)
@click.option(
    '--no-exclude-dirs',
    is_flag=True,
    help='Don\'t exclude common directories (.git, Caches, etc.)'
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
    no_exclude_dirs: bool = False
):
    """
    🔍 BIGFILES - Find large files on your Mac
    
    Run without arguments to see help menu.
    
    Examples:
    
        bigfiles                    Show this help menu
        bigfiles -d ~/Downloads     Scan Downloads folder
        bigfiles -m 500             Files > 500MB
        bigfiles -m 100 -M 1000    Files between 100-1000MB
        bigfiles -e pdf -e zip     Only PDF and ZIP files
        bigfiles -s modified       Sort by date modified
        bigfiles -x node_modules    Exclude paths with 'node_modules'
    """
    # Show welcome/help if no arguments provided
    if dir is None and min is None and max is None and not ext and not exclude and sort is None and limit is None:
        console.print(Panel.fit(
            """[bold cyan]🔍 BIGFILES[/bold cyan] - Large File Finder

[yellow]USAGE:[/yellow]

    bigfiles [OPTIONS]

[yellow]OPTIONS:[/yellow]

    [dim]-d, --dir DIR[/dim]        Directory to scan (default: ~)
    [dim]-m, --min MB[/dim]         Minimum size in MB (default: 100)
    [dim]-M, --max MB[/dim]         Maximum size in MB (optional)
    [dim]-e, --ext EXT[/dim]        Filter by extension(s) (can repeat)
    [dim]-x, --exclude PATTERN[/dim] Exclude paths containing pattern
    [dim]-s, --sort FIELD[/dim]     Sort by: size, name, path, modified
    [dim]-l, --limit N[/dim]        Max results to show (default: 50)
    [dim]-S, --simple[/dim]         Simple list output
    [dim]-h, --help[/dim]            Show this help menu

[yellow]EXAMPLES:[/yellow]

    [green]bigfiles[/green]                      Show this help
    [green]bigfiles -d ~/Downloads[/green]        Scan Downloads
    [green]bigfiles -m 1000[/green]              Files > 1GB
    [green]bigfiles -m 100 -M 500[/green]        Files 100-500MB
    [green]bigfiles -e pdf -e docx[/green]       Only documents
    [green]bigfiles -e mp4 -e mov[/green]         Only videos
    [green]bigfiles -s modified -l 20[/green]    Top 20 by date
    [green]bigfiles -x node_modules -x .git[/green]  Exclude patterns

[yellow]AUTO-EXCLUDED:[/yellow]

    .git, node_modules, __pycache__, Caches, .cache, vendor

[yellow]TIPS:[/yellow]

    • Combine filters: bigfiles -m 50 -e pdf -e zip
    • Sort by date: bigfiles -s modified
    • Find old files: bigfiles -s modified -l 10""",
            border_style="cyan",
            box=box.DOUBLE
        ))
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
        for i, f in enumerate(results, 1):
            print(f"{i}. {format_size(f.size).strip():>10} {f.path}")
    else:
        # Interactive mode
        asyncio.run(run_scan(
            str(directory),
            min,
            max,
            extensions,
            exclude_list,
            sort,
            limit
        ))


def run():
    cli()


if __name__ == '__main__':
    run()
