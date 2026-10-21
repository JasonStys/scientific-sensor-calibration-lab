"""Exports, immutable SQL and create-only local CLI by Jason Stys. Index: docs/CODE_INDEX.md."""

import csv
import io
import json
import sqlite3
from contextlib import closing

import pytest

from sensorlab.__main__ import main
from sensorlab.engine import analyze, build_run, canonical
from sensorlab.model import Settings, configuration
from sensorlab.reports import export_report, save_history


def test_exports():
    """JSON/input round-trip, CSV preserves unavailable cells, and report HTML cannot execute provenance."""
    data = configuration(Settings(scenario="missing-data"))
    data["provenance"] = '<img src=x onerror="alert(1)"><script>bad</script>'
    run = analyze(data)
    assert json.loads(export_report(run, "json")[0]) == run
    assert json.loads(export_report(run, "input")[0]) == data
    rows = list(csv.DictReader(io.StringIO(export_report(run, "csv")[0].decode())))
    assert len(rows) == 24 and rows[4]["signal_mv"] == "" and rows[4]["estimate"] == ""
    body = export_report(run, "html")[0]
    assert b"<script>" not in body and b"<img " not in body and b"&lt;img" in body
    with pytest.raises(ValueError):
        export_report(run, "exe")


def test_history(tmp_path):
    """Verify identity, immutable/idempotent SQL, 100-record cap, no pruning and explicit Windows close."""
    path = tmp_path / "private.sqlite3"
    run = build_run(Settings())
    save_history(path, run)
    save_history(path, run)
    with closing(sqlite3.connect(path)) as db, db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1
        assert json.loads(db.execute("SELECT report_json FROM runs").fetchone()[0]) == run
        for sql in ("DELETE FROM runs", "UPDATE runs SET report_json='{}'"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql)
        for i in range(99):
            db.execute(
                "INSERT INTO runs(id,report_json) VALUES(?,?)",
                (f"{i:064x}", canonical(run).decode()),
            )
    with pytest.raises(ValueError, match="History full"):
        save_history(path, build_run(Settings(age=60)))
    run["author"] = "altered"
    with pytest.raises(ValueError, match="identity"):
        save_history(path, run)
    path.unlink()


def test_cli(tmp_path, monkeypatch):
    """Files are explicit/create-only and replayed input retains missing data, not zero imputation."""
    target = tmp_path / "evidence.json"
    assert (
        main(["export", "--output", str(target), "--history", str(tmp_path / "history.sqlite3")])
        == 0
    )
    assert main(["export", "--output", str(target)]) == 1
    source = tmp_path / "input.json"
    source.write_bytes(canonical(configuration(Settings(age=120))))
    replay = tmp_path / "replay.json"
    assert main(["export", "--input", str(source), "--output", str(replay)]) == 0
    assert json.loads(replay.read_bytes())["summary"]["estimated"] == 0
    assert (
        main(
            [
                "export",
                "--input",
                str(tmp_path / "missing.json"),
                "--output",
                str(tmp_path / "no.json"),
            ]
        )
        == 1
    )
    monkeypatch.setattr("sensorlab.__main__.ROOT", tmp_path)
    assert main(["serve", "--no-browser"]) == 1
