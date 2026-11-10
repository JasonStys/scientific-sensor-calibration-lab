"""Freeze and verify portable calibration-lab bundles by Jason Stys. Index: docs/CODE_INDEX.md.

Function main; variables: fixed resources, notice paths, executable, archive digest. No installer/elevation.
"""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

if __package__:
    from .portable_archive import archive_metadata, create_archive, extract_archive
    from .release_contract import ROOT, asset_paths, configuration, require, source_metadata
else:
    from portable_archive import archive_metadata, create_archive, extract_archive
    from release_contract import ROOT, asset_paths, configuration, require, source_metadata


def main() -> int:
    """Freeze production assets with required notices, then accept a safely extracted archive."""
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Build and accept the extracted portable application"
    )
    parser.add_argument("--output-root", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    config, metadata = configuration(), source_metadata()
    generated = root / ".runtime/package-meta"
    generated.mkdir(parents=True, exist_ok=True)
    identity = generated / "RELEASE.json"
    identity.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
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
    command[command.index("launcher.py") : command.index("launcher.py")] = [
        "--add-data",
        str(identity) + ":sensorlab/resources",
    ]
    subprocess.run(command, cwd=root, check=True, timeout=600)
    executable_name = config["executable"]
    bundle = root / "dist" / executable_name
    shutil.copyfile(identity, bundle / "RELEASE.json")
    archive, checksum = asset_paths(metadata)
    archive, checksum = (
        args.output_root.resolve() / archive.name,
        args.output_root.resolve() / checksum.name,
    )
    archive.parent.mkdir(parents=True, exist_ok=True)
    require(not checksum.exists(), "Checksum destination already exists")
    create_archive(bundle, archive)
    require(
        archive_metadata(archive, executable_name) == metadata, "Created archive identity mismatch"
    )
    with tempfile.TemporaryDirectory(
        prefix="scientific-sensor-calibration-lab-extracted-"
    ) as temporary:
        extracted = extract_archive(archive, Path(temporary) / "unpacked", executable_name)
        executable = extracted / (executable_name + (".exe" if sys.platform == "win32" else ""))
        subprocess.run(
            [sys.executable, str(root / "tools/smoke_app.py"), str(executable)],
            cwd=temporary,
            check=True,
            timeout=120,
        )
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Extracted portable application passed: {archive.name} SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
