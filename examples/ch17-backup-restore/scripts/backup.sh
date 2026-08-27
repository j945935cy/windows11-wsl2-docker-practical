#!/usr/bin/env bash
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
PROJECT_NAME="${PROJECT_NAME:-book-ch17}"
case "$PROJECT_NAME" in book-ch17|book-ch17-*) ;; *) printf 'Refusing project: %s\n' "$PROJECT_NAME" >&2; exit 2;; esac
DEST="${1:?usage: backup.sh DESTINATION_OUTSIDE_REPOSITORY}"
ROOT_REAL="$(realpath "$ROOT")"
DEST_REAL="$(realpath -m "$DEST")"
case "$DEST_REAL" in
  "$ROOT_REAL"|"$ROOT_REAL"/*)
    printf 'Refusing backup destination inside repository: %s\n' "$DEST_REAL" >&2
    exit 2
    ;;
esac
install -d -m 700 "$DEST_REAL"
ARCHIVE="$DEST_REAL/bookdb.dump"
"$DOCKER_CMD" compose -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  pg_dump -U "${POSTGRES_USER:-bookuser}" -d "${POSTGRES_DB:-bookdb}" -Fc \
  > "$ARCHIVE"
chmod 600 "$ARCHIVE"
python3 "$ROOT/scripts/backup_manifest.py" create "$ARCHIVE" "$DEST_REAL/manifest.json" \
  --database "${POSTGRES_DB:-bookdb}"
chmod 600 "$DEST_REAL/manifest.json"
printf 'Backup created: %s\n' "$DEST_REAL/manifest.json"
