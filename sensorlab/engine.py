"""Native/reference verification, uncertainty and evidence gates by Jason Stys.

Functions and variables (ROOT, tolerances, fit coefficients, sample quality): docs/CODE_INDEX.md.
Calibration examples are synthetic; no real sensor or reference-standard interface exists.
"""

import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sensorlab.model import Settings, configuration, validate
from sensorlab.reference import FIELDS, reference_fit

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
ABS_TOL = 1e-7
REL_TOL = 1e-8


def canonical(value: Any) -> bytes:
    """Encode deterministic finite sorted JSON; hashes identify content, not certification/authorship."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def normalized(value: Any) -> Any:
    """Round only report floats to ten significant digits after verification/calculation for portable evidence."""
    if type(value) is float:
        return float(format(value, ".10g"))
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value


def native_fit(points: list[dict[str, int]]) -> dict[str, Any]:
    """Invoke only the fixed reviewed C# binary/DLL; bounded input/output and timeout, never a shell."""
    executable = (
        ROOT / "native" / ("CalibrationCore.exe" if sys.platform == "win32" else "CalibrationCore")
    )
    command = (
        [str(executable)]
        if executable.is_file()
        else ["dotnet", str(ROOT / "calibration-core/bin/Release/net10.0/CalibrationCore.dll")]
    )
    try:
        completed = subprocess.run(
            command,
            input=canonical({"points": points}),
            capture_output=True,
            check=True,
            timeout=10,
            env={**os.environ, "DOTNET_NOLOGO": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
        )
        if len(completed.stdout) > 4096:
            raise ValueError("Oversized native response")
        result = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise RuntimeError("Calibration worker unavailable or invalid") from error
    if not isinstance(result, dict):
        raise RuntimeError("Invalid native response")
    return result


def verified_fit(points: list[dict[str, int]]) -> dict[str, Any]:
    """Gate every native field against independent rational computation, including unavailable statuses."""
    actual, expected = native_fit(points), reference_fit(points)
    if set(actual) != set(expected):
        raise RuntimeError("Native reference field disagreement")
    for key, value in expected.items():
        other = actual[key]
        if key in FIELDS and value is not None:
            if (
                type(other) not in (float, int)
                or not math.isfinite(other)
                or not math.isclose(other, value, rel_tol=REL_TOL, abs_tol=ABS_TOL)
            ):
                raise RuntimeError("Native reference numerical disagreement")
        elif type(other) is not type(value) or other != value:
            raise RuntimeError("Native reference status disagreement")
    return actual


def signal_status(point: dict[str, Any], config: dict[str, int]) -> str:
    """Treat missing as absent, and readings at either electronics rail as saturated (never zero-filled)."""
    y = point["signal_uv"]
    if y is None:
        return "missing"
    return "saturated" if y <= config["rail_low_uv"] or y >= config["rail_high_uv"] else "usable"


def fit_variance(fit: dict[str, Any], x: float) -> float:
    """Evaluate known-variance covariance propagation for the fitted mean response at x."""
    value = fit["var_a"] + 2 * x * fit["cov_ab"] + x * x * fit["var_b"]
    if value < -ABS_TOL or not math.isfinite(value):
        raise RuntimeError("Invalid covariance propagation")
    return max(0.0, float(value))


def analyze(data: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    """Fit only calibration rows, validate on disjoint supplied checks, then gate each corrected sample."""
    validate(data)
    config = data["config"]
    points = [p for p in data["calibration"] if signal_status(p, config) == "usable"]
    fit = verified_fit(points)
    calibration_rows = []
    for i, p in enumerate(data["calibration"]):
        row: dict[str, Any] = {
            "index": i,
            "x": p["x_milli"] / 1000,
            "y_mv": p["signal_uv"] / 1000 if p["signal_uv"] is not None else None,
            "u_mv": p["u_uv"] / 1000,
            "status": signal_status(p, config),
            "predicted_mv": None,
            "residual_mv": None,
        }
        if fit["status"] == "ok":
            row["predicted_mv"] = fit["a"] + fit["b"] * row["x"]
            if row["status"] == "usable":
                row["residual_mv"] = row["y_mv"] - row["predicted_mv"]
        calibration_rows.append(row)
    check_rows = []
    for i, p in enumerate(data["checks"]):
        status = signal_status(p, config)
        x = p["x_milli"] / 1000
        z = None
        if status == "usable" and fit["status"] == "ok":
            if not fit["xmin"] <= x <= fit["xmax"]:
                status = "outside-calibration-span"
            else:
                z = (p["signal_uv"] / 1000 - fit["a"] - fit["b"] * x) / math.sqrt(
                    (p["u_uv"] / 1000) ** 2 + fit_variance(fit, x)
                )
                status = "within-check" if abs(z) <= config["z_limit"] else "reference-mismatch"
        elif status == "usable":
            status = "model-unavailable"
        check_rows.append({"index": i, "x": x, "status": status, "z": z})
    usable_checks = [r for r in check_rows if r["z"] is not None]
    gate = fit["status"]
    if gate == "ok" and fit["chi2_reduced"] > config["chi_limit"]:
        gate = "fit-inconsistent"
    if gate == "ok" and (
        len(usable_checks) < 2 or any(r["status"] != "within-check" for r in usable_checks)
    ):
        gate = "check-validation-failed"
    if gate == "ok" and config["age_days"] > config["max_age_days"]:
        gate = "calibration-expired"
    rows = []
    for hour, p in enumerate(data["samples"]):
        status = signal_status(p, config)
        row = {
            "hour": hour,
            "signal_mv": p["signal_uv"] / 1000 if p["signal_uv"] is not None else None,
            "reference": p["reference_milli"] / 1000 if p["reference_milli"] is not None else None,
            "estimate": None,
            "u": None,
            "error": None,
            "z": None,
            "status": status,
        }
        if status == "usable" and gate != "ok":
            row["status"] = gate
        elif status == "usable":
            x = (row["signal_mv"] - fit["a"]) / fit["b"]
            if not fit["xmin"] <= x <= fit["xmax"]:
                row["status"] = "outside-calibration-span"
            else:
                uncertainty = math.sqrt((p["u_uv"] / 1000) ** 2 + fit_variance(fit, x)) / abs(
                    fit["b"]
                )
                row.update(estimate=x, u=uncertainty, status="estimated")
                if row["reference"] is not None:
                    error = x - row["reference"]
                    row.update(error=error, z=error / uncertainty)
                    if abs(row["z"]) > config["z_limit"]:
                        row["status"] = "reference-mismatch"
        rows.append(row)
    errors = [r["error"] for r in rows if r["error"] is not None]
    estimated = sum(r["estimate"] is not None for r in rows)
    summary = {
        "samples": len(rows),
        "estimated": estimated,
        "withheld": len(rows) - estimated,
        "reference_mismatches": sum(r["status"] == "reference-mismatch" for r in rows),
        "missing": sum(r["status"] == "missing" for r in rows),
        "saturated": sum(r["status"] == "saturated" for r in rows),
        "calibration_used": len(points),
        "calibration_excluded": len(data["calibration"]) - len(points),
        "checks_used": len(usable_checks),
        "evaluated_references": len(errors),
        "rmse": math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else None,
        "mean_error": sum(errors) / len(errors) if errors else None,
    }
    run: dict[str, Any] = {
        "schema": 1,
        "author": "Jason Stys",
        "name": data["name"],
        "settings": asdict(settings) if settings else None,
        "input": data,
        "fit": fit,
        "gate": gate,
        "calibration_rows": calibration_rows,
        "check_rows": check_rows,
        "rows": rows,
        "summary": summary,
        "verification": {
            "native_reference_verified": True,
            "absolute_tolerance": ABS_TOL,
            "relative_tolerance": REL_TOL,
        },
        "method": {
            "fit": "Known-response-variance WLS; C# centered moments checked by independent Python Fraction normal equations",
            "uncertainty": "First-order combined standard uncertainty from independent new response and fit covariance; no residual rescaling, reference uncertainty, correlation or certified coverage interval",
            "limits": "Synthetic fixed-unit linear calibration only; no hardware, physical traceability, certification, arbitrary curve fitting, causal drift diagnosis or extrapolation",
        },
    }
    run = normalized(run)
    run["id"] = hashlib.sha256(canonical(run)).hexdigest()
    return run


def build_run(settings: Settings) -> dict[str, Any]:
    """Analyze one finite synthetic preset; held-out references never participate in fitting."""
    return analyze(configuration(settings), settings)
