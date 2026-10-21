"""Analytical, differential and quality-gate contracts by Jason Stys. Function/variable index: docs/CODE_INDEX.md."""

import copy
import itertools
import math
import subprocess

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from sensorlab import engine
from sensorlab.model import CASES, CHOICES, Settings, configuration


def analytical():
    """Construct a perfect y=10+2x line with known 1mV standard uncertainty and separate checks."""
    data = configuration(Settings())
    data["config"].update(rail_low_uv=-10000000, rail_high_uv=10000000)
    data["calibration"] = [
        {"x_milli": i * 1000, "signal_uv": 10000 + i * 2000, "u_uv": 1000} for i in range(5)
    ]
    data["checks"] = [
        {"x_milli": i * 1000, "signal_uv": 10000 + i * 2000, "u_uv": 1000} for i in (1, 3)
    ]
    data["samples"] = [{"signal_uv": 14000, "u_uv": 1000, "reference_milli": 2000}]
    return data


@pytest.mark.parametrize("values", list(itertools.product(CASES, *CHOICES.values())))
def test_all_controls(values):
    """All162 presets cross-check the real C# core, never a mocked replacement."""
    run = engine.build_run(Settings(*values))
    assert run["verification"]["native_reference_verified"]
    assert run["summary"]["estimated"] + run["summary"]["withheld"] == 24
    assert all((r["estimate"] is None) == (r["u"] is None) for r in run["rows"])


def test_analytical_coefficients_covariance_and_inverse():
    """Independently derived normal-equation values and first-order inverse uncertainty must match."""
    run = engine.analyze(analytical())
    for key, value in {
        "a": 10,
        "b": 2,
        "var_a": 0.6,
        "var_b": 0.1,
        "cov_ab": -0.2,
        "chi2_reduced": 0,
    }.items():
        assert run["fit"][key] == pytest.approx(value)
    row = run["rows"][0]
    assert row["estimate"] == 2 and row["error"] == 0 and row["status"] == "estimated"
    assert row["u"] == pytest.approx(math.sqrt(1.2) / 2)


def test_uncertainty_scaling_and_no_holdout_leakage():
    """Declared response uncertainty scales covariance; check data never changes fitted coefficients."""
    data = analytical()
    original = engine.analyze(data)
    for row in data["calibration"]:
        row["u_uv"] *= 2
    scaled = engine.analyze(data)
    assert scaled["fit"]["b"] == original["fit"]["b"]
    assert scaled["fit"]["var_b"] == pytest.approx(4 * original["fit"]["var_b"])
    data["checks"][0]["signal_uv"] += 100000
    changed = engine.analyze(data)
    assert changed["fit"] == scaled["fit"]
    assert changed["gate"] == "check-validation-failed" and changed["rows"][0]["estimate"] is None


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("missing", "missing"),
        ("saturation", "saturated"),
        ("outside", "outside-calibration-span"),
        ("expired", "calibration-expired"),
        ("flat", "noninvertible-fit"),
        ("span", "insufficient-span"),
        ("few", "insufficient-calibration"),
        ("checks", "check-validation-failed"),
    ],
)
def test_withholding(kind, expected):
    """Unsupported corrections retain the observation/status but withhold fabricated estimates and uncertainty."""
    data = analytical()
    if kind == "missing":
        data["samples"][0]["signal_uv"] = None
    if kind == "saturation":
        data["samples"][0]["signal_uv"] = data["config"]["rail_high_uv"]
    if kind == "outside":
        data["samples"][0]["signal_uv"] = 30000
    if kind == "expired":
        data["config"]["age_days"] = 91
    if kind == "flat":
        for row in data["calibration"]:
            row["signal_uv"] = 10000
    if kind == "span":
        for row in data["calibration"]:
            row["x_milli"] = 1
    if kind == "few":
        data["calibration"] = data["calibration"][:3]
    if kind == "checks":
        data["checks"][0]["signal_uv"] = None
    run = engine.analyze(data)
    assert run["rows"][0]["status"] == expected
    assert run["rows"][0]["estimate"] is None and run["rows"][0]["u"] is None
    assert run["summary"]["rmse"] is None


