# IG 自動發布（@daily.electricity / @daily.electronics.tw）

- `schedule.json`：要發的內容（時間＝台灣時間）。type：carousel／image／story／reel。
- `media/`：圖片（必須是 JPG）和影片（MP4）。這個 repo 必須是 **Public**，IG 才抓得到。
- `publish.py`：GitHub Actions 每 15 分鐘跑一次，把「時間到了、還沒發」的項目發出去，結果記在 `published.json`。超過預定時間 6 小時還沒發的會略過，不補發。
- `refresh_tokens.py`：每月 1、15 日自動延長 IG 權杖（權杖 60 天到期）。

## Secrets（Settings → Secrets and variables → Actions）
| 名稱 | 內容 |
|---|---|
| IG_TOKEN_ELECTRICITY | @daily.electricity 的長效權杖 |
| IG_TOKEN_ELECTRONICS | @daily.electronics.tw 的長效權杖 |
| GH_PAT | GitHub fine-grained token（此 repo 的 Secrets: Read and write），給自動延長權杖用 |

## 測試
Actions → publish → Run workflow → dry_run = 1：只列出會發什麼，不會真的發。
