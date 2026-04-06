"""
BigFiles - Interactive CLI tool to find large files on your Mac
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import asyncio

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


class BigFilesFinder:
    def __init__(self, directory: str, min_size_mb: int = 100):
        self.directory = Path(directory).expanduser().resolve()
        self.min_size_bytes = min_size_mb * 1024 * 1024
        self.files: list[FileInfo] = []
        self.total_scanned = 0
        self.is_running = True

    async def scan(self):
        """Scan directory for large files"""
        try:
            for root, dirs, filenames in os.walk(self.directory):
                if not self.is_running:
                    break
                
                # Skip hidden directories and common large folders to skip
                dirs[:] = [d for d in dirs if not d.startswith('.') 
                          and d not in ['node_modules', '__pycache__', '.git', 'Caches']]
                
                self.total_scanned += len(filenames)
                
                for filename in filenames:
                    if not self.is_running:
                        break
                    filepath = Path(root) / filename
                    try:
                        stat = filepath.stat()
                        if stat.st_size >= self.min_size_bytes:
                            self.files.append(FileInfo(
                                path=str(filepath),
                                size=stat.st_size,
                                is_dir=False
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
        '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.dmg': '💿', '.iso': '💿',
        '.pdf': '📄', '.doc': '📄', '.docx': '📄',
        '.sql': '🗄️', '.db': '🗄️',
        '.xcarchive': '📱', '.app': '📱',
        '.vm': '🖥️', '.vmdk': '🖥️',
    }
    return icons.get(ext, '📄')


async def run_scan(directory: str, min_size: int, sort_by: str, limit: int):
    """Run the scan and display results"""
    
    console.clear()
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]🔍 BIGFILES[/bold cyan] - Buscador de archivos grandes\n"
        f"[dim]Directorio:[/dim] {directory}\n"
        f"[dim]Mínimo:[/dim] {min_size} MB | [dim]Ordenado por:[/dim] {sort_by}",
        border_style="cyan",
        box=box.DOUBLE
    ))
    console.print()
    
    # Scan
    finder = BigFilesFinder(directory, min_size)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Escaneando...", total=None)
        
        scan_task = asyncio.create_task(finder.scan())
        
        # Update progress while scanning
        last_count = 0
        while not scan_task.done():
            await asyncio.sleep(0.1)
            if finder.total_scanned != last_count:
                progress.update(task, description=f"[cyan]Archivos escaneados: {finder.total_scanned:,}")
                last_count = finder.total_scanned
        
        await scan_task
    
    console.print(f"\n[green]✓[/green] Escaneados [bold]{finder.total_scanned:,}[/bold] archivos")
    console.print(f"[green]✓[/green] Encontrados [bold]{len(finder.files)}[/bold] archivos ≥ {min_size} MB\n")
    
    if not finder.files:
        console.print("[yellow]No se encontraron archivos.[/yellow]")
        return
    
    # Display results
    results = finder.get_results(sort_by, limit)
    
    table = Table(
        title=f"📊 Top {len(results)} archivos más grandes",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Archivo", style="white")
    table.add_column("Tamaño", justify="right", style="yellow")
    
    for i, file in enumerate(results, 1):
        icon = get_file_icon(file.path)
        name = Path(file.path).name
        parent = Path(file.path).parent.name
        display_path = f"{icon} [link]{parent}/{name}[/link]"
        size_str = format_size(file.size)
        table.add_row(str(i), display_path, size_str)
    
    console.print(table)
    
    # Summary
    total_size = sum(f.size for f in finder.files)
    console.print(f"\n[dim]Total: {len(finder.files)} archivos ({format_size(total_size)})[/dim]")


@click.command()
@click.option(
    '--dir', '-d',
    default=None,
    help='Directorio a escanear (default: ~)'
)
@click.option(
    '--min', '-m',
    default=None,
    type=int,
    help='Tamaño mínimo en MB (default: 100)'
)
@click.option(
    '--sort', '-s',
    type=click.Choice(['size', 'name', 'path'], case_sensitive=False),
    default=None,
    help='Ordenar por (default: size)'
)
@click.option(
    '--limit', '-l',
    default=None,
    type=int,
    help='Número máximo de resultados (default: 50)'
)
@click.option(
    '--list', '-L',
    is_flag=True,
    help='Modo lista simple (sin formato)'
)
@click.option(
    '--help', '-h',
    is_flag=True,
    help='Mostrar esta ayuda'
)
def cli(dir: Optional[str], min: Optional[int], sort: Optional[str], limit: Optional[int], list: bool, help: bool):
    """
    🔍 BIGFILES - Busca archivos grandes en tu Mac
    
    Sin argumentos muestra esta ayuda. Usa argumentos para escanear.
    
    Ejemplos:
    
        bigfiles                    # Escanea home, > 100MB
        bigfiles -d ~/Downloads     # Escanea Downloads
        bigfiles -m 500             # Solo > 500MB
        bigfiles -s name            # Ordena por nombre
        bigfiles -l 20              # Top 20
    """
    # Show welcome/help if no arguments provided
    if dir is None and min is None and sort is None and limit is None:
        console.print(Panel.fit(
            """[bold cyan]🔍 BIGFILES[/bold cyan] - Buscador de archivos grandes
            
            [yellow]USO:[/yellow]
            
            [white]bigfiles [-d DIR] [-m MIN] [-s SORT] [-l LIMIT]
            
            [yellow]OPCIONES:[/yellow]
            
            [dim]-d, --dir DIR[/dim]      Directorio a escanear (default: ~)
            [dim]-m, --min MB[/dim]        Tamaño mínimo en MB (default: 100)
            [dim]-s, --sort SORT[/dim]     Ordenar por: size, name, path (default: size)
            [dim]-l, --limit N[/dim]        Número máximo de resultados (default: 50)
            [dim]-L, --list[/dim]          Modo lista simple
            [dim]-h, --help[/dim]           Mostrar esta ayuda
            
            [yellow]EJEMPLOS:[/yellow]
            
            [green]bigfiles[/green]                    Escanea home, > 100MB
            [green]bigfiles -d ~/Descargas[/green]    Escanea Descargas
            [green]bigfiles -m 500[/green]            Solo archivos > 500MB
            [green]bigfiles -s name[/green]            Ordena por nombre
            [green]bigfiles -l 20[/green]             Top 20 resultados""",
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
    
    directory = Path(dir).expanduser().resolve()
    
    if not directory.exists():
        console.print(f"[red]✗[/red] Directorio no encontrado: {directory}")
        sys.exit(1)
    
    if list:
        # Simple list mode
        console.print(f"Escaneando {directory}...")
        finder = BigFilesFinder(str(directory), min)
        asyncio.run(finder.scan())
        results = finder.get_results(sort, limit)
        for i, f in enumerate(results, 1):
            print(f"{i}. {format_size(f.size).strip():>10} {f.path}")
    else:
        # Interactive mode
        asyncio.run(run_scan(str(directory), min, sort, limit))


def run():
    cli()


if __name__ == '__main__':
    run()
