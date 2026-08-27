#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="${DOCKER_CMD:-docker}"
PROJECT_NAME="${PROJECT_NAME:-sunny-platform-e2e}"
[[ "$PROJECT_NAME" == sunny-* ]] || { echo "Refusing non-sunny project: $PROJECT_NAME" >&2; exit 64; }
BACKUP_DIR="$(mktemp -d /tmp/sunny-platform-e2e.XXXXXX)"
SECRET_FILE="$ROOT/secrets/db_password.txt"
CREATED_SECRET=0
WINDOWS_SECRET=""
ENV_FILE=""
COMPOSE_ENV_FILE=""
COMPOSE_ENV_ARGS=()

compose() {
  "$DOCKER_CMD" compose "${COMPOSE_ENV_ARGS[@]}" -p "$PROJECT_NAME" -f "$ROOT/compose.yaml" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
  BACKUP_DIR="$BACKUP_DIR" python3 -c 'import os, shutil; shutil.rmtree(os.environ["BACKUP_DIR"], ignore_errors=True)'
  if [[ "$CREATED_SECRET" == 1 ]]; then
    SECRET_FILE="$SECRET_FILE" python3 -c 'import os; from pathlib import Path; Path(os.environ["SECRET_FILE"]).unlink(missing_ok=True)'
  fi
  if [[ -n "$WINDOWS_SECRET" ]]; then
    WSLENV=WINDOWS_SECRET/w WINDOWS_SECRET="$WINDOWS_SECRET" powershell.exe -NoProfile -Command 'Remove-Item -LiteralPath $env:WINDOWS_SECRET -Force -ErrorAction SilentlyContinue' >/dev/null || true
  fi
  if [[ -n "$ENV_FILE" ]]; then
    ENV_FILE="$ENV_FILE" python3 -c 'import os; from pathlib import Path; Path(os.environ["ENV_FILE"]).unlink(missing_ok=True)'
  fi
}
trap cleanup EXIT

if [[ "$DOCKER_CMD" == *.exe ]]; then
  WINDOWS_SECRET="$(powershell.exe -NoProfile -Command '$p=Join-Path $env:TEMP ("sunny-db-"+[guid]::NewGuid().ToString("N")+".txt"); $b=New-Object byte[] 32; $r=[Security.Cryptography.RandomNumberGenerator]::Create(); $r.GetBytes($b); $r.Dispose(); [IO.File]::WriteAllText($p,[Convert]::ToBase64String($b)); $p.Replace("\","/")' | tr -d '\r')"
  ENV_FILE="$(mktemp "$ROOT/.env.e2e.XXXXXX")"
  printf 'SUNNY_DB_PASSWORD_FILE=%s\n' "$WINDOWS_SECRET" > "$ENV_FILE"
  COMPOSE_ENV_FILE="$(wslpath -w "$ENV_FILE" | tr -d '\r')"
  COMPOSE_ENV_ARGS=(--env-file "$COMPOSE_ENV_FILE")
else
  if [[ ! -f "$SECRET_FILE" ]]; then
    SECRET_FILE="$SECRET_FILE" python3 -c 'import os, secrets; from pathlib import Path; p=Path(os.environ["SECRET_FILE"]); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(secrets.token_urlsafe(32)+"\n", encoding="utf-8"); p.chmod(0o600)'
    CREATED_SECRET=1
  fi
fi

compose up --build -d --wait
curl --fail --silent http://127.0.0.1:8018/health/live >/dev/null
curl --fail --silent http://127.0.0.1:8018/health/ready >/dev/null
curl --fail --silent -X POST http://127.0.0.1:8018/notes \
  -H 'content-type: application/json' -d '{"body":"backup keeper"}' >/dev/null

negative_status="$(curl --silent -o /dev/null -w '%{http_code}' -X POST \
  http://127.0.0.1:8018/notes -H 'content-type: application/json' -d '{"body":"   "}')"
[[ "$negative_status" == 422 ]]
printf 'negative_status=%s\n' "$negative_status"

compose stop db >/dev/null
not_ready_status="$(curl --silent -o /dev/null -w '%{http_code}' http://127.0.0.1:8018/health/ready)"
[[ "$not_ready_status" == 503 ]]
compose start db >/dev/null
for _ in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8018/health/ready >/dev/null; then break; fi
  sleep 2
done
curl --fail --silent http://127.0.0.1:8018/health/ready >/dev/null

DOCKER_CMD="$DOCKER_CMD" COMPOSE_ENV_FILE="$COMPOSE_ENV_FILE" PROJECT_NAME="$PROJECT_NAME" "$ROOT/scripts/backup.sh" "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/bad"
printf 'THIS IS NOT VALID SQL;\n' | gzip -9 > "$BACKUP_DIR/bad/invalid.sql.gz"
python3 "$ROOT/scripts/backup_manifest.py" create "$BACKUP_DIR/bad/invalid.sql.gz" "$BACKUP_DIR/bad/manifest.json" --database sunny
set +e
DOCKER_CMD="$DOCKER_CMD" COMPOSE_ENV_FILE="$COMPOSE_ENV_FILE" PROJECT_NAME="$PROJECT_NAME" "$ROOT/scripts/restore.sh" \
  --yes-replace-sunny-data "$BACKUP_DIR/bad/manifest.json" >/dev/null 2>&1
bad_restore_status=$?
set -e
[[ "$bad_restore_status" -ne 0 ]]
after_bad_restore="$(curl --fail --silent http://127.0.0.1:8018/notes)"
printf '%s' "$after_bad_restore" | grep -q 'backup keeper'
printf 'bad_restore_status=%s after_bad_restore=%s\n' "$bad_restore_status" "$after_bad_restore"

curl --fail --silent -X POST http://127.0.0.1:8018/notes \
  -H 'content-type: application/json' -d '{"body":"remove after restore"}' >/dev/null
DOCKER_CMD="$DOCKER_CMD" COMPOSE_ENV_FILE="$COMPOSE_ENV_FILE" PROJECT_NAME="$PROJECT_NAME" "$ROOT/scripts/restore.sh" \
  --yes-replace-sunny-data "$BACKUP_DIR/manifest.json" >/dev/null
after_restore="$(curl --fail --silent http://127.0.0.1:8018/notes)"
printf '%s' "$after_restore" | grep -q 'backup keeper'
if printf '%s' "$after_restore" | grep -q 'remove after restore'; then
  echo "Restore did not replace post-backup data" >&2
  exit 1
fi
printf 'after_restore=%s\n' "$after_restore"

uid="$(compose exec -T api id -u | tr -d '\r')"
[[ "$uid" != 0 ]]
port="$(compose port api 8000 | tr -d '\r')"
[[ "$port" == "127.0.0.1:8018" ]]
printf 'E2E passed: uid=%s port=%s\n' "$uid" "$port"
