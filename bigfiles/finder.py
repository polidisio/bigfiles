"""
BigFiles - Large file finder for macOS
Finder module - Core scanning logic
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict
import fnmatch
import asyncio


class FileCategory(Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    APP = "app"
    CODE = "code"
    DATABASE = "database"
    OTHER = "other"

    @classmethod
    def from_extension(cls, ext: str) -> "FileCategory":
        ext = ext.lower().lstrip(".")
        video_exts = {"mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "m4v"}
        image_exts = {"jpg", "jpeg", "png", "gif", "heic", "bmp", "tiff", "svg", "webp", "raw", "cr2", "nef"}
        audio_exts = {"mp3", "wav", "flac", "aac", "m4a", "ogg", "wma", "aiff"}
        doc_exts = {"pdf", "doc", "docx", "txt", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "rtf", "pages", "numbers", "keynote"}
        archive_exts = {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "dmg", "iso", "img"}
        app_exts = {"app", "ipa", "xcarchive", "pkg"}
        code_exts = {"py", "js", "ts", "java", "swift", "c", "cpp", "h", "hpp", "go", "rs", "rb", "php", "html", "css", "json", "xml", "yaml", "yml", "sql", "sh", "zsh"}
        db_exts = {"sql", "db", "sqlite", "sqlite3", "mdb", "accdb"}

        if ext in video_exts:
            return cls.VIDEO
        elif ext in image_exts:
            return cls.IMAGE
        elif ext in audio_exts:
            return cls.AUDIO
        elif ext in doc_exts:
            return cls.DOCUMENT
        elif ext in archive_exts:
            return cls.ARCHIVE
        elif ext in app_exts:
            return cls.APP
        elif ext in code_exts:
            return cls.CODE
        elif ext in db_exts:
            return cls.DATABASE
        return cls.OTHER


@dataclass
class FileInfo:
    path: str
    size: int
    is_dir: bool
    modified: float

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower()

    @property
    def category(self) -> FileCategory:
        return FileCategory.from_extension(self.extension)

    @property
    def parent_name(self) -> str:
        return Path(self.path).parent.name


@dataclass
class CategoryGroup:
    category: FileCategory
    files: List[FileInfo] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def icon(self) -> str:
        icons = {
            FileCategory.VIDEO: "📹",
            FileCategory.IMAGE: "🖼️",
            FileCategory.AUDIO: "🎵",
            FileCategory.DOCUMENT: "📄",
            FileCategory.ARCHIVE: "📦",
            FileCategory.APP: "📱",
            FileCategory.CODE: "💻",
            FileCategory.DATABASE: "🗄️",
            FileCategory.OTHER: "📁",
        }
        return icons.get(self.category, "📁")

    @property
    def label(self) -> str:
        labels = {
            FileCategory.VIDEO: "Videos",
            FileCategory.IMAGE: "Photos",
            FileCategory.AUDIO: "Audio",
            FileCategory.DOCUMENT: "Documents",
            FileCategory.ARCHIVE: "Archives",
            FileCategory.APP: "Apps",
            FileCategory.CODE: "Code",
            FileCategory.DATABASE: "Databases",
            FileCategory.OTHER: "Other",
        }
        return labels.get(self.category, "Other")


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
        self.current_directory = ""
        self.scan_rate = 0.0  # files per second
        self._last_update_time = 0
        self._files_at_last_update = 0

        # Default directories to skip
        self.default_excludes = [
            ".git", "node_modules", "__pycache__", ".cache", "Caches",
            ".npm", ".pip", ".cargo", "vendor", ".cocoapods", ".swiftpm",
            "Pods", ".build", "DerivedData", ".Spotlight-V100", ".Trashes",
            ".fseventsd", ".TemporaryItems", ".DocumentRevisions-V100"
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
        import time
        start_time = time.time()
        last_count_time = start_time

        try:
            for root, dirs, filenames in os.walk(self.directory):
                if not self.is_running:
                    break

                self.current_directory = root

                # Skip hidden dirs and common cache dirs
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".")
                    and d not in self.default_excludes
                ]

                self.total_scanned += len(filenames)

                # Update scan rate every 0.5 seconds
                current_time = time.time()
                if current_time - last_count_time >= 0.5:
                    elapsed = current_time - start_time
                    self.scan_rate = self.total_scanned / elapsed if elapsed > 0 else 0
                    last_count_time = current_time

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
                            if ext not in self.extensions and ext.lstrip(".") not in self.extensions:
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

    def group_by_category(self) -> Dict[FileCategory, CategoryGroup]:
        """Group files by category"""
        groups: Dict[FileCategory, CategoryGroup] = {}
        for file in self.files:
            cat = file.category
            if cat not in groups:
                groups[cat] = CategoryGroup(category=cat)
            groups[cat].files.append(file)
        return groups

    @staticmethod
    def format_size(size: int) -> str:
        """Format bytes to human readable"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


def format_size(size: int) -> str:
    """Format bytes to human readable"""
    return BigFilesFinder.format_size(size)
