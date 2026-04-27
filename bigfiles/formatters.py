"""
BigFiles - Output formatters using Rich
Contains progress HUD, size bars, and styled tables
"""
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.text import Text
from rich.style import Style
from rich import box

from .finder import FileInfo, BigFilesFinder, CategoryGroup, FileCategory


# Color palette for size bars
SIZE_BAR_COLORS = {
    "normal": "blue",
    "advisory": "yellow",
    "large": "red",
}

# macOS-like accent colors
COLORS_LIGHT = {
    "bg": "#FFFFFF",
    "surface": "#F5F5F7",
    "accent": "#007AFF",
    "text": "#1D1D1F",
    "dim": "#86868B",
    "border": "#D2D2D7",
}

COLORS_DARK = {
    "bg": "#1E1E1E",
    "surface": "#2D2D2D",
    "accent": "#007AFF",
    "text": "#FFFFFF",
    "dim": "#8E8E93",
    "border": "#48484A",
}


def detect_dark_mode() -> bool:
    """Detect if terminal is in dark mode"""
    # Check COLORTERM environment variable
    colorterm = os.getenv("COLORTERM", "").lower()
    if "dark" in colorterm or colorterm == "truecolor":
        return True

    # Check for common dark terminal signatures
    term = os.getenv("TERM", "").lower()
    if "dark" in term:
        return True

    # Check Apple_Terminal or iTerm
    term_program = os.getenv("TERM_PROGRAM", "").lower()
    if term_program in ("apple terminal", "iterm.app"):
        # Try to detect via TERM_SESSION_ID (Apple Terminal)
        if os.getenv("TERM_SESSION_ID"):
            return False  # Apple Terminal uses system appearance

    # Fallback: check for dark background in LS_COLORS or use heuristics
    # Heuristic: if most text is light-on-dark or if we're on macOS dark mode
    if sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            if "Dark" in result.stdout:
                return True
        except Exception:
            pass

    return False


class Theme:
    def __init__(self, dark: Optional[bool] = None):
        self.dark = dark if dark is not None else detect_dark_mode()
        self.colors = COLORS_DARK if self.dark else COLORS_LIGHT

    @property
    def primary(self) -> str:
        return self.colors["accent"]

    @property
    def text(self) -> str:
        return self.colors["text"]

    @property
    def dim(self) -> str:
        return self.colors["dim"]

    @property
    def surface(self) -> str:
        return self.colors["surface"]

    @property
    def border(self) -> str:
        return self.colors["border"]


# Global theme instance
_theme: Optional[Theme] = None


def get_theme(dark: Optional[bool] = None) -> Theme:
    global _theme
    if dark is not None:
        _theme = Theme(dark)
    if _theme is None:
        _theme = Theme()
    return _theme


def set_theme(dark: Optional[bool] = None):
    global _theme
    _theme = Theme(dark)


def get_size_bar_color(size_bytes: int) -> str:
    """Get color for size bar based on file size"""
    size_mb = size_bytes / (1024 * 1024)
    if size_mb >= 1024:  # >= 1GB
        return SIZE_BAR_COLORS["large"]
    elif size_mb >= 100:  # >= 100MB
        return SIZE_BAR_COLORS["advisory"]
    return SIZE_BAR_COLORS["normal"]


def create_size_bar(size_bytes: int, max_size_bytes: int, width: int = 30) -> str:
    """Create a horizontal size bar"""
    if max_size_bytes <= 0:
        return " " * width

    ratio = min(size_bytes / max_size_bytes, 1.0)
    filled = int(ratio * width)
    color = get_size_bar_color(size_bytes)

    return f"[{color}]{'█' * filled}[/{color}]{'░' * (width - filled)}"


def create_size_bar_inline(size_bytes: int, max_size_bytes: int, width: int = 20) -> Text:
    """Create inline size bar with proper Rich styling"""
    if max_size_bytes <= 0:
        return Text("░" * width, style="dim")

    ratio = min(size_bytes / max_size_bytes, 1.0)
    filled = int(ratio * width)
    color = get_size_bar_color(size_bytes)

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    return bar


def format_file_row(
    file: FileInfo,
    index: int,
    max_size: int,
    show_bars: bool = True
) -> Dict:
    """Format a file for table display"""
    theme = get_theme()
    icon = get_file_icon(file.path)
    name = file.name
    parent = file.parent_name
    size_str = BigFilesFinder.format_size(file.size)
    ext = file.extension.upper() or "FILE"

    display_path = f"{icon} {parent}/{name}"

    row = {
        "#": str(index),
        "File": display_path,
        "Size": size_str,
        "Type": ext.lstrip("."),
    }

    if show_bars:
        row["Bar"] = create_size_bar_inline(file.size, max_size)

    return row


