"""Portable export and CPU/HIP execution of SketchyUp's unchanged Blender adapter."""

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(value):
    found = shutil.which(value)
    if not found:
        raise RuntimeError(f"Executable not found: {value}")
    return str(Path(found).resolve())


def run(command, log, seconds, env=None):
    with log.open("w") as stream:
        subprocess.run(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=seconds,
            check=True,
            env=env,
        )


def fresh(path):
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise RuntimeError(f"Use a new empty output directory: {path}")
    return path


def export(args):
    """Build and capture only. This function never discovers or executes Blender."""
    out = fresh(args.output)
    cli = executable(args.cli)
    started = time.monotonic()
    # The generator calls the published CLI name. A temporary PATH entry supports
    # arbitrary build/package executable paths without changing model generation.
    with tempfile.TemporaryDirectory(prefix="build-", dir=out) as scratch:
        scratch = Path(scratch)
        bindir = scratch / "bin"
        bindir.mkdir()
        (bindir / "sketchyup-cli").symlink_to(cli)
        env = dict(
            os.environ, PATH=str(bindir) + os.pathsep + os.environ.get("PATH", "")
        )
        build = scratch / "model"
        run(
            [
                sys.executable,
                str(ROOT / "docs/images/showcase/build_showcase.py"),
                str(build),
            ],
            out / "build.log",
            300,
            env,
        )
        for name in [
            "showcase.sketchyup",
            "stats.json",
            "document.json",
            "sheet-preflight.json",
        ]:
            shutil.copyfile(build / name, out / name)
    run(
        [
            sys.executable,
            str(ROOT / "docs/images/showcase/sky_environment.py"),
            str(out / "sky.hdr"),
        ],
        out / "sky.log",
        30,
    )
    settings = {
        "apiVersion": 1,
        "width": 1440,
        "height": 900,
        "samples": args.samples,
        "seed": 17,
        "environment": {
            "path": str(out / "sky.hdr"),
            "strength": 0.65,
            "rotationDegrees": 0,
        },
        "camera": {
            "projection": "perspective",
            "position": [-10, -20, 6],
            "target": [5, 1, 1.9],
            "up": [0, 0, 1],
            "verticalFov": math.radians(43),
            "nearClip": 0.01,
            "farClip": 1000,
        },
    }
    settings_path = out / "settings.json"
    write_json(settings_path, settings)
    run(
        [
            cli,
            "--input",
            str(out / "showcase.sketchyup"),
            "--export-glb",
            str(out / "snapshot"),
            "--render-settings",
            str(settings_path),
        ],
        out / "export.log",
        120,
    )
    # The transfer bundle contains no dependency on the exporting machine's paths.
    settings["environment"]["path"] = "sky.hdr"
    write_json(settings_path, settings)
    shutil.copyfile(
        ROOT / "src/integrations/blender_worker.py", out / "blender_worker.py"
    )
    files = ["showcase.sketchyup", "settings.json", "sky.hdr", "blender_worker.py"]
    files += [
        str(p.relative_to(out))
        for p in sorted((out / "snapshot").rglob("*"))
        if p.is_file()
    ]
    write_json(
        out / "bundle.json",
        {
            "apiVersion": 1,
            "files": {p: digest(out / p) for p in files},
            "exportSeconds": round(time.monotonic() - started, 2),
        },
    )
    print(f"Export complete; Blender was not invoked. Copy this whole directory: {out}")


def worker(args, adapter, directory, request):
    directory.mkdir(parents=True, exist_ok=True)
    request_file = directory / "request.json"
    write_json(request_file, request)
    started = time.monotonic()
    run(
        [
            executable("systemd-run"),
            "--user",
            "--scope",
            "-q",
            "-p",
            "MemoryMax=8G",
            "-p",
            "MemorySwapMax=0",
            "timeout",
            "--foreground",
            str(args.timeout),
            executable(args.blender),
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--threads",
            "4",
            "--python-exit-code",
            "1",
            "--python",
            str(adapter),
            "--",
            str(request_file),
        ],
        directory / "blender.log",
        args.timeout + 30,
    )
    result = json.loads((directory / "result.json").read_text())
    write_json(
        directory / "elapsed.json", {"seconds": round(time.monotonic() - started, 2)}
    )
    if result["status"] not in ("available", "succeeded"):
        raise RuntimeError(f"Adapter failed: {result}")
    if result["blenderVersion"] != [5, 2, 2]:
        raise RuntimeError(
            f"This showcase requires Blender 5.2.2; got {result['blenderVersion']}"
        )
    return result


