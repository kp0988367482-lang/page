#!/usr/bin/env bash
# 全站一致性稽核。全部通過時 exit 0，有問題時列出並 exit 1。
# 用法：bash .claude/skills/site-check/check.sh
cd "$(dirname "$0")/../../.." || exit 1

fail=0
# report <標題> <內容>：內容非空才輸出，並標記失敗
report() {
  [ -z "$2" ] && return 0
  fail=1
  printf '\n[%s]\n%s\n' "$1" "$(printf '%s\n' "$2" | sed 's/^/  /')"
}
clip() { sed 's/^\(.\{125\}\).*/\1…/'; }

# --- 1. PayPal 網址寫法應統一為短網址 paypal.me ---
report 'PayPal 網址用了長版，應改為 https://paypal.me/HSIANGENTSAI/<金額>' \
  "$(grep -n 'paypal\.com/paypalme' ./*.html | clip)"

# --- 2. 金額必須對應正確商品：$19=PDF攻略（arrival-*），$79=1:1諮詢（非 arrival-*）---
report '$19（PDF 攻略）出現在非 arrival-* 頁' \
  "$(grep -ln 'paypal[^"]*/19' ./*.html | grep -v '^\./arrival-')"
report '$79（1:1 諮詢）出現在 arrival-* 頁' \
  "$(grep -ln 'paypal[^"]*/79' ./arrival-*.html 2>/dev/null)"

# --- 3. LINE 聯絡方式應統一為官方帳號（只比對 line.me 連結，不碰 email）---
report '使用了舊的個人 LINE ID，應改為官方帳號 @933rjphz' \
  "$(grep -n 'line\.me/[^"]*seoulmate31' ./*.html | clip)"

# --- 4. Calendly 應統一為實際運作中的預約連結 ---
# TODO(待確認)：seoulmate31 這個 Calendly 帳號是否仍有效，尚未向站主確認。
#   若有效，請刪除本項檢查；若失效，維持現狀即可。
report 'Calendly 連到失效帳號，應改為 calendly.com/kp0988367482/30min' \
  "$(grep -n 'calendly\.com/seoulmate31' ./*.html | clip)"

# --- 5. 字型組合應一致 ---
CANON='family=Noto+Serif+TC:wght@400;700;900&family=DM+Serif+Display:ital@0;1&family=Noto+Sans+KR:wght@300;400;700&family=Outfit:wght@400;500;600;700&family=Space+Mono&display=swap'
fonts=$(for f in ./*.html; do
  link=$(grep -o 'family=[^"'"'"']*' "$f" | head -1)
  if   [ -z "$link" ];        then echo "$f：完全沒載入 Google Fonts"
  elif [ "$link" != "$CANON" ]; then echo "$f：字型組合與標準不符"
  fi
done)
report '字型引用不一致（標準見 CLAUDE.md）' "$fonts"

# --- 6. 每頁基本 HTML 衛生 ---
html=$(for f in ./*.html; do
  grep -qi '<html[^>]*lang='   "$f" || echo "$f：<html> 缺 lang 屬性"
  grep -qi 'name="viewport"'   "$f" || echo "$f：缺 viewport meta（手機版會壞）"
  grep -qi '<title>'           "$f" || echo "$f：缺 <title>"
  grep -qi 'name="description"' "$f" || echo "$f：缺 description meta（影響 SEO）"
done)
report 'HTML 基本標籤缺漏' "$html"

# --- 7. 外連應開新分頁 ---
report '外部連結沒有 target="_blank"' \
  "$(grep -n 'href="https\?://' ./*.html \
     | grep -v 'fonts\.googleapis\|fonts\.gstatic\|w3\.org\|assets\.calendly' \
     | grep -v 'target="_blank"' | clip)"

if [ "$fail" -eq 0 ]; then
  echo "✅ 全站一致性檢查通過（$(ls -1 ./*.html | wc -l | tr -d ' ') 個頁面）"
fi
exit "$fail"
