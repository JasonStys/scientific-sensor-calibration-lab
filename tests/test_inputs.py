"""Strict schemas, ranges, local input and native parser boundaries by Jason Stys. Index: docs/CODE_INDEX.md."""

import json
import subprocess

import pytest

from sensorlab.engine import ROOT, analyze
from sensorlab.model import CHOICES, CONFIG_RANGES, Settings, configuration, load_input, validate


@pytest.mark.parametrize("key", CONFIG_RANGES)
@pytest.mark.parametrize("bad", [True, None, 1.5, "1", 10000001])
def test_config_types(key, bad):
    """Primitive types and upper bounds never silently coerce into valid configuration."""
    data = configuration(Settings())
    data["config"][key] = bad
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("key", CHOICES)
def test_settings(key):
    """Boolean settings are invalid even when numerically equal to a permitted integer."""
    with pytest.raises(ValueError):
        Settings(**{key: True})


@pytest.mark.parametrize("kind", range(17))
def test_invalid_objects(kind):
    """Exact object keys, size, schema, unit, reference, signal and uncertainty bounds are required."""
    data = configuration(Settings())
    if kind == 0:
        data["schema"] = True
    elif kind == 1:
        data["extra"] = 0
    elif kind == 2:
        data["name"] = "../bad"
    elif kind == 3:
        data["unit"] = "<img>"
    elif kind == 4:
        data["provenance"] = ""
    elif kind == 5:
        data["config"]["rail_low_uv"] = 3000000
    elif kind == 6:
        data["calibration"] = []
    elif kind == 7:
        data["checks"] *= 20
    elif kind == 8:
        data["samples"] *= 8
    elif kind == 9:
        data["checks"][0] = {}
    elif kind == 10:
        data["samples"][0]["reference_milli"] = True
    elif kind == 11:
        data["calibration"][0]["x_milli"] = None
    elif kind == 12:
        data["calibration"][0]["u_uv"] = 0
    elif kind == 13:
        data["samples"][0]["signal_uv"] = "missing"
    elif kind == 14:
        data["config"] = []
    elif kind == 15:
        data["provenance"] = "x" * 241
    else:
        data = None
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("kind", ["oversize", "duplicate", "utf16", "depth", "syntax"])
def test_local_file(tmp_path, kind):
    """UTF-8 only, 64KiB, depth and duplicate-key constraints are applied before interpretation."""
    bodies = {
        "oversize": b" " * 65537,
        "duplicate": b'{"a":1,"a":2}',
        "utf16": json.dumps(configuration(Settings())).encode("utf-16"),
        "depth": b"[" * 2000,
        "syntax": b"{",
    }
    path = tmp_path / "input.json"
    path.write_bytes(bodies[kind])
    with pytest.raises(ValueError):
        load_input(path)


def test_maximum_and_replay(tmp_path):
    """The maximum supported dataset dimensions are usable and explicit local input round-trips."""
    data = configuration(Settings())
    data["calibration"] = (data["calibration"] * 8)[:64]
    data["checks"] = (data["checks"] * 13)[:64]
    data["samples"] *= 7
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_input(path) == data and len(analyze(data)["rows"]) == 168


@pytest.mark.parametrize(
    "body",
    [
        b"{",
        b"[]",
        b'{"points":[],"points":[]}',
        b'{"points":[{"x_milli":true,"signal_uv":1,"u_uv":1}]}',
        b'{"points":[{"x_milli":1,"signal_uv":1,"u_uv":0}]}',
        b" " * 65537,
        b"\xff",
    ],
    ids=["syntax", "array", "duplicate", "boolean", "zero-uncertainty", "oversized", "utf8"],
)
def test_real_native_parser(body):
    """Exercise the actual C# CLI boundary, including malformed UTF-8 and oversized input."""
    result = subprocess.run(
        ["dotnet", str(ROOT / "calibration-core/bin/Release/net10.0/CalibrationCore.dll")],
        input=body,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2 and result.stdout == b"" and b"Invalid bounded" in result.stderr
