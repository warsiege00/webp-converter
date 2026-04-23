"""Recursively discover convertible image assets in a directory tree."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
OPTIMIZED_DIR_NAME = "optimized"


@dataclass
class AssetFile:
    path: Path
    extension: str
    size_bytes: int

    @property
    def format_label(self) -> str:
        ext = self.extension.lower()
        if ext == ".svg":
            return "SVG"
        if ext in {".jpg", ".jpeg"}:
            return "JPEG"
        return "PNG"


def scan(root: str | Path, extensions: set[str] | None = None) -> list[AssetFile]:
    """Return all image assets under *root*, excluding any ``optimized/`` folders.

    Args:
        root: Directory to search (searched recursively).
        extensions: Set of lowercase dot-extensions to include.
                    Defaults to SUPPORTED_EXTENSIONS.
    """
    root = Path(root).resolve()
    allowed = extensions or SUPPORTED_EXTENSIONS
    assets: list[AssetFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune traversal into any 'optimized' directory so we never re-process
        # files that were already converted.
        dirnames[:] = [d for d in dirnames if d != OPTIMIZED_DIR_NAME]

        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.suffix.lower() in allowed:
                try:
                    size = filepath.stat().st_size
                except OSError:
                    continue
                assets.append(
                    AssetFile(
                        path=filepath,
                        extension=filepath.suffix.lower(),
                        size_bytes=size,
                    )
                )

    assets.sort(key=lambda a: a.path)
    return assets
