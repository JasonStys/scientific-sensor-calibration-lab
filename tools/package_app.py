"""Freeze and verify portable calibration-lab bundles by Jason Stys. Index: docs/CODE_INDEX.md.

Function main; variables: fixed resources, notice paths, executable, archive digest. No installer/elevation.
"""

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path


def main() -> None:
    """Include production assets, SQL and actual runtime notices; smoke before creating an unsigned ZIP."""
    root = Path(__file__).resolve().parents[1]
    if not (root / "web/dist/index.html").is_file():
        raise SystemExit("Build production assets first")
    rid = {"Windows": "win-x64", "Linux": "linux-x64", "Darwin": "osx-arm64"}[platform.system()]
    runtime_lock = root / ".runtime/publish.lock.json"
    runtime_lock.parent.mkdir(exist_ok=True)
    subprocess.run(
        [
            "dotnet",
            "publish",
            "calibration-core",
            "-c",
            "Release",
            "-r",
            rid,
            "--self-contained",
            "true",
            "-o",
            "native-dist",
            "-p:DebugType=None",
            "-p:NuGetLockFilePath=" + str(runtime_lock),
        ],
        cwd=root,
        check=True,
        timeout=300,
    )
    worker = (
        root
        / "native-dist"
        / ("CalibrationCore.exe" if sys.platform == "win32" else "CalibrationCore")
    )
    subprocess.run([str(worker), "--self-test"], check=True, timeout=30)
    runtime = json.loads((root / "native-dist/CalibrationCore.runtimeconfig.json").read_bytes())
    versions = [
        entry["version"]
        for entry in runtime["runtimeOptions"]["includedFrameworks"]
        if entry["name"] == "Microsoft.NETCore.App"
    ]
    if len(versions) != 1:
        raise SystemExit("Expected one self-contained .NET runtime")
    cache = Path(
        subprocess.check_output(
            ["dotnet", "nuget", "locals", "global-packages", "--list"], text=True
        )
        .strip()
        .split(": ", 1)[1]
    )
    pack = cache / ("microsoft.netcore.app.runtime." + rid) / versions[0]
    for notice in ("LICENSE.txt", "THIRD-PARTY-NOTICES.txt"):
        source = pack / notice.upper()
        if not source.is_file():
            raise SystemExit("Expected actual .NET runtime pack notice")
        shutil.copy2(source, root / "native-dist" / notice)
        if not (root / "native-dist" / notice).is_file():
            raise SystemExit("Expected actual .NET runtime notices")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "ScientificSensorCalibrationLab",
    ]
    for source, destination in (
        ("web/dist", "web/dist"),
        ("sensorlab/resources", "sensorlab/resources"),
        ("LICENSE", "licenses/project"),
        ("licenses/PYTHON.txt", "licenses/python"),
        ("docs/THIRD_PARTY.md", "docs"),
        ("node_modules/vite/LICENSE.md", "licenses/vite"),
    ):
        command.extend(["--add-data", source + ":" + destination])
    package = distribution("pyinstaller")
    notices = [
        package.locate_file(path)
        for path in package.files or []
        if str(path).endswith("licenses/COPYING.txt")
    ]
    if len(notices) != 1:
        raise SystemExit("Expected locked PyInstaller license")
    command.extend(["--add-data", str(notices[0]) + ":licenses/pyinstaller"])
    command.extend(["--add-binary", str(worker) + ":native"])
    for source in sorted((root / "native-dist").rglob("*")):
        if source.is_file() and source != worker:
            relative = source.relative_to(root / "native-dist")
            command.extend(
                ["--add-data", str(source) + ":" + (Path("native") / relative.parent).as_posix()]
            )
    if sys.platform == "linux":
        for notice in (
            "/usr/share/doc/libstdc++6/copyright",
            "/usr/share/doc/libgcc-s1/copyright",
            "/usr/share/common-licenses/GPL-3",
        ):
            source = Path(notice)
            if not source.is_file():
                raise SystemExit("Expected Ubuntu/Debian runtime notices")
            command.extend(
                ["--add-data", str(source) + ":licenses/compiler-runtime/" + source.parent.name]
            )
    command.append("launcher.py")
    subprocess.run(command, cwd=root, check=True, timeout=600)
    executable = (
        root
        / "dist/ScientificSensorCalibrationLab"
        / (
            "ScientificSensorCalibrationLab.exe"
            if sys.platform == "win32"
            else "ScientificSensorCalibrationLab"
        )
    )
    subprocess.run(
        [sys.executable, "tools/smoke_app.py", str(executable)], cwd=root, check=True, timeout=120
    )
    slug = f"scientific-sensor-calibration-lab-{platform.system().lower()}-{platform.machine().lower()}"
    archive = Path(
        shutil.make_archive(
            str(root / "dist" / slug), "zip", root / "dist", "ScientificSensorCalibrationLab"
        )
    )
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (root / "dist" / (slug + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Verified portable bundle: {archive.name} SHA-256 {digest}")


if __name__ == "__main__":
    main()