def get_file_icon(path: str) -> str:
    """Get icon based on file extension"""
    ext = Path(path).suffix.lower()
    icons = {
        ".mp4": "🎬", ".mov": "🎬", ".avi": "🎬", ".mkv": "🎬", ".wmv": "🎬",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️", ".heic": "🖼️",
        ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".aac": "🎵", ".m4a": "🎵",
        ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦", ".gz": "📦",
        ".dmg": "💿", ".iso": "💿", ".img": "💿",
        ".pdf": "📄", ".doc": "📄", ".docx": "📄", ".txt": "📄",
        ".xls": "📄", ".xlsx": "📄", ".ppt": "📄", ".pptx": "📄",
        ".sql": "🗄️", ".db": "🗄️", ".sqlite": "🗄️", ".mdb": "🗄️",
        ".xcarchive": "📱", ".app": "📱", ".ipa": "📱",
        ".vm": "🖥️", ".vmdk": "🖥️", ".vdi": "🖥️",
        ".psd": "🎨", ".ai": "🎨", ".sketch": "🎨", ".fig": "🎨",
        ".py": "🐍", ".js": "📜", ".ts": "📜", ".java": "📜", ".swift": "📜",
        ".log": "📋", ".json": "📋", ".xml": "📋", ".csv": "📋",
    }
    return icons.get(ext, "📄")


