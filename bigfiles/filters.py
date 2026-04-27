"""
BigFiles - Spotlight-style filter parser
Supports: type:, larger:, newer:, name:, ext:
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .finder import FileInfo, FileCategory


class FilterType(Enum):
    TYPE = "type"
    LARGER = "larger"
    NEWER = "newer"
    NAME = "name"
    EXT = "ext"


@dataclass
class SpotlightFilter:
    """A parsed Spotlight-style filter"""
    filter_type: FilterType
    value: str
    negate: bool = False

    def matches(self, file: FileInfo) -> bool:
        """Check if file matches this filter"""
        result = self._matches_impl(file)
        return not result if self.negate else result

    def _matches_impl(self, file: FileInfo) -> bool:
        if self.filter_type == FilterType.TYPE:
            return self._match_type(file)
        elif self.filter_type == FilterType.LARGER:
            return self._match_larger(file)
        elif self.filter_type == FilterType.NEWER:
            return self._match_newer(file)
        elif self.filter_type == FilterType.NAME:
            return self._match_name(file)
        elif self.filter_type == FilterType.EXT:
            return self._match_ext(file)
        return True

    def _match_type(self, file: FileInfo) -> bool:
        type_map = {
            "video": [FileCategory.VIDEO],
            "image": [FileCategory.IMAGE],
            "audio": [FileCategory.AUDIO],
            "photo": [FileCategory.IMAGE],
            "photos": [FileCategory.IMAGE],
            "document": [FileCategory.DOCUMENT],
            "doc": [FileCategory.DOCUMENT],
            "docs": [FileCategory.DOCUMENT],
            "archive": [FileCategory.ARCHIVE],
            "app": [FileCategory.APP],
            "apps": [FileCategory.APP],
            "code": [FileCategory.CODE],
            "database": [FileCategory.DATABASE],
            "db": [FileCategory.DATABASE],
            "other": [FileCategory.OTHER],
        }

        value_lower = self.value.lower()
        categories = type_map.get(value_lower, [])

        # Handle plural forms
        if not categories:
            if value_lower.endswith("s"):
                # Try singular form
                singular = value_lower[:-1]
                categories = type_map.get(singular, [])

        return file.category in categories if categories else False

    def _match_larger(self, file: FileInfo) -> bool:
        """Match files larger than specified size"""
        size_bytes = self._parse_size(self.value)
        return file.size > size_bytes if size_bytes > 0 else False

    def _match_newer(self, file: FileInfo) -> bool:
        """Match files modified within specified time"""
        delta = self._parse_time_delta(self.value)
        if delta is None:
            return False
        cutoff = datetime.now() - delta
        file_date = datetime.fromtimestamp(file.modified)
        return file_date > cutoff

    def _match_name(self, file: FileInfo) -> bool:
        """Fuzzy match on filename"""
        pattern = self.value.lower()
        name = file.name.lower()
        return pattern in name

    def _match_ext(self, file: FileInfo) -> bool:
        """Match by extension"""
        ext = file.extension.lower().lstrip(".")
        value = self.value.lower().lstrip(".")
        return ext == value

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """Parse size string like '1GB', '500MB' to bytes"""
        size_str = size_str.upper().strip()

        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
            "PB": 1024 ** 5,
        }

        # Try to parse as number + unit
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT]?B)$", size_str)
        if match:
            value, unit = match.groups()
            return int(float(value) * units.get(unit, 1))

        # Try just a number (assume MB)
        try:
            return int(float(size_str) * 1024 * 1024)
        except ValueError:
            return 0

    @staticmethod
    def _parse_time_delta(time_str: str) -> Optional[timedelta]:
        """Parse time string like '30d', '1y', '1w' to timedelta"""
        time_str = time_str.lower().strip()

        units = {
            "s": 1,
            "sec": 1,
            "secs": 1,
            "m": 60,
            "min": 60,
            "mins": 60,
            "h": 3600,
            "hr": 3600,
            "hrs": 3600,
            "hour": 3600,
            "hours": 3600,
            "d": 86400,
            "day": 86400,
            "days": 86400,
            "w": 604800,
            "wk": 604800,
            "week": 604800,
            "weeks": 604800,
            "mo": 2592000,  # 30 days
            "month": 2592000,
            "months": 2592000,
            "y": 31536000,
            "yr": 31536000,
            "year": 31536000,
            "years": 31536000,
        }

        match = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]+)$", time_str)
        if match:
            value, unit = match.groups()
            try:
                seconds = float(value) * units.get(unit, 0)
                if seconds > 0:
                    return timedelta(seconds=seconds)
            except (ValueError, KeyError):
                pass

        return None


def parse_spotlight_query(query: str) -> List[SpotlightFilter]:
    """Parse a Spotlight-style query string into filters"""
    filters = []

    # Split by spaces but respect quoted strings
    tokens = []
    current = ""
    in_quote = False
    quote_char = None

    for char in query:
        if char in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = char
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif char == " " and not in_quote:
            if current:
                tokens.append(current)
            current = ""
        else:
            current += char

    if current:
        tokens.append(current)

    for token in tokens:
        filter_obj = parse_filter_token(token)
        if filter_obj:
            filters.append(filter_obj)

    return filters


def parse_filter_token(token: str) -> Optional[SpotlightFilter]:
    """Parse a single filter token like 'type:video' or '-larger:1GB'"""
    token = token.strip()
    if not token:
        return None

    # Check for negation
    negate = token.startswith("-")
    if negate:
        token = token[1:]

    # Check for supported filter types
    filter_types = ["type:", "larger:", "newer:", "name:", "ext:", "size:", "modified:"]

    for ft in filter_types:
        if token.lower().startswith(ft):
            value = token[len(ft):]
            if not value:
                return None

            # Map aliases
            actual_type = ft.rstrip(":").lower()
            if actual_type == "size":
                actual_type = "larger"
            elif actual_type == "modified":
                actual_type = "newer"

            try:
                filter_type = FilterType(actual_type)
                return SpotlightFilter(filter_type=filter_type, value=value, negate=negate)
            except ValueError:
                return None

    return None


def apply_filters(files: List[FileInfo], filters: List[SpotlightFilter]) -> List[FileInfo]:
    """Apply filters to a list of files"""
    if not filters:
        return files

    result = []
    for file in files:
        if all(f.matches(file) for f in filters):
            result.append(file)

    return result


def filter_to_description(filters: List[SpotlightFilter]) -> str:
    """Convert filters to human-readable description"""
    parts = []
    for f in filters:
        prefix = "not " if f.negate else ""
        if f.filter_type == FilterType.TYPE:
            parts.append(f"{prefix}type:{f.value}")
        elif f.filter_type == FilterType.LARGER:
            parts.append(f"{prefix}larger:{f.value}")
        elif f.filter_type == FilterType.NEWER:
            parts.append(f"{prefix}newer:{f.value}")
        elif f.filter_type == FilterType.NAME:
            parts.append(f"{prefix}name:{f.value}")
        elif f.filter_type == FilterType.EXT:
            parts.append(f"{prefix}ext:{f.value}")
    return ", ".join(parts)
