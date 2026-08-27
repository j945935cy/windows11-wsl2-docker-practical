# Chapter 13：加入 PostgreSQL

以 Compose 建立 PostgreSQL 16、健康檢查、初始化 SQL 與 named volume。資料庫連接埠只發布到 `127.0.0.1:5433`。

## 從專案根目錄執行

```bash
cp examples/ch13-postgres-compose/.env.example examples/ch13-postgres-compose/.env
docker compose -f examples/ch13-postgres-compose/compose.yaml up -d
```

若裸 `docker` 顯示未啟用 WSL Integration，可先以 `docker.exe` 執行同一命令，並把此現象保留作環境邊界的負向案例。

## 正常流程

```bash
docker compose -f examples/ch13-postgres-compose/compose.yaml exec db \
  psql -U bookuser -d bookdb -c "INSERT INTO notes(body) VALUES ('hello'); SELECT * FROM notes;"
```

## 負向測試

錯誤密碼應拒絕登入：

```bash
PGPASSWORD=wrong psql -h 127.0.0.1 -p 5433 -U bookuser -d bookdb -c 'SELECT 1'
```

預期非零 exit code 與 authentication failed；不可把失敗改成成功。

## 驗證

```bash
.venv/bin/pytest examples/ch13-postgres-compose/test_ch13_contracts.py -q
docker compose -f examples/ch13-postgres-compose/compose.yaml ps
```

## Reset

`--volumes` 會永久刪除本例資料；先確認 project name 是 `book-ch13`：

```bash
docker compose -f examples/ch13-postgres-compose/compose.yaml down --volumes --remove-orphans
rm -f examples/ch13-postgres-compose/.env
```
