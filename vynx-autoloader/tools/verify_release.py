#!/usr/bin/env python3
"""Verify a built Vynx.dev Autoloader release without starting its servers."""

import argparse
import base64
import hashlib
import importlib.util
import io
import pathlib
import sys
import zipfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fail(message):
    raise SystemExit("verification failed: " + message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="2.0")
    parser.add_argument("--host", required=True, type=pathlib.Path)
    parser.add_argument("--elf", required=True, type=pathlib.Path)
    parser.add_argument("--dist", required=True, type=pathlib.Path)
    args = parser.parse_args()

    host_source = args.host.read_text(encoding="utf-8")
    compile(host_source, str(args.host), "exec")

    spec = importlib.util.spec_from_file_location("vynx_release_host", args.host)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.VERSION != args.version:
        fail(f"host version is {module.VERSION!r}, expected {args.version!r}")

    archive = base64.b64decode(module.EMBEDDED_ZIP_B64, validate=True)
    elf = args.elf.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        names = set(zf.namelist())
        required = {
            "index.html",
            "ps5-autoload/app.js",
            "ps5-autoload/selected_exploit",
            "ps5-autoload/payloads/payload.elf",
            "ps5-autoload/relapse/index.html",
            "ps5-autoload/slopkit/slopkit/poops.html",
            "ps5-autoload/umtx2/index.html",
        }
        missing = required - names
        if missing:
            fail("host archive is missing: " + ", ".join(sorted(missing)))
        if zf.read("ps5-autoload/payloads/payload.elf") != elf:
            fail("embedded bootstrap payload does not match the release installer ELF")
        unresolved = (b"[[VERSION_PLACEHOLDER]]", b"[[BUILD_TIME_PLACEHOLDER]]",
                      b"[[EXPLOIT_MODE]]", b"[[APP_DIR_PLACEHOLDER]]")
        checked = (zf.read("index.html") + zf.read("ps5-autoload/index.html") +
                   zf.read("ps5-autoload/app.js"))
        if any(token in checked for token in unresolved):
            fail("host archive contains unresolved build placeholders")

    app_dir = args.dist / "app" / ("v" + args.version)
    marker = app_dir / "__complete__"
    manifest_path = args.dist / "cache.appcache"
    pointer = args.dist / "app" / "index.html"
    if marker.read_text(encoding="utf-8").strip() != args.version:
        fail("__complete__ marker has the wrong version")
    staged = (pointer.read_bytes() + (app_dir / "index.html").read_bytes() +
              (app_dir / "ps5-autoload" / "index.html").read_bytes() +
              (app_dir / "ps5-autoload" / "app.js").read_bytes())
    if any(token in staged for token in unresolved):
        fail("stable pointer contains unresolved build placeholders")
    manifest = manifest_path.read_text(encoding="utf-8").splitlines()
    marker_url = f"/app/v{args.version}/__complete__"
    pointer_url = "/app/index.html"
    if marker_url not in manifest or pointer_url not in manifest:
        fail("manifest is missing the pointer or completeness marker")
    if manifest.index(marker_url) != manifest.index(pointer_url) + 1:
        fail("__complete__ is not the final cache entry after the stable pointer")
    if any(line.startswith(f"/app/{args.version}/") for line in manifest):
        fail("manifest contains an unprefixed version directory")

    print(f"OK: Vynx.dev Autoloader v{args.version}")
    print(f"  host archive: {len(names)} files")
    print(f"  installer ELF SHA-256: {sha256(elf)}")
    print(f"  host script SHA-256:   {sha256(args.host.read_bytes())}")


if __name__ == "__main__":
    sys.exit(main())
