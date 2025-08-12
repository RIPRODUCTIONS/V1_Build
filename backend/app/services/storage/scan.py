from __future__ import annotations

import os
from typing import BinaryIO

ENABLE_SCAN = os.getenv("ENABLE_ANTIVIRUS", "0") == "1"
DISALLOWED_EXT = {".exe", ".dll", ".bat", ".cmd", ".sh", ".js"}


def precheck_filename(name: str) -> None:
    ext = os.path.splitext(name)[1].lower()
    if ext in DISALLOWED_EXT:
        raise ValueError("disallowed file type")


def scan_stream(stream: BinaryIO) -> bool:
    if not ENABLE_SCAN:
        return True
    # TODO: Wire to real antivirus engine (clamd, etc.)
    return True


