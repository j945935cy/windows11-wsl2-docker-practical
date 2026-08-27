#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${1:-$ROOT/backups/$STAMP}"
mkdir -p "$DEST"
ARCHIVE="$DEST/bookdb.sql.gz"
"$DOCKER_CMD" compose -f "$ROOT/compose.yaml" exec -T db \
  pg_dump -U "${POSTGRES_USER:-bookuser}" -d "${POSTGRES_DB:-bookdb}" \
  | gzip -9 > "$ARCHIVE"
python3 "$ROOT/scripts/backup_manifest.py" create "$ARCHIVE" "$DEST/manifest.json" \
  --database "${POSTGRES_DB:-bookdb}"
printf 'Backup created: %s\n' "$DEST/manifest.json"
