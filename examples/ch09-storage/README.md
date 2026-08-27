# Chapter 9：bind mount 與 named volume

所有命令都從 repository root 執行。必要 gate 只用 Python 標準庫；Docker 可用時才跑選擇性 integration。

## 起始狀態

- 位於 repository root。
- 可執行 `python3`。
- static 驗證不要求 Docker daemon。

## 正常案例

```bash
python3 examples/ch09-storage/verify.py --integration --docker-cli docker.exe
# `.gitkeep` 讓 bind-data 在全新 checkout 已存在且由目前 WSL 使用者擁有。
test -d examples/ch09-storage/bind-data
# 只有啟用 Docker Desktop WSL Integration 後才跑 bind mount runtime：
HOST_UID="$(id -u)" HOST_GID="$(id -g)" \
  docker compose -f examples/ch09-storage/compose.yaml run --rm writer
test "$(stat -c %u examples/ch09-storage/bind-data/message.txt)" = "$(id -u)"
```

## 負向案例

把 bind mount 改成主機私人絕對路徑，static gate 應回報 FAIL。若只可用 `docker.exe` 且尚未啟用 WSL Integration，`compose config` 可以成功，但實際 bind mount 可能因 distro mount service 不可用而失敗；這是預期的環境負向案例，不代表 volume 契約已通過 runtime。

負向修改後請還原檔案，再執行 verifier。

## 驗證

```bash
python3 examples/ch09-storage/verify.py
python3 examples/ch09-storage/tests/test_verify.py -v
```

`volume-init` 只以 root 掛載本章 named volume，完成一次 scoped `chown` 後退出；它看不到 host bind path。`writer` 等 initializer 成功後仍以目前 WSL UID/GID 寫入兩種 storage，不需要 `chmod 777`。

預期 static contract 與 6 個 tests 都顯示 `PASS`／`OK`。加上 `--integration` 時預設檢查裸 `docker`；也可明確傳入 `--docker-cli docker.exe`。CLI 或 daemon 不可用會顯示 `SKIP`，static gate 仍已執行。

## Reset

```bash
docker compose -f examples/ch09-storage/compose.yaml down
docker volume rm wslbook_ch09_data 2>/dev/null || true
# 先確認 bind-data 內容，再只刪該目錄下自行產生的 message.txt：
python3 -c 'from pathlib import Path; Path("examples/ch09-storage/bind-data/message.txt").unlink(missing_ok=True)'
```
