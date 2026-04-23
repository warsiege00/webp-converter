"""Convert PNG, JPEG and SVG files to optimized WebP.

Pipeline:
  PNG / JPEG  → Pillow open → save as WebP
  SVG         → CairoSVG render to PNG bytes → Pillow open → save as WebP
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

OPTIMIZED_DIR_NAME = "optimized"


@dataclass
class ConversionResult:
    source_path: Path
    output_path: Path | None
    original_bytes: int
    converted_bytes: int = 0
    success: bool = False
    error: str = ""

    @property
    def saving_bytes(self) -> int:
        return self.original_bytes - self.converted_bytes

    @property
    def saving_pct(self) -> float:
        if not self.original_bytes:
            return 0.0
        return self.saving_bytes / self.original_bytes * 100


def _output_path(source: Path) -> Path:
    """Compute <source_dir>/optimized/<stem>.webp for a given source file."""
    optimized_dir = source.parent / OPTIMIZED_DIR_NAME
    return optimized_dir / f"{source.stem}.webp"


def _convert_raster(source: Path, output: Path, quality: int) -> None:
    """Convert PNG or JPEG to WebP using Pillow."""
    from PIL import Image  # lazy import keeps startup fast

    with Image.open(source) as img:
        # Preserve transparency for PNG; convert palette images for better compat.
        if img.mode in {"P", "PA"}:
            img = img.convert("RGBA")
        elif img.mode not in {"RGB", "RGBA", "L", "LA"}:
            img = img.convert("RGBA")

        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(
            output,
            format="WEBP",
            quality=quality,
            method=6,       # best compression method (slower but smaller)
            lossless=False,
        )


def _convert_svg(source: Path, output: Path, quality: int, scale: float = 1.0) -> None:
    """Rasterise SVG → PNG bytes → WebP using CairoSVG + Pillow."""
    import cairosvg
    from PIL import Image  # lazy import

    png_bytes = cairosvg.svg2png(
        url=str(source),
        scale=scale,
    )

    with Image.open(io.BytesIO(png_bytes)) as img:
        if img.mode not in {"RGB", "RGBA"}:
            img = img.convert("RGBA")

        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(
            output,
            format="WEBP",
            quality=quality,
            method=6,
            lossless=False,
        )


def convert_file(source_path: str | Path, quality: int = 85) -> ConversionResult:
    """Convert a single image file to WebP.

    Args:
        source_path: Absolute path to the source image.
        quality:     WebP quality (1–100). Default 85 balances size and fidelity.

    Returns:
        A :class:`ConversionResult` describing the outcome.
    """
    source = Path(source_path).resolve()
    original_bytes = source.stat().st_size if source.exists() else 0
    output = _output_path(source)

    result = ConversionResult(
        source_path=source,
        output_path=output,
        original_bytes=original_bytes,
    )

    ext = source.suffix.lower()
    try:
        if ext == ".svg":
            _convert_svg(source, output, quality)
        elif ext in {".png", ".jpg", ".jpeg"}:
            _convert_raster(source, output, quality)
        else:
            result.error = f"Unsupported extension: {ext}"
            return result

        result.converted_bytes = output.stat().st_size
        result.success = True
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        result.output_path = None

    return result
