# Chapter 5：localhost 與 port

所有命令都從 repository root 執行。必要 gate 只用 Python 標準庫；Docker 可用時才跑選擇性 integration。

## 起始狀態

- 位於 repository root。
- 可執行 `python3`。
- static 驗證不要求 Docker daemon。

## 正常案例

```bash
python3 examples/ch05-networking/server.py  # 另一個 shell: curl http://127.0.0.1:8000/
```

## 負向案例

在第二個 shell 再啟動一次，應看到 port 已被占用；或 curl 錯誤 port 8001。

負向修改後請還原檔案，再執行 verifier。

## 驗證

```bash
python3 examples/ch05-networking/verify.py
python3 examples/ch05-networking/tests/test_verify.py -v
```

預期 static contract 與 3 個 tests 都顯示 `PASS`／`OK`。加上 `--integration` 時，如果 Docker CLI 或 daemon 不可用會明確顯示 `SKIP`，static gate 仍已執行。

## Reset

```bash
在 server shell 按 Ctrl+C；沒有背景服務或固定資源要刪除。
```
