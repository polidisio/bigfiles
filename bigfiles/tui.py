"""
BigFiles - Interactive TUI using Textual
Full keyboard navigation, quick actions, and macOS integration
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.commands import PalettePage
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.events import Key
from textual.keys import Keys
from textual.layouts import DockLayout
from textual.reactive import reactive
from textual.theme import Theme as TextualTheme
from textual.widgets import (
    Button, Footer, Header, Static, ListView, ListItem,
    ProgressBar, TextLog, ScrollView
)

from .finder import FileInfo, BigFilesFinder, CategoryGroup, FileCategory, format_size
from .formatters import create_size_bar, get_file_icon, detect_dark_mode, get_theme
from .notifier import send_scan_complete_notification


class BigFilesTUI(App):
    """Interactive TUI for BigFiles"""

    CSS = """
    Screen {
        background: $surface;
    }

    #header {
        height: 3;
        background: $primary;
        color: $text;
        dock: top;
    }

    #header Static {
        content-align: center middle;
        width: 100%;
    }

    #status-bar {
        height: 3;
        background: $surface;
        border-top: solid $border;
        dock: bottom;
    }

    #file-list {
        width: 100%;
        height: 100%;
    }

    .file-item {
        height: 1;
        padding: 0 2;
    }

    .file-item:hover {
        background: $accent 20%;
    }

    .file-item.selected {
        background: $accent 40%;
    }

    #details-panel {
        width: 40;
        height: 100%;
        background: $surface;
        border-left: solid $border;
    }

    #quick-actions {
        height: 3;
        background: $surface;
        border-top: solid $border;
    }

    .action-button {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("o", "open_file", "Open", show=True),
        Binding("r", "reveal", "Reveal", show=True),
        Binding("space", "quicklook", "Look", show=True),
        Binding("s", "sort_menu", "Sort", show=True),
        Binding("f", "filter_menu", "Filter", show=True),
        Binding("n", "toggle_theme", "Theme", show=True),
        Binding("b", "toggle_bars", "Bars", show=True),
        Binding("g", "toggle_group", "Group", show=True),
        Binding("escape", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        directory: str,
        min_size_mb: int = 100,
        max_size_mb: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        sort_by: str = "size",
        limit: int = 50,
        dark: Optional[bool] = None,
        notify: bool = False
    ):
        super().__init__()

        self.directory = directory
        self.min_size_mb = min_size_mb
        self.max_size_mb = max_size_mb
        self.extensions = extensions
        self.exclude_patterns = exclude_patterns
        self.sort_by = sort_by
        self.limit = limit
        self.notify = notify

        # Determine theme
        if dark is None:
            dark = detect_dark_mode()
        self.dark_mode = dark

        # State
        self.files: List[FileInfo] = []
        self.selected_index = 0
        self.show_size_bars = True
        self.show_grouped = False
        self.scan_start_time = time.time()
        self.is_scanning = True

        # Setup theme
        self.setup_theme()

    def setup_theme(self):
        """Setup Textual theme based on dark/light mode"""
        theme = get_theme(self.dark_mode)

        if self.dark_mode:
            self.theme = TextualTheme(
                name="bigfiles-dark",
                primary=Color.parse(theme.primary),
                secondary=Color.parse(theme.primary),
                accent=Color.parse(theme.accent),
                background=Color.parse(theme.colors["bg"]),
                surface=Color.parse(theme.colors["surface"]),
                text=Color.parse(theme.colors["text"]),
                dim=Color.parse(theme.colors["dim"]),
                border=Color.parse(theme.colors["border"]),
            )
        else:
            self.theme = TextualTheme(
                name="bigfiles-light",
                primary=Color.parse(theme.primary),
                secondary=Color.parse(theme.primary),
                accent=Color.parse(theme.accent),
                background=Color.parse(theme.colors["bg"]),
                surface=Color.parse(theme.colors["surface"]),
                text=Color.parse(theme.colors["text"]),
                dim=Color.parse(theme.colors["dim"]),
                border=Color.parse(theme.colors["border"]),
            )

    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header()

        with Horizontal():
            # Main file list
            with ScrollableContainer(id="file-list-container"):
                yield ListView(id="file-list")

            # Details panel (optional)
            with Vertical(id="details-panel"):
                yield Static("File Details", id="details-title")
                yield ScrollView(id="details-content")

        # Status bar
        yield Horizontal(
            Static("", id="status-text"),
            id="status-bar"
        )

        # Quick actions bar
        yield Horizontal(
            Button("Open (o)", id="btn-open", variant="primary"),
            Button("Reveal (r)", id="btn-reveal"),
            Button("QuickLook (␣)", id="btn-quicklook"),
            id="quick-actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when app mounts - start scan"""
        self.title = "BigFiles"
        self.sub_title = f"Scanning {self.directory}"

        # Start scanning in background
        asyncio.create_task(self.run_scan())

    async def run_scan(self) -> None:
        """Run the file scan"""
        finder = BigFilesFinder(
            self.directory,
            self.min_size_mb,
            self.max_size_mb,
            self.extensions,
            self.exclude_patterns
        )

        self.is_scanning = True
        self.scan_start_time = time.time()

        # Update status
        self.update_status("🔍 Scanning...")

        # Run scan
        await finder.scan()

        self.is_scanning = False
        self.files = finder.get_results(self.sort_by, self.limit)

        # Update UI
        self.sub_title = f"Found {len(self.files)} files"
        self.update_file_list()
        self.update_status(f"✅ Found {len(self.files)} files in {int(time.time() - self.scan_start_time)}s")

        # Send notification if requested
        if self.notify:
            send_scan_complete_notification(
                scanned_count=finder.total_scanned,
                found_count=len(self.files),
                total_size=sum(f.size for f in self.files),
                duration_seconds=time.time() - self.scan_start_time
            )

    def update_file_list(self) -> None:
        """Update the file list display"""
        list_view = self.query_one("#file-list", ListView)
        list_view.clear()

        max_size = max(f.size for f in self.files) if self.files else 0

        for i, file in enumerate(self.files):
            icon = get_file_icon(file.path)
            name = file.name
            parent = file.parent_name
            size_str = format_size(file.size)

            if self.show_size_bars:
                bar = create_size_bar(file.size, max_size, width=20)
                display = f" {icon} {name:<40} {size_str:>10}  {bar}"
            else:
                display = f" {icon} {name:<50} {size_str:>10}"

            list_item = ListItem(
                Static(display),
                id=f"file-{i}"
            )
            list_view.append(list_item)

        # Select first item
        if self.files:
            list_view.index = 0

    def update_status(self, message: str) -> None:
        """Update the status bar"""
        status = self.query_one("#status-text", Static)
        status.update(message)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle file selection"""
        list_view = self.query_one("#file-list", ListView)
        self.selected_index = list_view.index or 0

    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()

    def action_show_help(self) -> None:
        """Show help"""
        help_text = """
        🔍 BIGFILES TUI - Keyboard Shortcuts

        Navigation:
        ↑/↓ or j/k     Navigate files
        Enter or o     Open file with default app
        Space          QuickLook preview
        r              Reveal in Finder
        d              Show disk usage

        Display:
        b              Toggle size bars
        g              Toggle group by category
        n              Toggle dark/light mode

        Actions:
        s              Sort menu
        f              Filter menu
        h              Show this help
        q              Quit

        Press any key to close...
        """
        self.update_status(help_text)

    def action_open_file(self) -> None:
        """Open selected file with default application"""
        if not self.files or self.selected_index >= len(self.files):
            return

        file_path = self.files[self.selected_index].path
        try:
            subprocess.run(["open", file_path], check=True)
            self.update_status(f"✅ Opened: {Path(file_path).name}")
        except subprocess.CalledProcessError:
            self.update_status(f"❌ Failed to open: {file_path}")

    def action_reveal(self) -> None:
        """Reveal file in Finder"""
        if not self.files or self.selected_index >= len(self.files):
            return

        file_path = self.files[self.selected_index].path
        try:
            subprocess.run(["open", "-R", file_path], check=True)
            self.update_status(f"✅ Revealed: {Path(file_path).name}")
        except subprocess.CalledProcessError:
            self.update_status(f"❌ Failed to reveal: {file_path}")

    def action_quicklook(self) -> None:
        """QuickLook preview of selected file"""
        if not self.files or self.selected_index >= len(self.files):
            return

        file_path = self.files[self.selected_index].path
        try:
            subprocess.run(["qlmanage", "-p", file_path], check=True)
        except subprocess.CalledProcessError:
            self.update_status(f"❌ QuickLook failed: {Path(file_path).name}")

    def action_sort_menu(self) -> None:
        """Show sort options"""
        current = self.sort_by
        options = ["size", "name", "path", "modified"]
        current_idx = options.index(current) if current in options else 0
        next_idx = (current_idx + 1) % len(options)
        self.sort_by = options[next_idx]
        self.files = sorted(self.files, key=lambda f: getattr(f, self.sort_by, 0), reverse=(self.sort_by == "size"))
        self.update_file_list()
        self.update_status(f"🔄 Sorted by {self.sort_by}")

    def action_filter_menu(self) -> None:
        """Cycle through filters"""
        self.update_status("Filters: Use -e flag at startup (e.g., -e pdf -e zip)")

    def action_toggle_theme(self) -> None:
        """Toggle dark/light mode"""
        self.dark_mode = not self.dark_mode
        self.setup_theme()
        self.theme = self.theme  # Force refresh
        self.update_file_list()
        mode = "dark" if self.dark_mode else "light"
        self.update_status(f"🎨 Switched to {mode} mode")

    def action_toggle_bars(self) -> None:
        """Toggle size bars"""
        self.show_size_bars = not self.show_size_bars
        self.update_file_list()
        status = "shown" if self.show_size_bars else "hidden"
        self.update_status(f"📊 Size bars {status}")

    def action_toggle_group(self) -> None:
        """Toggle group by category"""
        self.show_grouped = not self.show_grouped
        self.update_status(f"📁 Grouping {'enabled' if self.show_grouped else 'disabled'}")


async def run_tui(
    directory: str,
    min_size: int,
    max_size: Optional[int],
    extensions: Optional[List[str]],
    exclude: Optional[List[str]],
    sort_by: str,
    limit: int,
    dark: Optional[bool],
    notify: bool
):
    """Run the TUI application"""
    app = BigFilesTUI(
        directory=directory,
        min_size_mb=min_size,
        max_size_mb=max_size,
        extensions=extensions,
        exclude_patterns=exclude,
        sort_by=sort_by,
        limit=limit,
        dark=dark,
        notify=notify
    )
    await app.run_async()
