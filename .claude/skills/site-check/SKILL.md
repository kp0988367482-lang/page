---
name: site-check
description: 稽核並修正 SEOULMATE 31 靜態站的跨頁一致性——付款連結、LINE 官方帳號、Calendly、字型組合、HTML 基本標籤。在新增或修改任何 .html 後、commit 之前使用；使用者提到「檢查全站」「一致性」「連結對不對」「上線前確認」時也適用。
---

# 全站一致性稽核

這個站是 20 個各自獨立的 HTML 檔，沒有共用模板、沒有 build step。同一段
CTA、付款連結、字型引用在每頁都是複製貼上的——所以改動極容易只改到一半，
留下半新半舊的頁面。這個 skill 就是用來擋這件事。

## 怎麼跑

```bash
bash .claude/skills/site-check/check.sh
```

全過 exit 0；有問題會依類別列出「檔名:行號:內容」並 exit 1。

## 檢查哪些項目

| # | 項目 | 標準 |
|---|---|---|
| 1 | PayPal 網址寫法 | 一律短網址 `https://paypal.me/HSIANGENTSAI/<金額>` |
| 2 | 金額對應商品 | `$19` = PDF 攻略（只在 `arrival-*`）；`$79` = 1:1 諮詢（不在 `arrival-*`） |
| 3 | LINE 聯絡方式 | 一律官方帳號 `@933rjphz`，不用舊的個人 ID |
| 4 | Calendly | 一律 `calendly.com/kp0988367482/30min` |
| 5 | 字型組合 | 五套字型的標準 query string，見 `CLAUDE.md` |
| 6 | HTML 基本標籤 | `lang`、`viewport`、`title`、`description` 四項齊全 |
| 7 | 外部連結 | 一律 `target="_blank"` |

每一條的權威定義都在專案根目錄的 `CLAUDE.md`。**要改規則，先改 `CLAUDE.md`，
再同步改 `check.sh`**——兩邊講的必須是同一件事。

## 修的時候注意

- **逐項修，不要一次全掃。**每一類的成因不同，混在一起改很容易誤傷。
- **第 2 項（金額）永遠不要自動改。**`$19` 和 `$79` 是兩個不同商品，不是筆誤。
  這一項報錯代表某頁掛錯了商品，屬於商業決策——回報給使用者，不要自己選一個。
- **第 6 項的 `description`** 需要針對每頁內容各寫一句，不能套同一句罐頭文案。
- 改完一定要重跑 `check.sh` 確認歸零，再 commit。

## 新增頁面時

複製一個 `arrival-*` 頁當骨架（它們最貼近標準），改完內容後跑一次 `check.sh`，
把七項都清乾淨再 commit。
