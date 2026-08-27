# Chapter 6：Docker readiness

所有命令都從 repository root 執行。必要 gate 只用 Python 標準庫；Docker 可用時才跑選擇性 integration。

## 起始狀態

- 位於 repository root。
- 可執行 `python3`。
- static 驗證不要求 Docker daemon。

## 正常案例

```bash
python3 examples/ch06-docker-readiness/readiness.py
# 若裸 docker 顯示 cli-missing，再獨立確認 Windows CLI：
docker.exe version
docker.exe compose version
```

## 負向案例

即使 `docker.exe` 可用，裸 `docker` 在尚未啟用 Docker Desktop WSL Integration 時仍可能是 `cli-missing` 或 `daemon-unavailable`；兩條路徑不可混寫成同一狀態。本機實測為裸 `docker` 回報 `daemon-unavailable`，而 `docker.exe` client/server 皆可連線。

負向修改後請還原檔案，再執行 verifier。

## 驗證

```bash
python3 examples/ch06-docker-readiness/verify.py
python3 examples/ch06-docker-readiness/tests/test_verify.py -v
```

預期 static contract 與 3 個 tests 都顯示 `PASS`／`OK`。加上 `--integration` 時，如果 Docker CLI 或 daemon 不可用會明確顯示 `SKIP`，static gate 仍已執行。

## Reset

```bash
此診斷不建立 container、image 或 volume，不需 reset。
```
