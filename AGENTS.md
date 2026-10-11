# AGENTS.md — task-ledger

## 用途
Python 單機持久任務核心：磁碟收據、依檔案事實產生進度、延後承諾與中斷後續跑。公開 alpha；離線測試使用 FakeEngine。依據 README.md、pyproject.toml、src/task_ledger/。

## 目錄地圖
- `src/task_ledger/cli.py`：task-ledger 命令入口。
- `classify/`、`enqueue/`、`deferred/`、`progress/`、`tick/`：分類、入列、承諾、進度、worker／resume。
- `ports.py`、`adapters/`：引擎與通知介面。
- `tests/`：pytest／合約夾具；`scripts/`：離線自測、sanitize／release gates。
- `docs/`：架構與外部 CLI 接線說明；`adapters/powershell/`：可選範例。

## 安裝與第一次執行
Python 3.10+，在 repo 根目錄安裝 `pip install -e .`。使用者選一個專用輸出資料夾再設定 TASK_LEDGER_ROOT。POSIX shell 範例：
```bash
export TASK_LEDGER_ROOT=./demo-ledger
task-ledger order "Demo task"
task-ledger tick
task-ledger table
```
PowerShell 用 `$env:TASK_LEDGER_ROOT = './demo-ledger'`，再執行相同三條命令。`task-ledger demo-resume` 是離線模擬中斷，不要為此終止真實 agent。

## 驗證
測試需要 pytest；可用 `pip install -e '.[dev]'`。README 指令：
```bash
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
python scripts/ship_readiness_gate.py --root .
```
`python scripts/run_offline_selftest.py` 是另一個入口，但腳本會清理暫存與 `.pytest_basetemp`；執行前確認符合使用者的刪除邊界。

## 不要做的事
不要把 code_done 當 live_green，FakeEngine 通過不代表生產驗證。不要編完成百分比。外部 CLI 接線目前是 docs-only，不宣稱已附正式生產引擎。不必安裝 PowerShell adapter；不把執行期任務資料提交到 repo。

## 同作者相關工具
- [execution-proofs](https://github.com/zaxardery8011-design/execution-proofs)：檢查完成宣稱的檔案存在／新鮮度；本 repo 管任務生命週期，沒有內建該服務。
