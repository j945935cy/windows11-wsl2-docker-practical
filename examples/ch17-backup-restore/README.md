# Chapter 17：備份、還原與搬移環境

本例以 `pg_dump -Fc` 產生 PostgreSQL custom-format archive，並建立含 schema version、database、UTC timestamp、archive 檔名與 SHA-256 的 `manifest.json`。SHA-256 只能偵測意外損壞，不能證明備份來源可信；只接受自己在受控位置建立的備份。

## 從專案根目錄執行

```bash
# WSL Bash（公開 companion repository root）
install -m 600 /dev/null ../book-ch17-db-password.txt
python3 - <<'PY'
from pathlib import Path
import secrets
Path('../book-ch17-db-password.txt').write_text(secrets.token_urlsafe(32) + '\n')
PY
export CH17_DB_SECRET_FILE="$(realpath ../book-ch17-db-password.txt)"
docker compose -f examples/ch17-backup-restore/compose.yaml up --build -d --wait
```

本 README 主線假設第 6 章的裸 WSL `docker` 已通過 Client／Server gate。不要只把 scripts 改成 `DOCKER_CMD=docker.exe`：Windows daemon 無法直接掛載 WSL-only secret path；若 integration 尚未完成，先回第 6 章修復。維護者若刻意測 Windows CLI 替代路線，必須另外建立 Windows-native mode-restricted secret 並一致傳入 Compose。

## 正常流程

備份目的地必須明確提供，而且必須位於 repository 外。腳本設定 `umask 077`，建立 mode 0700 目錄及 mode 0600 產物。

```bash
# WSL Bash（公開 companion repository root）
backup_dir="$(realpath -m ../book-ch17-backups)/$(date -u +%Y%m%dT%H%M%SZ)"
examples/ch17-backup-restore/scripts/backup.sh "$backup_dir"
examples/ch17-backup-restore/scripts/restore.sh "$backup_dir/manifest.json"
```

restore 不會覆寫來源 `bookdb`；它只重建固定的練習資料庫 `book_restore`，以 `pg_restore --exit-on-error --single-transaction` 還原，然後查詢 `notes` 筆數。來源資料庫與 staging 資料庫都應另外查詢代表資料；只有 archive 存在不代表可還原。

## 負向測試

複製一組 backup、修改 `.dump` 任一 byte，再執行 verify。`backup_manifest.py` 必須以 `backup checksum mismatch` 拒絕，且不可把內容交給 `pg_restore`。指定錯誤的來源資料庫名稱也必須被拒絕。

```bash
# WSL Bash
python3 examples/ch17-backup-restore/scripts/backup_manifest.py verify \
  "$backup_dir/manifest.json" --expected-database bookdb
```

不要把從網路下載或他人提供的 SQL／dump 直接交給 database owner 執行；manifest 與 archive 放在一起的 checksum 不具來源認證能力。真實環境需使用受控來源、權限、簽章或組織核准的備份系統，並先在隔離環境檢查。

## 驗證

```bash
# WSL Bash
.venv/bin/pytest examples/ch17-backup-restore/test_ch17_contracts.py -q
bash -n examples/ch17-backup-restore/scripts/{backup,restore,reset}.sh
```

## Reset

危險操作必須提供本例專屬確認字串；只會刪除 Compose project `book-ch17` 的 volume，不刪 repository 外的 backup directory：

```bash
# WSL Bash
examples/ch17-backup-restore/scripts/reset.sh --yes-delete-book-ch17-data
```

如使用 Windows CLI，secret path 也必須是 Windows-native path；只有 `DOCKER_CMD=docker.exe` 而仍傳入 WSL-only secret 會失敗。維護者完成該前置後，reset 才使用：

```bash
# WSL Bash
DOCKER_CMD=docker.exe examples/ch17-backup-restore/scripts/reset.sh --yes-delete-book-ch17-data
```
