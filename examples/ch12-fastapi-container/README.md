# Chapter 12：容器化 FastAPI

最小 FastAPI 映像，使用非 root 帳號執行；容器內必須監聽 `0.0.0.0`，主機發布則只綁定 loopback。

## 從專案根目錄執行

```bash
docker build -t book-ch12-fastapi examples/ch12-fastapi-container
docker run --rm -d --name book-ch12 -p 127.0.0.1:8012:8000 book-ch12-fastapi
```

在 Windows Docker Desktop 尚未開啟此 distribution 的 WSL Integration 時，可把命令的 `docker` 改為 `docker.exe`。

## 正常流程

```bash
curl --fail http://127.0.0.1:8012/
curl --fail http://127.0.0.1:8012/health
```

## 負向測試

未知路由應明確回傳 HTTP 404，而不是假裝成功：

```bash
curl -i http://127.0.0.1:8012/missing
```

## 驗證

```bash
.venv/bin/pytest examples/ch12-fastapi-container/test_ch12_contracts.py -q
docker inspect --format '{{.Config.User}}' book-ch12
```

預期 container user 為 `app`。

## Reset

只停止本例的具名 container 並移除本例 image：

```bash
docker rm -f book-ch12 2>/dev/null || true
docker image rm book-ch12-fastapi 2>/dev/null || true
```
