#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
COMPOSE_ENV_ARGS=()
if [[ -n "${COMPOSE_ENV_FILE:-}" ]]; then
  COMPOSE_ENV_ARGS=(--env-file "$COMPOSE_ENV_FILE")
fi
PROJECT_NAME="${PROJECT_NAME:-sunny-platform}"
if [[ "$PROJECT_NAME" != sunny-* ]]; then
  echo "Refusing reset outside sunny-* projects: $PROJECT_NAME" >&2
  exit 64
fi
if [[ "${1:-}" != "--yes-delete-sunny-platform-data" ]]; then
  echo "Refusing destructive reset. Re-run with --yes-delete-sunny-platform-data" >&2
  exit 64
fi
"$DOCKER_CMD" compose "${COMPOSE_ENV_ARGS[@]}" -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" down --volumes --remove-orphans
