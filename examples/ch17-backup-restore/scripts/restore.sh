#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
MANIFEST="${1:?usage: restore.sh PATH/manifest.json}"
ARCHIVE="$(python3 "$ROOT/scripts/backup_manifest.py" verify "$MANIFEST")"
gzip -cd -- "$ARCHIVE" | "$DOCKER_CMD" compose -f "$ROOT/compose.yaml" exec -T db \
  psql --set ON_ERROR_STOP=1 -U "${POSTGRES_USER:-bookuser}" -d "${POSTGRES_DB:-bookdb}"
printf 'Restore completed from: %s\n' "$ARCHIVE"
