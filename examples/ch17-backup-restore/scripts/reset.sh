#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
CONFIRM="${1:-}"
if [[ "$CONFIRM" != "--yes-delete-book-ch17-data" ]]; then
  echo "Refusing destructive reset. Re-run with --yes-delete-book-ch17-data" >&2
  exit 64
fi
"$DOCKER_CMD" compose -f "$ROOT/compose.yaml" down --volumes --remove-orphans
