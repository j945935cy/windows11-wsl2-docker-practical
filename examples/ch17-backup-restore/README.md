# Chapter 17：備份、還原與搬移環境

本例以 `pg_dump` 產生 gzip archive，並建立含 schema version、database、UTC timestamp、archive 檔名與 SHA-256 的 `manifest.json`。還原前必須驗證 checksum。

## 從專案根目錄執行

```bash
docker compose -f examples/ch17-backup-restore/compose.yaml up -d
```

Docker Desktop 只提供 Windows CLI 時，可在後續 scripts 前加 `DOCKER_CMD=docker.exe`。

## 正常流程

```bash
examples/ch17-backup-restore/scripts/backup.sh
examples/ch17-backup-restore/scripts/restore.sh examples/ch17-backup-restore/backups/<timestamp>/manifest.json
```

先在來源與還原後環境分別查詢資料筆數；只有 archive 存在不代表可還原。

## 負向測試

複製一組 backup、修改 `.sql.gz` 任一 byte，再執行 restore。`backup_manifest.py verify` 必須以 `backup checksum mismatch` 拒絕，且不可把內容 pipe 進資料庫。

```bash
python3 examples/ch17-backup-restore/scripts/backup_manifest.py verify \
  examples/ch17-backup-restore/backups/<timestamp>/manifest.json
```

## 驗證

```bash
.venv/bin/pytest examples/ch17-backup-restore/test_ch17_contracts.py -q
bash -n examples/ch17-backup-restore/scripts/{backup,restore,reset}.sh
```

## Reset

危險操作必須提供本例專屬確認字串；只會刪除 Compose project `book-ch17` 的 volume，不刪 backup directory：

```bash
examples/ch17-backup-restore/scripts/reset.sh --yes-delete-book-ch17-data
```

如使用 Windows CLI：

```bash
DOCKER_CMD=docker.exe examples/ch17-backup-restore/scripts/reset.sh --yes-delete-book-ch17-data
```
