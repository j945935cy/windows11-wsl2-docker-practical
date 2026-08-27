# Chapter 7：第一個 container 契約

所有命令都從 repository root 執行。必要 gate 只用 Python 標準庫；Docker 可用時才跑選擇性 integration。

## 起始狀態

- 位於 repository root。
- 可執行 `python3`。
- static 驗證不要求 Docker daemon。

## 正常案例

```bash
python3 examples/ch07-container-contract/verify.py --integration --docker-cli docker.exe
```

## 負向案例

把 `expected_stdout` 改成不同文字後跑 static verifier；契約片段 gate 應失敗。

負向修改後請還原檔案，再執行 verifier。

## 驗證

```bash
python3 examples/ch07-container-contract/verify.py
python3 examples/ch07-container-contract/tests/test_verify.py -v
```

預期 static contract 與 3 個 tests 都顯示 `PASS`／`OK`。加上 `--integration` 時預設檢查裸 `docker`；也可明確傳入 `--docker-cli docker.exe`。CLI 或 daemon 不可用會顯示 `SKIP`，static gate 仍已執行。

## Reset

```bash
docker rm -f wslbook-ch07-demo 2>/dev/null || true  # 只清理由本 lab 命名的 container
```