def probe(args):
    out = fresh(args.output)
    result = worker(
        args,
        ROOT / "src/integrations/blender_worker.py",
        out,
        {
            "apiVersion": 1,
            "operation": "probe",
            "backend": args.backend,
            "deviceId": "",
        },
    )
    print(json.dumps(result, indent=2))


def render(args):
    source = args.input.resolve()
    bundle = json.loads((source / "bundle.json").read_text())
    for name, expected in bundle["files"].items():
        if digest(source / name) != expected:
            raise RuntimeError(f"Export bundle changed: {name}")
    out = fresh(args.output)
    adapter = source / "blender_worker.py"
    info = worker(
        args,
        adapter,
        out / "probe",
        {
            "apiVersion": 1,
            "operation": "probe",
            "backend": args.backend,
            "deviceId": "",
        },
    )
    devices = info["devices"]
    device_id = args.device_id
    if device_id is None:
        if len(devices) != 1:
            raise RuntimeError(
                f"Choose --device-id from these {args.backend} devices: {devices}"
            )
        device_id = devices[0]["id"]
    if not any(d["id"] == device_id for d in devices):
        raise RuntimeError(
            f"Requested device is unavailable: {device_id}; devices: {devices}"
        )
    snapshot = source / "snapshot"
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if args.samples is not None and args.samples != manifest["settings"]["samples"]:
        # Samples are immutable snapshot settings. Re-export through SketchyUp,
        # retaining the original snapshot and native document, never patch a manifest.
        settings = json.loads((source / "settings.json").read_text())
        settings["samples"] = args.samples
        settings["environment"]["path"] = str(source / "sky.hdr")
        write_json(out / "settings.json", settings)
        snapshot = out / "snapshot"
        run(
            [
                executable(args.cli),
                "--input",
                str(source / "showcase.sketchyup"),
                "--export-glb",
                str(snapshot),
                "--render-settings",
                str(out / "settings.json"),
            ],
            out / "export.log",
            120,
        )
    result = worker(
        args,
        adapter,
        out,
        {
            "apiVersion": 1,
            "operation": "render",
            "backend": args.backend,
            "deviceId": device_id,
            "sourceDirectory": str(snapshot),
            "manifestSha256": digest(snapshot / "manifest.json"),
        },
    )
    if digest(out / "image.png") != result["image"]["sha256"]:
        raise RuntimeError("Rendered image does not match the adapter result")
    print(
        json.dumps(
            {k: result[k] for k in ["status", "device", "settings", "preset"]}, indent=2
        )
    )
    print(f"Render: {out / 'image.png'}")
    # Rendering never writes a repository image or social preview implicitly.
    if args.publish:
        image_tool = shutil.which("magick") or executable("convert")
        run(
            [
                image_tool,
                str(out / "image.png"),
                "-strip",
                "-dither",
                "None",
                "-colors",
                "256",
                "-define",
                "png:compression-level=9",
                "PNG8:" + str(args.publish),
            ],
            out / "publish.log",
            60,
        )
        if args.publish.stat().st_size > 500000:
            raise RuntimeError(f"Published image exceeds 500 KB: {args.publish}")


def sample_count(value):
    value = int(value)
    if not 1 <= value <= 1024:
        raise argparse.ArgumentTypeError("samples must be in 1..1024")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser(
        "export", help="Build and export a portable bundle; never run Blender"
    )
    p.add_argument("output", type=Path)
    p.add_argument("--samples", type=sample_count, default=160)
    p.add_argument("--cli", default=os.environ.get("SKETCHYUP_CLI", "sketchyup-cli"))
    p.set_defaults(action=export)
    for name, action in [("probe", probe), ("render", render)]:
        p = commands.add_parser(name)
        if name == "render":
            p.add_argument("input", type=Path)
            p.add_argument(
                "--device-id",
                help="Exact adapter-probed ID; auto-select only when exactly one exists",
            )
            p.add_argument(
                "--samples",
                type=sample_count,
                help="Re-export a new snapshot if samples differ",
            )
            p.add_argument(
                "--cli", default=os.environ.get("SKETCHYUP_CLI", "sketchyup-cli")
            )
            p.add_argument(
                "--publish", type=Path, help="Optional 1440x900 PNG under 500 KB"
            )
        p.add_argument("output", type=Path)
        p.add_argument("--backend", choices=["CPU", "HIP"], default="CPU")
        p.add_argument("--blender", default=os.environ.get("BLENDER", "blender"))
        p.add_argument(
            "--timeout",
            type=int,
            choices=range(1, 1801),
            default=1200,
            metavar="SECONDS",
        )
        p.set_defaults(action=action)
    args = parser.parse_args()
    args.action(args)


if __name__ == "__main__":
    main()
