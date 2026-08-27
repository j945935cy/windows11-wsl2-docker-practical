#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
PROJECT_NAME="${PROJECT_NAME:-book-ch17}"
case "$PROJECT_NAME" in book-ch17|book-ch17-*) ;; *) printf 'Refusing project: %s\n' "$PROJECT_NAME" >&2; exit 2;; esac
MANIFEST="${1:?usage: restore.sh PATH/manifest.json}"
SOURCE_DATABASE="${POSTGRES_DB:-bookdb}"
TARGET_DATABASE="book_restore"
if [[ "$SOURCE_DATABASE" == "$TARGET_DATABASE" ]]; then
  printf 'source database must differ from restore target: %s\n' "$TARGET_DATABASE" >&2
  exit 2
fi
ARCHIVE="$(python3 "$ROOT/scripts/backup_manifest.py" verify "$MANIFEST" \
  --expected-database "$SOURCE_DATABASE")"

# Never overwrite the source database. Recreate only the fixed exercise target.
"$DOCKER_CMD" compose -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  dropdb --if-exists -U "${POSTGRES_USER:-bookuser}" "$TARGET_DATABASE"
"$DOCKER_CMD" compose -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  createdb -U "${POSTGRES_USER:-bookuser}" "$TARGET_DATABASE"
"$DOCKER_CMD" compose -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  pg_restore -U "${POSTGRES_USER:-bookuser}" -d "$TARGET_DATABASE" \
    --exit-on-error --single-transaction < "$ARCHIVE"
"$DOCKER_CMD" compose -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" exec -T db \
  psql -U "${POSTGRES_USER:-bookuser}" -d "$TARGET_DATABASE" \
    --set ON_ERROR_STOP=1 -Atc 'SELECT count(*) FROM notes;'
printf 'Restore drill completed in staging database %s from: %s\n' \
  "$TARGET_DATABASE" "$ARCHIVE"