def test_age_boundary_negative_slope_and_unknown_reference():
    """Age limit is inclusive; negative sensitivities invert correctly; absent reference produces no error score."""
    data = analytical()
    data["config"]["age_days"] = 90
    for row in data["calibration"] + data["checks"]:
        row["signal_uv"] = 20000 - 2 * row["x_milli"]
    data["samples"][0].update(signal_uv=16000, reference_milli=None)
    run = engine.analyze(data)
    assert run["gate"] == "ok" and run["fit"]["b"] == -2
    assert run["rows"][0]["estimate"] == 2
    assert run["rows"][0]["error"] is None and run["summary"]["evaluated_references"] == 0


def test_scenarios_and_exclusions():
    """Drift is a reference-mismatch signal, clipping/range are distinct, and nonlinear fits are not silently accepted."""
    assert (
        engine.build_run(Settings(scenario="sensor-drift"))["summary"]["reference_mismatches"] > 0
    )
    sat = engine.build_run(Settings(scenario="saturation"))
    assert sat["summary"]["saturated"] == 2
    assert sat["rows"][18]["status"] == "outside-calibration-span"
    missing = engine.build_run(Settings(scenario="missing-data"))
    assert missing["summary"]["missing"] == 2 and missing["summary"]["calibration_excluded"] == 2
    assert engine.build_run(Settings(scenario="nonlinear-response"))["gate"] == "fit-inconsistent"


@pytest.mark.parametrize("fault", ["fields", "number", "status", "nan", "bool"])
def test_native_mismatch_fails_closed(monkeypatch, fault):
    """Malformed/corrupted native responses cannot acquire a verified badge."""
    actual = engine.native_fit(analytical()["calibration"])
    if fault == "fields":
        actual["extra"] = 1
    if fault == "number":
        actual["b"] += 1
    if fault == "status":
        actual["status"] = "other"
    if fault == "nan":
        actual["var_a"] = float("nan")
    if fault == "bool":
        actual["n"] = True
    monkeypatch.setattr(engine, "native_fit", lambda points: actual)
    with pytest.raises(RuntimeError):
        engine.analyze(analytical())


def test_native_failures(monkeypatch):
    """Timeout, missing executable, oversized/malformed output and non-object payloads fail generically."""

    def fail(*args, **kwargs):
        """Inject timeout from the process boundary, not from the mathematical reference."""
        raise subprocess.TimeoutExpired("worker", 10)

    monkeypatch.setattr(engine.subprocess, "run", fail)
    with pytest.raises(RuntimeError):
        engine.analyze(analytical())
    for body in (b"x" * 5000, b"{", b"[]"):
        monkeypatch.setattr(
            engine.subprocess,
            "run",
            lambda *args, body=body, **kwargs: subprocess.CompletedProcess([], 0, body, b""),
        )
        with pytest.raises(RuntimeError):
            engine.native_fit([])
    with pytest.raises(RuntimeError):
        engine.fit_variance({"var_a": -1, "var_b": 0, "cov_ab": 0}, 0)


@settings(max_examples=60, deadline=None, derandomize=True)
@given(
    st.lists(
        st.tuples(
            st.integers(-1000000, 1000000), st.integers(-9000000, 9000000), st.integers(1, 100000)
        ),
        min_size=4,
        max_size=24,
    )
)
def test_generated_native_differential(rows):
    """Sixty generated fit problems probe centered-double versus exact-rational numerical stability."""
    points = [dict(zip(("x_milli", "signal_uv", "u_uv"), r, strict=True)) for r in rows]
    assert engine.verified_fit(points)["n"] == len(rows)


def test_identity_and_no_mutation():
    """Content identity is deterministic without mutating original input or fitting to monitoring references."""
    data = analytical()
    before = copy.deepcopy(data)
    assert engine.analyze(data) == engine.analyze(data) and data == before
    original = engine.analyze(data)
    data["samples"][0]["reference_milli"] = 1000
    changed = engine.analyze(data)
    assert original["fit"] == changed["fit"] and original["id"] != changed["id"]
