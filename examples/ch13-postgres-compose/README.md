# Chapter 13：加入 PostgreSQL

本例以單一 Compose stack 執行 FastAPI `api` 與 PostgreSQL `db`。API 透過 service DNS `db:5432` 連線；db 不發布任何 host port。只有 API 以 `127.0.0.1:8013` 提供讀者測試。兩個 service 只掛載同一個 repository 外 runtime file secret。

## 從專案根目錄執行

```bash
# WSL Bash（公開 companion repository root）
install -m 600 /dev/null ../book-ch13-db-password.txt
python3 - <<'PY'
from pathlib import Path
import secrets
Path('../book-ch13-db-password.txt').write_text(secrets.token_urlsafe(32) + '\n')
PY
export CH13_DB_SECRET_FILE="$(realpath ../book-ch13-db-password.txt)"
docker compose -f examples/ch13-postgres-compose/compose.yaml up --build -d --wait
```

若裸 `docker` 尚未啟用 WSL Integration，可用 `docker.exe` 診斷 Windows daemon，但這不等於裸 WSL integration 已完成。使用替代 CLI 時，後續命令也要一致使用 `docker.exe compose`。

## 正常流程

```bash
# WSL Bash
curl --fail http://127.0.0.1:8013/health/live
curl --fail http://127.0.0.1:8013/health/ready
curl --fail -H 'Content-Type: application/json' \
  -d '{"body":"hello postgres"}' http://127.0.0.1:8013/notes
curl --fail http://127.0.0.1:8013/notes
```

預期 live 與 ready 都是 HTTP 200，POST 是 201，GET 能讀回剛建立的 note。`docker compose exec db ...` 可作 scoped 診斷，但主線不需要也不允許從 host 直接連 `5432`。

## Migration

首次 `init.sql` 只處理空 volume；既有資料的 schema 變更必須明確執行。短命 `migrate` service 位於 profile，不會干擾一般 `up --wait`。以下以 committed `0003_add_priority.sql` 為 migration image 重建後執行，`-e` 必須放在 service 名稱 `migrate` 前：

```bash
# WSL Bash（公開 companion repository root）
docker compose -f examples/ch13-postgres-compose/compose.yaml --profile migrate run --build --rm -e MIGRATION_FILE=0003_add_priority.sql migrate
docker compose -f examples/ch13-postgres-compose/compose.yaml exec -T db \
  psql -U bookuser -d bookdb -Atc \
  "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='notes' AND column_name='priority';"
```

預期 migration 退出碼 0，查詢輸出 `priority|smallint|NO|0`。重跑 migration 也必須成功；不要改寫已套用的版本檔。`MIGRATION_FILE` 只接受四位數 revision 加小寫字母、數字或底線的安全 basename，且目標必須是 image 中 `/migrations` 下的 regular file；不得傳入路徑或自行拼接 shell 程式。

## 負向測試

停止 db 後，API process 仍活著，因此 live 保持 200；ready 必須變成 503。恢復 db 後 ready 應回到 200。

```bash
# WSL Bash
docker compose -f examples/ch13-postgres-compose/compose.yaml stop db
curl --fail http://127.0.0.1:8013/health/live
curl -i http://127.0.0.1:8013/health/ready
docker compose -f examples/ch13-postgres-compose/compose.yaml start db
```

缺少 `CH13_DB_SECRET_FILE` 時，`docker compose config` 必須 fail closed；不要以公開 `.example` 密碼讓服務繼續啟動。

## 驗證

```bash
# WSL Bash
.venv/bin/pytest examples/ch13-postgres-compose/test_ch13_contracts.py -q
docker compose -f examples/ch13-postgres-compose/compose.yaml ps
```

## Reset

`--volumes` 會永久刪除本例資料。先確認 project name 是 `book-ch13`，再只清除此 stack：

```bash
# WSL Bash
docker compose -f examples/ch13-postgres-compose/compose.yaml down --volumes --remove-orphans
rm -f ../book-ch13-db-password.txt
unset CH13_DB_SECRET_FILE
```
