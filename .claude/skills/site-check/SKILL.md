---
name: site-check
description: 稽核並自動修復 SEOULMATE 31 靜態站的跨頁一致性——付款連結、LINE 官方帳號、Calendly、字型載入、HTML 基本標籤。在新增或修改任何 .html 後、commit 之前使用；使用者提到「檢查全站」「一致性」「連結對不對」「上線前確認」「自我修復」時也適用。
---

# 全站一致性稽核與自我修復

這個站是 20 個各自獨立的 HTML 檔，沒有共用模板、沒有 build step。同一段
CTA、付款連結、字型引用在每頁都是複製貼上的——所以改動極容易只改到一半，
留下半新半舊的頁面。這個 skill 就是用來擋這件事。

## 怎麼跑

```bash
bash .claude/skills/site-check/check.sh          # 只檢查
bash .claude/skills/site-check/check.sh --fix    # 先自動修，再檢查剩下的
```

全過 exit 0；有問題會分類列出並 exit 1。

**commit 前會自動跑。** `.githooks/pre-commit` 會先 `--fix`，把修好的內容
一併加進該次 commit；修不掉的則中止 commit。新 clone 要啟用一次：

```bash
git config core.hooksPath .githooks
```

## 正解放在 rules.conf

只有站主知道的值（LINE 官方帳號、Calendly 帳號、預設語言、PayPal 帳號名）
集中在 `rules.conf`，**每個值都附上判定依據**。改規則改那裡，不要改程式。

留空 = 尚未確認。這時腳本仍會偵測「全站出現幾種寫法」並回報，但不會自己
挑一個去改——它不知道哪個才對。填好之後跑 `--fix` 就會一次改齊。

## 檢查哪些項目

| # | 項目 | 標準 | 自動修 |
|---|---|---|---|
| 1 | PayPal 網址寫法 | 短網址 `paypal.me/<帳號>/<金額>` | ✅ |
| 2 | 金額對應商品 | `$19` = PDF 攻略（只在 `arrival-*`）；`$79` = 1:1 諮詢 | ❌ |
| 3 | LINE 聯絡方式 | `rules.conf` 的 `LINE_URL` | ✅ |
| 4 | Calendly | `rules.conf` 的 `CALENDLY_URL`，保留各頁原有查詢參數 | ✅ |
| 5 | 字型載入 | CSS 用到的 Google 字型必須有載入，且有 `display=swap` | ❌ |
| 6 | HTML 基本標籤 | `lang`、`viewport`、`title`、`description` | 前兩項 ✅ |
| 7 | 外部連結 | `target="_blank"` + `rel="noopener"` | ✅ |

## 哪些永遠不自動修，為什麼

- **第 2 項（金額）。** `$19` 和 `$79` 是兩個不同商品，不是筆誤。報錯代表
  某頁掛錯商品，是商業決策——回報給使用者，不要自己選一個。
- **第 5 項（字型）。** 各頁字型組合本來就該不同：`index.html`、`success.html`
  用系統字體是 2026-06 改版的刻意設計；`b2b`/`shop`/`student`/`plastic` 沒有
  韓文內容，不該載 Noto Sans KR。所以**不比對各頁字型是否一致**——那會製造
  一堆假警報。只檢查「CSS 宣告了但沒載入」這種真的會壞掉的情況。
- **第 6 項的 `description`。** 要針對每頁內容各寫一句，套罐頭文案等於沒寫。

## LINE 群組連結是例外

`success.html` 用的 `line.me/ti/g/…` 是**群組**連結，不是官方帳號私訊。
這是刻意的：commit 48415f0 寫明「open chat is post-purchase only」，
success.html 正是付款完成頁。

`sitecheck.py` 已寫死不會動 `line.me/ti/g/` 開頭的連結，也不會把它算進
「全站有幾種寫法」的比對。**無腦全站取代會弄壞這條。**

## 新增頁面時

複製一個 `arrival-*` 頁當骨架（它們最貼近標準），改完內容後跑
`check.sh --fix`，剩下的手動處理完再 commit。
