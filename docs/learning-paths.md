# 閱讀路線

## 日常 Linux 使用者

適合希望在 Windows 11 使用 Linux 命令、檔案工具與本機服務的讀者。

```text
環境分層 → WSL 2 → Shell → 路徑與權限 → localhost 與連接埠 → 診斷 → 備份
```

完成後應能：

- 分辨 Windows、WSL 與 container shell。
- 正確選擇 Windows 或 Linux 專案路徑。
- 解釋 `/mnt/c`、`/home` 與 `\\wsl$` 的用途。
- 保存不含秘密的環境診斷資料。

## 軟體開發者

```text
環境分層 → WSL 2 → Git／Python → Docker → Dockerfile → Compose
→ FastAPI → PostgreSQL → 測試 → 日誌 → 備份與還原
```

完成後應能：

- 從 repository root 重建鎖定的開發環境。
- 建立 non-root application image。
- 以 Compose 啟動應用程式與資料庫。
- 用 health check、測試和 log 區分應用程式、網路及環境問題。

## 自架服務與自動化使用者

```text
環境分層 → WSL 2 → Docker → Network → Volume → Compose
→ 設定與秘密 → Health check → Restart → Backup／restore
```

完成後應能：

- 說明 published port 與 container network 的差異。
- 避免把資料只保存在 container writable layer。
- 建立可驗證的 volume 與資料庫備份。
- 在更新或故障後執行還原演練。

## 共通規則

不論採哪一條路線，每個範例都應包含：

1. 起始目錄與先決條件。
2. 執行命令。
3. 預期輸出。
4. 代表性錯誤案例。
5. 驗證方式。
6. 回復乾淨狀態的方法。
