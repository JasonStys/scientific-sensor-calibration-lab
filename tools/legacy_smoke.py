"""Exercise a freshly reviewed frozen app by Jason Stys. Functions/variables: docs/CODE_INDEX.md.
Preserved domain acceptance; canonical process/version/browser proof is in smoke_app.py."""

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

if __package__:
    from .release_contract import require
else:
    from release_contract import require


class RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """A local application check never follows an HTTP redirect to another listener or origin."""

    def redirect_request(self, *args, **kwargs):
        """Abort before urllib can issue the redirected request."""
        raise ValueError("Local native acceptance refuses redirects")


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), RefuseRedirects())


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
        require(bool((internal / "licenses" / name).is_file()), name)
    for name in ("LICENSE.txt", "THIRD-PARTY-NOTICES.txt", "CalibrationCore.runtimeconfig.json"):
        require(bool((internal / "native" / name).is_file()), name)
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
        require(
            bool(result["rows"][4]["estimate"] is None), "Preserved native acceptance check failed"
        )
        require(
            bool(result["verification"]["native_reference_verified"]),
            "Preserved native acceptance check failed",
        )
        require(bool(result["summary"]["missing"] == 2), "Preserved native acceptance check failed")
        require(
            bool(len((folder / "csv").read_text().splitlines()) == 25),
            "Preserved native acceptance check failed",
        )
        require(
            bool(b"<script" not in (folder / "html").read_bytes()),
            "Preserved native acceptance check failed",
        )
        with closing(sqlite3.connect(folder / "history.sqlite3")) as db:
            require(
                bool(db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1),
                "Preserved native acceptance check failed",
            )
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
        require(
            bool(json.loads((folder / "replayed.json").read_bytes())["rows"] == result["rows"]),
            "Preserved native acceptance check failed",
        )
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read owned process stdout off-thread so startup cannot wait without a deadline."""
        require(bool(process.stdout), "Preserved native acceptance check failed")
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
        require(bool(url), "Preserved native acceptance check failed")
        for route in ("api/health", "", "api/run"):
            with OPENER.open(url + route, timeout=30) as response:
                body = response.read()
                if not route:
                    require(
                        bool(b"DATUM" in body and b"/assets/" in body),
                        "Preserved native acceptance check failed",
                    )
                elif route == "api/run":
                    run = json.loads(body)
                    require(
                        bool(len(run["rows"]) == 24), "Preserved native acceptance check failed"
                    )
                    require(
                        bool(run["verification"]["native_reference_verified"]),
                        "Preserved native acceptance check failed",
                    )
                else:
                    require(
                        bool(json.loads(body)["status"] == "ok"),
                        "Preserved native acceptance check failed",
                    )
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
