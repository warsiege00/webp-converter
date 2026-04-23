"""Size and loading-gain estimates for image-to-WebP conversions.

Ratios are conservative empirical averages; actual results vary by image
content but these provide a reliable planning baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

from .scanner import AssetFile

# Fraction of original file size expected after WebP conversion
_REDUCTION_RATIO: dict[str, float] = {
    ".png": 0.70,   # WebP is ~30% smaller than PNG
    ".jpg": 0.75,   # WebP is ~25% smaller than JPEG
    ".jpeg": 0.75,
    ".svg": 0.60,   # rasterised WebP tends to be significantly smaller
}

# Typical web page loading impact per KB saved (very rough heuristic):
# ~0.008 ms per KB at a 10 Mbps connection — used only for a rough estimate.
_MS_PER_KB_SAVED = 0.008


@dataclass
class SizeEstimate:
    original_bytes: int
    estimated_bytes: int
    saving_bytes: int
    saving_pct: float
    estimated_loading_gain_ms: float

    @property
    def original_kb(self) -> float:
        return self.original_bytes / 1024

    @property
    def estimated_kb(self) -> float:
        return self.estimated_bytes / 1024

    @property
    def saving_kb(self) -> float:
        return self.saving_bytes / 1024


def estimate(asset: AssetFile) -> SizeEstimate:
    """Return a :class:`SizeEstimate` for converting *asset* to WebP."""
    ratio = _REDUCTION_RATIO.get(asset.extension.lower(), 0.75)
    estimated = int(asset.size_bytes * ratio)
    saving = asset.size_bytes - estimated
    saving_pct = (saving / asset.size_bytes * 100) if asset.size_bytes else 0.0
    loading_gain_ms = (saving / 1024) * _MS_PER_KB_SAVED

    return SizeEstimate(
        original_bytes=asset.size_bytes,
        estimated_bytes=estimated,
        saving_bytes=saving,
        saving_pct=saving_pct,
        estimated_loading_gain_ms=loading_gain_ms,
    )


def total_savings(estimates: list[SizeEstimate]) -> tuple[int, int, float]:
    """Return (total_original_bytes, total_estimated_bytes, total_saving_pct)."""
    total_orig = sum(e.original_bytes for e in estimates)
    total_est = sum(e.estimated_bytes for e in estimates)
    pct = ((total_orig - total_est) / total_orig * 100) if total_orig else 0.0
    return total_orig, total_est, pct
