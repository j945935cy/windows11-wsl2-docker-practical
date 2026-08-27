#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_manifest(
    archive: Path, manifest: Path, database: str, created_utc: str | None = None
) -> None:
    if not archive.is_file():
        raise ValueError(f"archive does not exist: {archive}")
    payload = {
        "schema_version": 1,
        "database": database,
        "created_utc": created_utc or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "archive": archive.name,
        "sha256": sha256_file(archive),
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def verify_manifest(manifest: Path) -> Path:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    required = {"schema_version", "database", "created_utc", "archive", "sha256"}
    if data.keys() != required or data["schema_version"] != 1:
        raise ValueError("unsupported or incomplete manifest")
    archive_name = data["archive"]
    if Path(archive_name).name != archive_name:
        raise ValueError("archive must be beside manifest")
    archive = manifest.parent / archive_name
    if not archive.is_file():
        raise ValueError("archive is missing")
    if sha256_file(archive) != data["sha256"]:
        raise ValueError("backup checksum mismatch")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("archive", type=Path)
    create.add_argument("manifest", type=Path)
    create.add_argument("--database", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.command == "create":
        create_manifest(args.archive, args.manifest, args.database)
    else:
        print(verify_manifest(args.manifest))


if __name__ == "__main__":
    main()
