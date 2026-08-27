#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
COMPOSE_ENV_ARGS=()
if [[ -n "${COMPOSE_ENV_FILE:-}" ]]; then
  COMPOSE_ENV_ARGS=(--env-file "$COMPOSE_ENV_FILE")
fi
PROJECT_NAME="${PROJECT_NAME:-sunny-platform}"
[[ "$PROJECT_NAME" == sunny-* ]] || { echo "Refusing non-sunny project: $PROJECT_NAME" >&2; exit 64; }
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${1:-$ROOT/backups/$STAMP}"
mkdir -p "$DEST"
ARCHIVE="$DEST/sunny-data.sql.gz"
"$DOCKER_CMD" compose "${COMPOSE_ENV_ARGS[@]}" -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  pg_dump --data-only --column-inserts -U "${POSTGRES_USER:-sunny}" -d "${POSTGRES_DB:-sunny}" \
  | gzip -9 > "$ARCHIVE"
python3 "$ROOT/scripts/backup_manifest.py" create "$ARCHIVE" "$DEST/manifest.json" \
  --database "${POSTGRES_DB:-sunny}"
printf 'Backup created: %s\n' "$DEST/manifest.json"
