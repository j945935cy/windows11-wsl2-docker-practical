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
[[ "${1:-}" == "--yes-replace-sunny-data" && -n "${2:-}" ]] || {
  echo "usage: restore.sh --yes-replace-sunny-data PATH/manifest.json" >&2; exit 64;
}
ARCHIVE="$(python3 "$ROOT/scripts/backup_manifest.py" verify "$2")"
{
  printf 'TRUNCATE notes RESTART IDENTITY;\n'
  gzip -cd -- "$ARCHIVE"
} | "$DOCKER_CMD" compose "${COMPOSE_ENV_ARGS[@]}" -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  psql --single-transaction --set ON_ERROR_STOP=1 -U "${POSTGRES_USER:-sunny}" -d "${POSTGRES_DB:-sunny}"
printf 'Restore completed: %s\n' "$ARCHIVE"
