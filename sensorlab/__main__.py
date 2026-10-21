"""Local calibration-lab CLI by Jason Stys. Function main and argument locations: docs/CODE_INDEX.md.

No network sources, hardware commands or shell commands; output files are create-only.
"""

import argparse
import sqlite3
import sys
import webbrowser
from pathlib import Path

from sensorlab.engine import ROOT, analyze, build_run
from sensorlab.model import CASES, CHOICES, Settings, load_input
from sensorlab.reports import export_report, save_history
from sensorlab.server import make_server


def main(argv: list[str] | None = None) -> int:
    """Launch read-only loopback UI or save explicitly requested, independently checked evidence."""
    parser = argparse.ArgumentParser(description="Scientific Sensor Calibration Lab by Jason Stys")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--no-browser", action="store_true")
    export = commands.add_parser("export")
    export.add_argument("--scenario", choices=CASES, default=Settings().scenario)
    for key, choices in CHOICES.items():
        export.add_argument("--" + key, type=int, choices=choices, default=getattr(Settings(), key))
    export.add_argument("--input", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--history", type=Path)
    export.add_argument("--format", choices=("json", "input", "csv", "html"), default="json")
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            if args.output.exists():
                raise FileExistsError("Destination already exists")
            settings = Settings(**{key: getattr(args, key) for key in ("scenario", *CHOICES)})
            run = analyze(load_input(args.input)) if args.input else build_run(settings)
            body, _ = export_report(run, args.format)
            if args.history:
                save_history(args.history, run)
            with args.output.open("xb") as stream:
                stream.write(body)
            print("Saved " + run["id"])
            return 0
        assets = ROOT / "web/dist"
        if not (assets / "index.html").is_file():
            raise OSError("Build web assets first")
        with make_server(assets, args.port) as server:
            url = f"http://127.0.0.1:{server.server_port}/"
            print("Scientific Sensor Calibration Lab by Jason Stys\n" + url, flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever(poll_interval=0.25)
            except KeyboardInterrupt:
                print("Calibration lab stopped.", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"Cannot complete: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
