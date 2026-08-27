# Chapter 1：辨識目前的執行環境

這個範例回答：目前命令是在 Windows、WSL、Docker container，還是一般 Linux 中執行？

## 從 repository root 執行

```bash
python3 examples/ch01-environment-layers/inspect_environment.py
```

Windows PowerShell 也可以使用已安裝的 Python：

```powershell
python examples/ch01-environment-layers/inspect_environment.py
```

## 預期輸出

輸出為 JSON；`layer` 應為下列之一：

```text
windows
wsl
container
linux
other
```

在 WSL 2 中可能看到：

```json
{
  "cwd_under_windows_mount": false,
  "layer": "wsl",
  "wsl_distribution": "Ubuntu"
}
```

實際輸出還會包含 Python、kernel、machine、目前目錄與 home。不要把包含私人使用者名稱或公司路徑的完整輸出直接貼到公開 issue。

## 錯誤案例

若你原本以為命令在 WSL 執行，`layer` 卻是 `container`，通常表示終端機目前附加到 container shell。先執行：

```bash
pwd
python3 examples/ch01-environment-layers/inspect_environment.py
```

不要因為提示字元長得相似，就假設所在環境相同。

## 驗證

```bash
python3 -m unittest discover -s examples/ch01-environment-layers/tests -v
```

測試使用合成訊號，不要求 Windows、WSL 與 Docker 同時存在。

## 回復乾淨狀態

此範例只讀取環境並輸出到 stdout，不會建立 container、volume 或輸出檔，因此不需要清理。
