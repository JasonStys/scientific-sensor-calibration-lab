"""Exercise a freshly reviewed frozen app by Jason Stys. Functions/variables: docs/CODE_INDEX.md."""

import json
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.request
from contextlib import closing
from pathlib import Path


def main(executable: Path) -> None:
    """Verify real exports, replay, SQL, notices and loopback web UI; always stop only this process."""
    executable = executable.resolve(strict=True)
    internal = executable.parent / "_internal"
    for name in (
        "project/LICENSE",
        "python/PYTHON.txt",
        "pyinstaller/COPYING.txt",
        "vite/LICENSE.md",
    ):
        assert (internal / "licenses" / name).is_file(), name
    for name in ("LICENSE.txt", "THIRD-PARTY-NOTICES.txt", "CalibrationCore.runtimeconfig.json"):
        assert (internal / "native" / name).is_file(), name
    with tempfile.TemporaryDirectory(prefix="sensor-smoke-") as temporary:
        folder = Path(temporary)
        for format_name in ("json", "csv", "html", "input"):
            subprocess.run(
                [
                    str(executable),
                    "export",
                    "--scenario",
                    "missing-data",
                    "--format",
                    format_name,
                    "--output",
                    str(folder / format_name),
                    "--history",
                    str(folder / "history.sqlite3"),
                ],
                check=True,
                timeout=30,
            )
        result = json.loads((folder / "json").read_bytes())
        assert result["rows"][4]["estimate"] is None
        assert result["verification"]["native_reference_verified"]
        assert result["summary"]["missing"] == 2
        assert len((folder / "csv").read_text().splitlines()) == 25
        assert b"<script" not in (folder / "html").read_bytes()
        with closing(sqlite3.connect(folder / "history.sqlite3")) as db:
            assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1
        subprocess.run(
            [
                str(executable),
                "export",
                "--input",
                str(folder / "input"),
                "--output",
                str(folder / "replayed.json"),
            ],
            check=True,
            timeout=30,
        )
        assert json.loads((folder / "replayed.json").read_bytes())["rows"] == result["rows"]
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read owned process stdout off-thread so startup cannot wait without a deadline."""
        assert process.stdout
        for line in process.stdout:
            lines.put(line.strip())

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        url = ""
        for _ in range(6):
            line = lines.get(timeout=15)
            if line.startswith("http://127.0.0.1:"):
                url = line
                break
        assert url
        for route in ("api/health", "", "api/run"):
            with urllib.request.urlopen(url + route, timeout=30) as response:
                body = response.read()
                if not route:
                    assert b"DATUM" in body and b"/assets/" in body
                elif route == "api/run":
                    run = json.loads(body)
                    assert len(run["rows"]) == 24
                    assert run["verification"]["native_reference_verified"]
                else:
                    assert json.loads(body)["status"] == "ok"
        print(
            "Frozen C# fit/reference, missing-value exports, replay, SQL, notices and HTTP UI passed"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=3)
        if process.stdout:
            process.stdout.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
