# Chapter 18 Final Project：晴日平台

`Sunny Platform` 是可實跑的最終專案：非 root FastAPI image、PostgreSQL named volume、liveness/readiness、DB 啟動相依、只綁 `127.0.0.1:8018` 的 API、輸入驗證，以及帶 SHA-256 manifest 的備份/還原。資料庫不發布到主機。

## 從專案根目錄執行

```bash
python3 -c 'from pathlib import Path; import secrets; p=Path("examples/ch18-sunny-platform/secrets/db_password.txt"); p.write_text(secrets.token_urlsafe(32)+"\n", encoding="utf-8"); p.chmod(0o600)'
git check-ignore examples/ch18-sunny-platform/secrets/db_password.txt
docker compose -f examples/ch18-sunny-platform/compose.yaml up --build -d --wait
```

第一個命令只把隨機值寫入被 Git 忽略的本機檔，不印出內容。`.env.example` 只包含 user、database 與 secret file path，沒有 password。`git check-ignore` 應輸出該 secret 路徑；若沒有輸出，先停止，不要啟動或提交。

### WSL Integration 邊界

若裸 `docker info` 提示「enable WSL Integration」，這是刻意保留的負向環境案例：WSL distribution 尚未連到 Docker Desktop。主要學習路線是先在 Docker Desktop → Settings → Resources → WSL Integration 啟用目前 Ubuntu，再使用上述 Linux secret file。

若你只想驗證 Windows daemon 與完整專案，不要用 `docker.exe compose up` 直接 bind WSL secret；沒有 integration 時會缺少 distro mount service。改執行已驗證的雙路線 E2E：

```bash
docker.exe info
DOCKER_CMD=docker.exe examples/ch18-sunny-platform/scripts/e2e.sh
```

script 會在 Windows `%TEMP%` 產生不回顯的暫時 secret，透過暫存 `--env-file` 傳給 Windows Compose，最後精確清理。不要把裸 `docker` 的失敗報成成功；static／unit tests、Windows daemon E2E 與真正 WSL Integration 是三個不同證據。

## 正常流程

```bash
curl --fail http://127.0.0.1:8018/health/live
curl --fail http://127.0.0.1:8018/health/ready
curl --fail -X POST http://127.0.0.1:8018/notes \
  -H 'content-type: application/json' -d '{"body":"first sunny note"}'
curl --fail http://127.0.0.1:8018/notes
```

備份會輸出 `backups/<UTC>/sunny-data.sql.gz` 與同目錄 `manifest.json`：

```bash
examples/ch18-sunny-platform/scripts/backup.sh
# docker.exe 環境：DOCKER_CMD=docker.exe examples/ch18-sunny-platform/scripts/backup.sh
```

還原會先驗證 manifest／checksum，再把 `TRUNCATE` 與 archive 放入同一個 `psql --single-transaction --set ON_ERROR_STOP=1`。即使 checksum 正確但 SQL 無效也會 rollback，不留下已清空的 notes table。它仍會取代目前資料，因此需要明確確認：

```bash
examples/ch18-sunny-platform/scripts/restore.sh --yes-replace-sunny-data \
  examples/ch18-sunny-platform/backups/<UTC>/manifest.json
```

## 負向測試

空白 note 必須回 422；停止 db 後 readiness 必須回 503，liveness 仍表示 API process 狀態：

```bash
curl -i -X POST http://127.0.0.1:8018/notes -H 'content-type: application/json' -d '{"body":"   "}'
docker compose -f examples/ch18-sunny-platform/compose.yaml stop db
curl -i http://127.0.0.1:8018/health/ready
curl -i http://127.0.0.1:8018/health/live
docker compose -f examples/ch18-sunny-platform/compose.yaml start db
```

修改 backup archive 後執行 restore，checksum 驗證必須在資料庫清空前拒絕操作。

## 驗證

Static／unit tests：

```bash
.venv/bin/pytest examples/ch18-sunny-platform/test_ch18_contracts.py -q
docker compose -f examples/ch18-sunny-platform/compose.yaml config --quiet
docker compose -f examples/ch18-sunny-platform/compose.yaml ps
```

完整 E2E 會在 secret 檔不存在時產生本機隨機值，實際 build、啟動服務、測正常與負向案例、停止／恢復 DB、備份、還原，最後以 trap 移除該 `sunny-*` project 的 container、network 與 volume。它只刪除自己建立的 secret，不覆寫或刪除既有檔：

```bash
examples/ch18-sunny-platform/scripts/e2e.sh
# 若 Ubuntu 尚未啟用 WSL Integration，但 Windows daemon 可由 WSL 呼叫：
DOCKER_CMD=docker.exe examples/ch18-sunny-platform/scripts/e2e.sh
```

E2E 不移除 image cache；需要空間時，先用 `docker image ls 'sunny-*'` 預覽，再只移除你本次建立的精確 tag。

`docker inspect` 應顯示 API user 不是 root、兩服務健康，published address 為 `127.0.0.1`。

## Reset

reset script 同時要求專屬確認字串與 `sunny-*` project 前綴。它只執行本 project 的 `down --volumes --remove-orphans`，不會刪除 `backups/`：

```bash
examples/ch18-sunny-platform/scripts/reset.sh --yes-delete-sunny-platform-data
python3 -c 'from pathlib import Path; Path("examples/ch18-sunny-platform/secrets/db_password.txt").unlink(missing_ok=True)'
```

使用 Windows CLI 時：

```bash
DOCKER_CMD=docker.exe examples/ch18-sunny-platform/scripts/reset.sh --yes-delete-sunny-platform-data
```