def create_results_table(
    files: List[FileInfo],
    show_bars: bool = True,
    max_size: Optional[int] = None
) -> Table:
    """Create a Rich table with results and optional size bars"""
    theme = get_theme()

    if max_size is None and files:
        max_size = max(f.size for f in files)

    table = Table(
        title="📊 Top files by size",
        box=box.ROUNDED,
        show_header=True,
        header_style=f"bold {theme.primary}",
        border_style=theme.border,
        style=theme.text,
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("File", style=theme.text)
    table.add_column("Size", justify="right", style="yellow")
    if show_bars:
        table.add_column("Size Bar", style=theme.dim, width=22)
    table.add_column("Type", justify="center", style=theme.dim, width=6)

    for i, file in enumerate(files, 1):
        icon = get_file_icon(file.path)
        name = file.name
        parent = file.parent_name
        ext = file.extension.upper() or "FILE"
        size_str = BigFilesFinder.format_size(file.size)
        display_path = f"{icon} [link={file.path}]{parent}/{name}[/link]"

        if show_bars:
            bar = create_size_bar_inline(file.size, max_size)
            table.add_row(str(i), display_path, size_str, bar, ext.lstrip("."))
        else:
            table.add_row(str(i), display_path, size_str, ext.lstrip("."))

    return table


def create_category_summary(groups: Dict[FileCategory, CategoryGroup]) -> Table:
    """Create a summary table grouped by category"""
    theme = get_theme()

    # Sort by total size
    sorted_groups = sorted(groups.values(), key=lambda g: g.total_size, reverse=True)

    # Calculate max size for bars
    max_total = max(g.total_size for g in sorted_groups) if sorted_groups else 0

    table = Table(
        title="📁 Files by Category",
        box=box.ROUNDED,
        show_header=True,
        header_style=f"bold {theme.primary}",
        border_style=theme.border,
    )

    table.add_column("Category", style=theme.text)
    table.add_column("Files", justify="right", style=theme.dim)
    table.add_column("Total Size", justify="right", style="yellow")
    table.add_column("Proportion", style=theme.dim, width=25)

    for group in sorted_groups:
        icon = group.icon
        label = group.label
        count = len(group.files)
        size_str = BigFilesFinder.format_size(group.total_size)
        bar = create_size_bar_inline(group.total_size, max_total, width=20)

        table.add_row(f"{icon} {label}", str(count), size_str, bar)

    return table


class EnhancedProgress:
    """Enhanced progress display with macOS-style HUD"""

    def __init__(self, console: Console):
        self.console = console
        self.progress: Optional[Progress] = None
        self._task_id = None
        self._start_time = time.time()
        self._last_scanned = 0

    def __enter__(self):
        self._start_time = time.time()
        self._last_scanned = 0

        # Use simple spinner without emoji for macOS feel
        self.progress = Progress(
            SpinnerColumn(style=get_theme().primary),
            TextColumn("[progress.description]{task.description}", style=get_theme().text),
            BarColumn(
                bar_width=40,
                style=get_theme().primary,
                complete_style=get_theme().primary,
                finished_style="green"
            ),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[rate]}/s[/dim]", style=get_theme().dim),
            TimeElapsedColumn(),
            console=self.console
        )
        self.progress.__enter__()
        self._task_id = self.progress.add_task(
            "[cyan]Scanning...",
            total=100,
            rate="0",
            directory=""
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
        return False

    def update(
        self,
        scanned: int,
        current_dir: str = "",
        found_count: int = 0,
        found_size: int = 0
    ):
        """Update progress display"""
        if not self.progress or self._task_id is None:
            return

        elapsed = time.time() - self._start_time
        rate = int(scanned / elapsed) if elapsed > 0 else 0

        # Truncate directory path for display
        if current_dir:
            home = os.path.expanduser("~")
            if current_dir.startswith(home):
                current_dir = "~" + current_dir[len(home):]
            if len(current_dir) > 50:
                current_dir = "..." + current_dir[-47:]

        # Calculate fake percentage based on rate
        percentage = min((rate / 1000) * 100, 99) if rate > 0 else 0

        desc = f"[cyan]Scanning"
        if current_dir:
            desc += f" [dim]{current_dir}[/dim]"
        if found_count > 0:
            desc += f" | Found: {found_count} ({BigFilesFinder.format_size(found_size)})"

        self.progress.update(
            self._task_id,
            description=desc,
            completed=percentage,
            rate=str(rate),
            directory=current_dir
        )

        self._last_scanned = scanned

    def finish(self, total_scanned: int, found_count: int, found_size: int):
        """Mark progress as complete"""
        if not self.progress or self._task_id is None:
            return

        elapsed = time.time() - self._start_time
        rate = int(total_scanned / elapsed) if elapsed > 0 else 0

        self.progress.update(
            self._task_id,
            description=f"✅ Done! Scanned {total_scanned:,} files | Found {found_count:,} ({BigFilesFinder.format_size(found_size)})",
            completed=100,
            rate=str(rate)
        )


def create_header_panel(
    directory: str,
    min_size: int,
    max_size: Optional[int],
    extensions: Optional[List[str]],
    exclude: Optional[List[str]],
    sort_by: str,
    limit: int,
    dark: Optional[bool] = None
) -> Panel:
    """Create the scan header panel"""
    theme = get_theme(dark)

    ext_desc = f" [{', '.join(extensions)}]" if extensions else ""
    max_desc = f" - {max_size}MB max" if max_size else ""
    exclude_desc = f" (excl: {', '.join(exclude)})" if exclude else ""

    content = f"""[bold {theme.primary}]🔍 BIGFILES[/bold {theme.primary}] - Large File Finder
[dim]Directory:[/dim] {directory}
[dim]Size:[/dim] > {min_size}MB{max_desc}{ext_desc}{exclude_desc}
[dim]Sort:[/dim] {sort_by} | [dim]Limit:[/dim] {limit}"""

    return Panel.fit(
        content,
        border_style=theme.primary,
        box=box.DOUBLE,
        style=theme.surface
    )


def create_help_panel(dark: Optional[bool] = None) -> Panel:
    """Create the help panel"""
    theme = get_theme(dark)

    content = f"""[bold {theme.primary}]🔍 BIGFILES[/bold {theme.primary}] - Large File Finder

[yellow]USAGE:[/yellow]

    bigfiles [OPTIONS]

[yellow]OPTIONS:[/yellow]

    [dim]-d, --dir DIR[/dim]          Directory to scan (default: ~)
    [dim]-m, --min MB[/dim]           Minimum size in MB (default: 100)
    [dim]-M, --max MB[/dim]           Maximum size in MB (optional)
    [dim]-e, --ext EXT[/dim]          Filter by extension(s) (can repeat)
    [dim]-x, --exclude PATTERN[/dim]  Exclude paths containing pattern
    [dim]-s, --sort FIELD[/dim]       Sort by: size, name, path, modified
    [dim]-l, --limit N[/dim]          Max results to show (default: 50)
    [dim]-S, --simple[/dim]           Simple list output
    [dim]-i, --interactive[/dim]      Interactive TUI mode
    [dim]--notify[/dim]               Send notification on completion
    [dim]--output json|csv[/dim]      Output format
    [dim]--group[/dim]                Group by category
    [dim]--no-bars[/dim]              Hide size bars
    [dim]--dark|--light[/dim]         Force theme
    [dim]-h, --help[/dim]             Show this help menu

[yellow]SPOTLIGHT FILTERS:[/yellow]

    [green]type:video[/green]           Videos only
    [green]type:image[/green]           Photos only
    [green]larger:1GB[/green]           Files larger than 1GB
    [green]newer:30d[/green]            Modified in last 30 days
    [green]name:backup[/green]          Files containing 'backup'

[yellow]KEYBOARD SHORTCUTS (TUI):[/yellow]

    [dim]↑/↓ or j/k[/dim]         Navigate
    [dim]Enter or o[/dim]          Open file
    [dim]Space[/dim]               QuickLook preview
    [dim]r[/dim]                   Reveal in Finder
    [dim]d[/dim]                   Disk usage info
    [dim]s[/dim]                   Sort menu
    [dim]f[/dim]                   Filter menu
    [dim]h[/dim]                   Help
    [dim]q[/dim]                   Quit

[yellow]EXAMPLES:[/yellow]

    [green]bigfiles[/green]                      Show this help
    [green]bigfiles -d ~/Downloads[/green]      Scan Downloads
    [green]bigfiles -m 1000[/green]             Files > 1GB
    [green]bigfiles -m 100 -M 500[/green]       Files 100-500MB
    [green]bigfiles -e pdf -e docx[/green]       Only documents
    [green]bigfiles --interactive[/green]        TUI mode
    [green]bigfiles --notify[/green]             With notification"""

    return Panel.fit(
        content,
        border_style=theme.primary,
        box=box.DOUBLE,
        style=theme.surface
    )
