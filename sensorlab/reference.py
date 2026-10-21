"""Independent exact-rational weighted-fit reference by Jason Stys. Functions/variables: docs/CODE_INDEX.md.

Uses raw weighted normal equations rather than the C# centered-moment implementation. Not physical validation.
"""

from fractions import Fraction as F
from typing import Any

FIELDS = ("a", "b", "var_a", "var_b", "cov_ab", "chi2_reduced", "xmin", "xmax")


def reference_fit(points: list[dict[str, int]]) -> dict[str, Any]:
    """Solve known-variance WLS exactly before conversion to float; references are assumed error-free."""
    result: dict[str, Any] = {
        "status": "insufficient-calibration",
        "n": len(points),
        **dict.fromkeys(FIELDS),
    }
    if len(points) < 4:
        return result
    xs = [F(p["x_milli"], 1000) for p in points]
    ys = [F(p["signal_uv"], 1000) for p in points]
    weights = [F(1000000, p["u_uv"] ** 2) for p in points]
    if max(xs) - min(xs) < 1:
        result["status"] = "insufficient-span"
        return result
    w = sum(weights, F(0))
    x = sum((a * b for a, b in zip(weights, xs, strict=True)), F(0))
    y = sum((a * b for a, b in zip(weights, ys, strict=True)), F(0))
    xx = sum((a * b * b for a, b in zip(weights, xs, strict=True)), F(0))
    xy = sum((a * b * c for a, b, c in zip(weights, xs, ys, strict=True)), F(0))
    determinant = w * xx - x * x
    a = (xx * y - x * xy) / determinant
    b = (w * xy - x * y) / determinant
    if abs(b) < F(1, 100):
        result["status"] = "noninvertible-fit"
        return result
    chi = sum(ww * (yy - a - b * xx_) ** 2 for ww, xx_, yy in zip(weights, xs, ys, strict=True)) / (
        len(points) - 2
    )
    values = (a, b, xx / determinant, w / determinant, -x / determinant, chi, min(xs), max(xs))
    result.update(status="ok", **{k: float(v) for k, v in zip(FIELDS, values, strict=True)})
    return result
