# Windows 11、WSL 2 與 Docker 應用實戰

副標：從 Linux 開發環境、容器化服務到可重現的跨平台工作流程

作者：Happy eBook Authors

出版：Happy eBook

這是本書的公開讀者教材 repository，包含可執行範例、測試、環境診斷、勘誤與技術問題入口；不包含完整書稿、EPUB、封面或商店素材。

本版不可變教材快照：

https://github.com/j945935cy/windows11-wsl2-docker-practical/releases/tag/reader-files-v1.0

## 取得教材

完成書中第 2 章的 WSL 2／Ubuntu 驗證後，在 WSL Bash 執行：

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/j945935cy/windows11-wsl2-docker-practical.git
cd windows11-wsl2-docker-practical
pwd
test -f README.md
python3 --version
```

主要 lab baseline：Windows 11、WSL 2＋Ubuntu、PowerShell、WSL Bash、Docker Desktop WSL integration、Docker Compose、Python 3.12。

## 建立驗證環境

從 repository root 執行：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
.venv/bin/python scripts/verify_reader_files.py
```

若沒有 `uv`：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/verify_reader_files.py
```

Windows host 診斷器在 PowerShell 執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/inspect-host.ps1
```

## 三條閱讀路線

### 環境與日常生產力

依序閱讀第 1～6、9～11、15～17 章；重點是 Windows／WSL／container 邊界、路徑、localhost、VS Code、設定與備份。

### 軟體開發

依序閱讀第 1～13、15～18 章；完成 Dockerfile、Compose、FastAPI、PostgreSQL 與晴日商店 final project。

### 自動化與 Bot

先讀第 1～10、15～17 章，再把 Chapter 18 的 health、secret、log、backup／restore 契約套用到排程、worker 或 Bot。這條路線不把本書擴張成 Kubernetes 或正式雲端部署教材。

## 驗證邊界

- Static／unit tests 不需要 Docker daemon。
- Integration tests 需要 Docker Desktop 已啟動並對 Ubuntu 開啟 WSL Integration。
- 若只有 Windows `docker.exe` 可用，Chapter 18 的 E2E 會使用 Windows temp file secret；這只證明 Windows CLI integration，不代表 WSL integration 已完成。
- 所有範例只使用 localhost、`sunny-*`／`book-*` scoped resources 與合成資料。
- 任何 reset 前先 preview；不要以全域 prune 取代 scoped cleanup。

## 支援與隱私

- 勘誤與技術問題：使用 repository 的 Issues 表單。
- 討論與延伸 Q&A：使用 Discussions。
- 提交診斷前先閱讀 [SUPPORT.md](SUPPORT.md)，移除 token、密碼、cookie、SSH key、私人路徑、公司 URL、IP、registry、客戶資料與未公開程式碼。

## 公開內容邊界

本 repository 只包含讀者範例、環境檔、支援文件與 issue forms。內容未另行授權者保留一切權利；詳見 [RIGHTS.md](RIGHTS.md)。
