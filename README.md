# Telegram Bot

一個簡單的 Telegram 機器人，使用 Python 和 python-telegram-bot 函式庫建立。

## 功能

- `/start` - 開始使用機器人
- `/help` - 查看幫助說明
- `/echo <訊息>` - 機器人會重複你的訊息
- 回覆任何文字訊息

## 安裝

1. 確保已安裝 Python 3.8 或更新版本

2. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

## 執行

啟動機器人：
```bash
python bot.py
```

## 設定

如需更改 Bot Token，請編輯 `bot.py` 中的 `BOT_TOKEN` 變數。

## 注意事項

- 請確保 Bot Token 保密，不要公開分享
- 機器人需要持續運行才能回應訊息
