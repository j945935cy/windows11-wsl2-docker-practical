# Chapter 15：設定、秘密與安全邊界

本例透過 Compose secret 將 token 掛載成 `/run/secrets/api_token`；應用只確認秘密可讀，絕不回傳內容，也不把 token 放在 image 或環境變數。已提交的 `.example` 只說明格式，Compose 不會自動把它當 runtime secret。

## 從專案根目錄執行

建立被 Git 忽略的本機示範 token；命令不把值印到 terminal：

```bash
python3 -c 'from pathlib import Path; import secrets; p=Path("examples/ch15-secrets/secrets/api_token.txt"); p.write_text(secrets.token_urlsafe(24)+"\n", encoding="utf-8"); p.chmod(0o600)'
export API_TOKEN_FILE=./secrets/api_token.txt
docker compose -p book-ch15 -f examples/ch15-secrets/compose.yaml up --build -d
```

`API_TOKEN_FILE` 的相對路徑以 Compose 檔所在目錄解析。未設定變數時，Compose 會停止並要求你明確指定檔案；它不會 fallback 到公開 placeholder。

## 正常流程

```bash
curl --fail http://127.0.0.1:8015/health
```

預期 `secret` 欄位只顯示 `loaded-but-not-disclosed`。

## 負向測試

不用移動正常 secret；改指向固定不存在的檔案，以獨立 project 證明啟動失敗：

```bash
API_TOKEN_FILE=./secrets/does-not-exist.txt docker compose -p book-ch15-negative -f examples/ch15-secrets/compose.yaml up --build
printf 'exit=%s\n' "$?"
docker compose -p book-ch15-negative -f examples/ch15-secrets/compose.yaml down --remove-orphans
```

`up` 必須非零，不能 fallback 到硬編碼 token。若意外建立任何 negative project 資源，最後一行只清理該固定 project。

## 驗證

```bash
.venv/bin/python -m pytest examples/ch15-secrets/test_ch15_contracts.py -q
API_TOKEN_FILE=./secrets/api_token.txt docker compose -p book-ch15 -f examples/ch15-secrets/compose.yaml config
```

檢查輸出只包含秘密的檔案路徑，不包含秘密值。

## Reset

```bash
API_TOKEN_FILE=./secrets/api_token.txt docker compose -p book-ch15 -f examples/ch15-secrets/compose.yaml down --remove-orphans --rmi local
python3 -c 'from pathlib import Path; Path("examples/ch15-secrets/secrets/api_token.txt").unlink(missing_ok=True)'
unset API_TOKEN_FILE
```
