# Chapter 4：安全處理路徑

所有命令都從 repository root 執行。必要 gate 只用 Python 標準庫；Docker 可用時才跑選擇性 integration。

## 起始狀態

- 位於 repository root。
- 可執行 `python3`。
- static 驗證不要求 Docker daemon。

## 正常案例

```bash
python3 examples/ch04-paths/path_demo.py examples/ch04-paths/sample/data.txt
```

## 負向案例

python3 examples/ch04-paths/path_demo.py ../outside.txt  # 預期 ValueError

負向修改後請還原檔案，再執行 verifier。

## 驗證

```bash
python3 examples/ch04-paths/verify.py
python3 examples/ch04-paths/tests/test_verify.py -v
```

預期 static contract 與 3 個 tests 都顯示 `PASS`／`OK`。加上 `--integration` 時，如果 Docker CLI 或 daemon 不可用會明確顯示 `SKIP`，static gate 仍已執行。

## Reset

```bash
範例只顯示路徑，不寫檔；不需 reset。
```
