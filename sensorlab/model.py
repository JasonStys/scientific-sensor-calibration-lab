"""Strict synthetic calibration inputs by Jason Stys. Settings, configuration, validate and loaders:
docs/CODE_INDEX.md lists exact function, field, parameter and variable locations. No device inputs.
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CASES = {
    "linear-clean": "Stable linear instrument",
    "unequal-noise": "Unequal declared uncertainty",
    "sensor-drift": "Changing sensor offset",
    "saturation": "Clipped signal / range checks",
    "missing-data": "Missing calibration and samples",
    "nonlinear-response": "Unsupported nonlinear response",
}
CHOICES = {"sigma": (1, 2, 4), "limit": (2, 3, 4), "age": (0, 60, 120)}
CONFIG_RANGES = {
    "rail_low_uv": (-10000000, 10000000),
    "rail_high_uv": (-10000000, 10000000),
    "age_days": (0, 3650),
    "max_age_days": (1, 3650),
    "z_limit": (2, 5),
    "chi_limit": (1, 25),
}


@dataclass(frozen=True)
class Settings:
    """Finite controls for scenario, declared-uncertainty multiplier, review threshold and calibration age."""

    scenario: str = "linear-clean"
    sigma: int = 1
    limit: int = 3
    age: int = 0

    def __post_init__(self) -> None:
        """Reject unknown and Boolean/coerced settings before profile generation."""
        if (
            not isinstance(self.scenario, str)
            or self.scenario not in CASES
            or any(
                type(getattr(self, k)) is not int or getattr(self, k) not in v
                for k, v in CHOICES.items()
            )
        ):
            raise ValueError("Unsupported experiment setting")


def catalog() -> dict[str, Any]:
    """Return finite labels/defaults without uploads, devices or remote endpoints."""
    return {"cases": CASES, "choices": CHOICES, "defaults": asdict(Settings())}


def configuration(s: Settings) -> dict[str, Any]:
    """Invent training/held-out/monitoring records for a fictional temperature-to-mV instrument."""

    def response(x: int) -> int:
        """Return the fictional transfer response in microvolts; nonlinear case deliberately violates the fit."""
        return 400000 + 20 * x + (x * x // 10000 if s.scenario == "nonlinear-response" else 0)

    calibration = []
    for i in range(9):
        x = i * 12500
        noise = (-6000, 4000, -3000, 5000, -2000, 3000, -4000, 2000, 1000)[i]
        u = 6000 + (i * 2000 if s.scenario == "unequal-noise" else 0)
        y = response(x) + noise * (i + 1 if s.scenario == "unequal-noise" else 1)
        calibration.append(
            {
                "x_milli": x,
                "signal_uv": None if s.scenario == "missing-data" and i in (1, 4) else y,
                "u_uv": u * s.sigma,
            }
        )
    checks = [
        {
            "x_milli": x,
            "signal_uv": response(x) + (3500 if i % 2 else -3500),
            "u_uv": 6000 * s.sigma,
        }
        for i, x in enumerate(range(10000, 100000, 20000))
    ]
    samples = []
    for h in range(24):
        x = (5 + h * 4) * 1000
        sample_y: int | None = response(x) + (h % 3 - 1) * 3000
        if s.scenario == "sensor-drift" and h >= 10:
            sample_y = response(x) + (h % 3 - 1) * 3000 + (h - 9) * 8000
        if s.scenario == "saturation" and h in (8, 10):
            sample_y = 2600000 if h == 8 else 300000
        if s.scenario == "saturation" and h == 18:
            sample_y = 2500000  # valid electronics range, but beyond calibrated reference span
        if s.scenario == "missing-data" and h in (4, 5):
            sample_y = None
        samples.append(
            {
                "signal_uv": sample_y,
                "u_uv": 6000 * s.sigma,
                "reference_milli": None if h == 12 else x,
            }
        )
    return {
        "schema": 1,
        "name": s.scenario,
        "provenance": "Invented laboratory temperature sensor by Jason Stys; no physical reference standards, measured device data or calibration certification.",
        "unit": "degC",
        "config": {
            "rail_low_uv": 300000,
            "rail_high_uv": 2600000,
            "age_days": s.age,
            "max_age_days": 90,
            "z_limit": s.limit,
            "chi_limit": 9,
        },
        "calibration": calibration,
        "checks": checks,
        "samples": samples,
    }


def integer(value: Any, low: int, high: int) -> bool:
    """Accept only bounded exact integers; Boolean and decimal-looking JSON numbers are not coerced."""
    return type(value) is int and low <= value <= high


def validate(data: Any) -> dict[str, Any]:
    """Require exact schemas, consistent fixed-unit input and bounded dataset sizes/types."""
    if (
        not isinstance(data, dict)
        or set(data)
        != {"schema", "name", "provenance", "unit", "config", "calibration", "checks", "samples"}
        or not integer(data["schema"], 1, 1)
    ):
        raise ValueError("Invalid input schema")
    if not isinstance(data["name"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,47}", data["name"]
    ):
        raise ValueError("Invalid scenario name")
    if (
        not isinstance(data["provenance"], str)
        or not 1 <= len(data["provenance"]) <= 240
        or not isinstance(data["unit"], str)
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,15}", data["unit"])
    ):
        raise ValueError("Invalid unit/provenance")
    c = data["config"]
    if (
        not isinstance(c, dict)
        or set(c) != set(CONFIG_RANGES)
        or any(not integer(c[k], *bounds) for k, bounds in CONFIG_RANGES.items())
        or c["rail_low_uv"] >= c["rail_high_uv"]
    ):
        raise ValueError("Invalid configuration")
    for kind, maximum in (("calibration", 64), ("checks", 64), ("samples", 168)):
        rows = data[kind]
        if not isinstance(rows, list) or not 1 <= len(rows) <= maximum:
            raise ValueError("Invalid dataset length")
        for r in rows:
            xkey = "reference_milli" if kind == "samples" else "x_milli"
            if not isinstance(r, dict) or set(r) != {xkey, "signal_uv", "u_uv"}:
                raise ValueError("Invalid record fields")
            if not (
                r["signal_uv"] is None or integer(r["signal_uv"], -10000000, 10000000)
            ) or not integer(r["u_uv"], 1, 100000):
                raise ValueError("Invalid signal/uncertainty")
            if not (kind == "samples" and r[xkey] is None) and not integer(
                r[xkey], -1000000, 1000000
            ):
                raise ValueError("Invalid reference")
    return data


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous repeated JSON keys rather than keeping the last value."""
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Duplicate JSON key")
        out[key] = value
    return out


def load_input(path: Path) -> dict[str, Any]:
    """Read explicit local UTF-8 JSON within 64KiB; reject malformed encodings, depth and duplicate keys."""
    with path.open("rb") as stream:
        body = stream.read(65537)
    if len(body) > 65536:
        raise ValueError("Input file too large")
    try:
        return validate(json.loads(body.decode("utf-8"), object_pairs_hook=unique_object))
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ValueError("Malformed JSON") from error
