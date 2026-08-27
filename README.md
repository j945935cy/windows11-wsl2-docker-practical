# Windows 11、WSL 2 與 Docker 應用實戰

副標：從 Linux 開發環境、容器化服務到可重現的跨平台工作流程

作者：Happy eBook Authors

出版：Happy eBook

這是本書的製作 repository。公開讀者教材位於：

https://github.com/j945935cy/windows11-wsl2-docker-practical

本版不可變教材快照：

https://github.com/j945935cy/windows11-wsl2-docker-practical/releases/tag/reader-files-v1.0

## 讀者環境

主要 lab baseline：

- Windows 11
- WSL 2＋Ubuntu
- PowerShell＋WSL Bash
- Docker Desktop WSL 2 backend
- Docker Compose
- Python 3.12

## 建立驗證環境

從 repository root 執行：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
.venv/bin/python scripts/audit_book.py
.venv/bin/python scripts/audit_examples.py
```

若沒有 `uv`，可使用 Python 3.12 的標準 venv：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

## 驗證邊界

- Static contract tests 不需要 Docker daemon。
- Integration tests 需要 Docker Desktop 已啟動並對 Ubuntu 啟用 WSL Integration。
- 若只有 Windows `docker.exe` 可用，測試報告必須明確寫成 Windows CLI integration，不得聲稱 WSL integration 已完成。
- 所有服務只使用 localhost 與合成資料。

## 公開內容邊界

公開 companion repository 只包含讀者範例、環境檔、支援文件與 issue forms，不包含：

- `book/`、`frontmatter/`、`parts/`、`appendices/`
- EPUB、封面與商店素材
- 內部研究、審查筆記或完整 production scripts
- 秘密、私人路徑、`.env` 或真實公司資料
