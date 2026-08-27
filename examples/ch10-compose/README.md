# Chapter 10：用 Docker Compose 組合服務

本例用 Compose 啟動有 healthcheck 的靜態 `web`，再讓短命 `checker` 等到 `web` healthy 後透過 service DNS 請求 `http://web:8000/`。主機只在 `127.0.0.1:8000` 發布網站。

## 從專案根目錄執行

```bash
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml config --quiet
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml up -d --build --wait
```

## 正常流程

```bash
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml ps
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml run --rm checker
curl --fail http://127.0.0.1:8000/
```

預期 `web` healthy、`checker` stdout 為 `200` 且命令退出碼為 0；curl 回傳包含 `Compose is ready` 的 HTML。checker 放在 `verify` profile，不會讓正常 `up --wait` 因短命 service 正常離開而誤報失敗。

## 負向測試

把 `web` healthcheck URL 暫時改成 `/missing`，執行 `up -d --build --wait` 應非零或顯示 unhealthy，`checker` 不應成功。完成後立刻還原 `/` 並重跑正常流程；不要以固定 `sleep` 取代 healthcheck。

## 驗證

```bash
.venv/bin/python -m pytest examples/ch10-compose/test_ch10_contracts.py -q
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml config --quiet
```

若 Docker CLI 或 daemon 不可用，pytest 的 live config case 會明確顯示 `SKIPPED`；靜態 contract 仍必須通過。

## Reset

只移除本例的 containers、network 與本機 build image；本例沒有資料 volume：

```bash
docker compose -p book-ch10 -f examples/ch10-compose/compose.yaml down --remove-orphans --rmi local
```
