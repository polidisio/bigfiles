"""
BigFiles - macOS Native Notifications
Uses osascript to display Notification Center notifications
"""
import subprocess
import sys
from typing import Optional

from .finder import BigFilesFinder, format_size


def send_notification(
    title: str = "BigFiles",
    message: str = "Scan complete",
    subtitle: Optional[str] = None,
    sound: bool = True
) -> bool:
    """
    Send a native macOS notification using osascript.

    Args:
        title: Notification title
        message: Main notification message
        subtitle: Optional subtitle
        sound: Whether to play a sound

    Returns:
        True if notification was sent successfully
    """
    try:
        # Build osascript command
        cmd = [
            "osascript",
            "-e",
            f'display notification "{message}" with title "{title}"'
        ]

        if subtitle:
            cmd[-1] = cmd[-1][:-1] + f' subtitle "{subtitle}"' + '"'

        if sound:
            cmd[-1] = cmd[-1][:-1] + ' sound name "Glass"' + '"'

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.returncode == 0

    except Exception as e:
        # Fallback: just print to stderr if notification fails
        if sys.stderr:
            print(f"[dim]Notification failed: {e}[/dim]", file=sys.stderr)
        return False


def send_scan_complete_notification(
    scanned_count: int,
    found_count: int,
    total_size: int,
    duration_seconds: float
) -> bool:
    """
    Send a scan completion notification with summary.

    Args:
        scanned_count: Total files scanned
        found_count: Number of files matching criteria
        total_size: Total size of found files in bytes
        duration_seconds: How long the scan took

    Returns:
        True if notification was sent successfully
    """
    # Format duration
    if duration_seconds < 60:
        duration_str = f"{duration_seconds:.1f}s"
    else:
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s"

    # Format message
    size_str = BigFilesFinder.format_size(total_size)
    message = f"Found {found_count:,} files ({size_str}) in {duration_str}"

    # Optional subtitle with scan rate
    if duration_seconds > 0:
        rate = int(scanned_count / duration_seconds)
        subtitle = f"Scanned {scanned_count:,} files ({rate:,}/s)"
    else:
        subtitle = None

    return send_notification(
        title="🔍 BigFiles Scan Complete",
        message=message,
        subtitle=subtitle,
        sound=True
    )


def send_error_notification(error_message: str) -> bool:
    """Send an error notification."""
    return send_notification(
        title="❌ BigFiles Error",
        message=error_message,
        sound=True
    )
