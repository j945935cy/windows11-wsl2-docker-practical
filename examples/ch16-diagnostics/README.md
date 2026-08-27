# Chapter 16：日誌、Health Check 與系統化除錯

本例區分 liveness（process 活著）與 readiness（相依服務可用），並輸出 method、path、status、duration 結構化欄位及限制 Docker log rotation。診斷時先用 `docker compose logs`（本例命令另帶 `-f`）查看應用日誌。

## 從專案根目錄執行

```bash
docker compose -f examples/ch16-diagnostics/compose.yaml up --build -d
```

## 正常流程

```bash
curl --fail http://127.0.0.1:8016/health/live
curl --fail http://127.0.0.1:8016/health/ready
docker compose -f examples/ch16-diagnostics/compose.yaml logs --tail=20 app
```

## 負向測試

把 dependency 設為不可用，liveness 應維持 200、readiness 必須為 503：

```bash
DEPENDENCY_READY=false docker compose -f examples/ch16-diagnostics/compose.yaml run --rm -e DEPENDENCY_READY=false app \
  python -c 'from app.main import dependency_ready; raise SystemExit(0 if not dependency_ready() else 1)'
```

也可暫時把 compose 的值改成 `false` 後重建，使用 `curl -i /health/ready` 觀察 503，再還原。

## 驗證

```bash
.venv/bin/pytest examples/ch16-diagnostics/test_ch16_contracts.py -q
docker inspect --format '{{json .State.Health}}' book-ch16-app-1
```

## Reset

```bash
docker compose -f examples/ch16-diagnostics/compose.yaml down --volumes --remove-orphans --rmi local
```
