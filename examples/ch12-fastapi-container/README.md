# Chapter 12：容器化 FastAPI

本例是本章唯一權威專案：`examples/ch12-fastapi-container`。image 從 repository root 的完整 `requirements-lock.txt` 安裝依賴，以 UID 10001 的 `appuser` 執行，並內建 `/health` healthcheck。container 內監聽 `0.0.0.0:8000`；host 只發布 `127.0.0.1:8012`。

## 從專案根目錄執行

```bash
# WSL Bash（公開 companion repository root）
test -f requirements-lock.txt
test -f examples/ch12-fastapi-container/app/main.py
docker build \
  --file examples/ch12-fastapi-container/Dockerfile \
  --tag book-ch12-fastapi:1.0 \
  .
docker run --detach --name book-ch12 \
  --publish 127.0.0.1:8012:8000 \
  book-ch12-fastapi:1.0
```

若裸 `docker` 尚未通過第 6 章 WSL Integration gate，請先完成整合；`docker.exe` 只可作 Windows daemon 替代診斷，不得誤稱裸 WSL integration 已完成。

## 正常流程

```bash
# WSL Bash（公開 companion repository root）
curl --fail http://127.0.0.1:8012/
curl --fail http://127.0.0.1:8012/health
docker inspect book-ch12 --format '{{.State.Status}} {{.State.Health.Status}}'
docker exec book-ch12 id
```

預期兩個 HTTP 請求回 200；health 最終為 `healthy`；`id` 顯示 UID 10001 的 `appuser`，不是 root。

## 負向測試

未知路由應回 HTTP 404。這是預期負向結果，因此不要加 `--fail`：

```bash
# WSL Bash（公開 companion repository root）
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8012/missing
```

預期輸出 `404`。

## 驗證

```bash
# WSL Bash（公開 companion repository root）
.venv/bin/pytest examples/ch12-fastapi-container/test_ch12_contracts.py -q
docker image inspect book-ch12-fastapi:1.0 \
  --format '{{.Config.User}} {{json .Config.Healthcheck.Test}}'
docker inspect book-ch12 --format '{{.State.Health.Status}}'
```

預期 image user 為 `appuser`，healthcheck 包含 `/health`，container 最終為 `healthy`。靜態 pytest 不等於 image integration；只有真實 build、run、HTTP、health 與 user 都通過，才算本章整合驗證。

## Reset

先預覽精確名稱，再只移除本例 container 與 image：

```bash
# WSL Bash（公開 companion repository root）
docker ps -a --filter name='^/book-ch12$'
docker rm -f book-ch12
docker image inspect book-ch12-fastapi:1.0 >/dev/null
docker image rm book-ch12-fastapi:1.0
```

若 preview 沒有 `book-ch12`，停止，不要把名稱換成模糊 filter 或執行全域 prune。
