# Windows 11、WSL 2 與 Docker 應用實戰

副標：從 Linux 開發環境、容器化服務到可重現的跨平台工作流程

作者：Happy eBook Authors
出版：Happy eBook

這是《Windows 11、WSL 2 與 Docker 應用實戰》的公開讀者教材 repository。

## Repository 邊界

本 repository 只包含：

- 可執行教學範例
- Windows／WSL／Docker 環境檢查工具
- 範例設定檔與測試
- 勘誤與技術問題入口

本 repository **不包含**完整書稿、EPUB、封面或出版素材。權利說明請見 [`RIGHTS.md`](RIGHTS.md)。

## 開始使用

### Windows PowerShell

```powershell
git clone https://github.com/j945935cy/windows11-wsl2-docker-practical.git
cd windows11-wsl2-docker-practical
pwsh -File scripts/windows/inspect-host.ps1
```

若尚未安裝 PowerShell 7，可在 Windows PowerShell 5.1 執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/inspect-host.ps1
```

### WSL 2

```bash
git clone https://github.com/j945935cy/windows11-wsl2-docker-practical.git
cd windows11-wsl2-docker-practical
python3 examples/ch01-environment-layers/inspect_environment.py
python3 scripts/verify_reader_files.py
```

成功時 verifier 退出碼為 0；測試或安全檢查失敗時退出碼為 1。

## 第一個範例

[`examples/ch01-environment-layers`](examples/ch01-environment-layers/) 協助讀者回答第一個重要問題：

> 目前命令是在 Windows、一般 Linux、WSL，還是 Docker container 中執行？

範例輸出為 JSON，方便讀者保存環境診斷證據，也方便後續章節自動驗證。

## 閱讀路線

- 日常 Linux 使用：Windows Terminal、PowerShell、WSL、檔案與網路
- 軟體開發：Git、Python、VS Code、Dockerfile、Compose 與資料庫
- 自架服務／自動化：容器網路、volume、health check、日誌與備份

完整路線請見 [`docs/learning-paths.md`](docs/learning-paths.md)。

## 支援

- 發現書籍或範例錯誤：使用 **勘誤回報** issue form
- 遇到可重現的技術問題：使用 **技術問題** issue form
- 一般討論與延伸交流：使用 GitHub Discussions

提問時請先執行環境檢查工具，並移除使用者名稱、私人路徑、token、密碼、公司 URL 或其他敏感資訊。

## 安全原則

- 範例只使用本機服務及合成資料。
- 不要把真實秘密寫入 `.env`、issue、log 或 screenshot。
- 不執行來源不明的 `curl | sh`。
- 所有清理命令都必須限制在範例自行建立的目錄或 container／volume。
- 正式資料備份完成前，不執行 destructive reset。
