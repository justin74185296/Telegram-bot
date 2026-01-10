# 🌍 Telegram City Guide Bot / 城市指南 Bot

> ⚠️ **此 Bot 純粹用於程式學習、資料結構研究與全球地點匹配實驗，嚴禁公開部署或用於任何商業用途。**  
> ⚠️ **This Bot is purely for programming learning and experiments. Do not deploy publicly or commercially.**

一個使用 Python + aiogram 3.x 構建的 Telegram Bot，展示模糊字串匹配和 JSON 資料處理技術。

A Telegram Bot built with Python + aiogram 3.x, demonstrating fuzzy string matching and JSON data processing.

## ✨ 功能特點 / Features

- 🔍 **模糊搜尋** - 使用 fuzzywuzzy 進行智能匹配（70% 相似度門檻）
- 📊 **優先級排序** - sub_area > area > city > country
- ⌨️ **Inline Keyboards** - 互動式結果選擇
- 🌐 **多語言支援** - 中英日韓等多種語言輸入
- 📱 **TG 聯絡資訊** - 部分景點包含官方 Telegram 連結
- 💾 **純靜態資料** - 無網路請求，所有資料存於 JSON

## 📁 專案結構 / Project Structure

```
telegram_city_guide/
├── main.py              # 主程式入口 / Main entry point
├── handlers.py          # 訊息處理器 / Message handlers
├── database.py          # 資料庫模組 / Database module
├── requirements.txt     # 依賴套件 / Dependencies
├── .env.example         # 環境變數範例 / Env example
├── README.md            # 說明文件 / Documentation
└── data/
    └── global_locations.json  # 地點資料 (45+ 筆) / Location data
```

## 🚀 快速開始 / Quick Start

### 1. 安裝依賴 / Install Dependencies

```bash
cd telegram_city_guide
pip install -r requirements.txt
```

### 2. 設定 Bot Token / Configure Bot Token

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 並填入你的 Bot Token（從 @BotFather 獲取）
# Edit .env and add your Bot Token (get from @BotFather)
BOT_TOKEN=your_bot_token_here
```

### 3. 執行 Bot / Run the Bot

```bash
python main.py
```

## 📖 使用方式 / How to Use

### 指令 / Commands

| 指令 | 說明 |
|------|------|
| `/start` | 開始使用，顯示歡迎訊息 |
| `/help` | 顯示使用說明 |

### 搜尋範例 / Search Examples

直接輸入地點名稱即可搜尋：

- `Tokyo Senso-ji` → 東京淺草寺
- `Paris Eiffel` → 巴黎艾菲爾鐵塔
- `台北 101` → 台北101大樓
- `Bangkok Temple` → 曼谷寺廟
- `New York Times Square` → 紐約時代廣場

## 🔧 技術細節 / Technical Details

### 依賴套件 / Dependencies

- `aiogram>=3.4.0` - Telegram Bot 框架（非同步）
- `fuzzywuzzy>=0.18.0` - 模糊字串匹配
- `python-Levenshtein>=0.25.0` - 加速 fuzzywuzzy
- `python-dotenv>=1.0.0` - 環境變數管理

### 匹配邏輯 / Matching Logic

1. 使用多種模糊匹配演算法：
   - `ratio` - 整體相似度
   - `partial_ratio` - 部分匹配
   - `token_sort_ratio` - 詞序無關匹配
   - `token_set_ratio` - 詞集合匹配

2. 優先級排序（數字越小越優先）：
   - sub_area: 1
   - area/nickname: 2
   - city/address_detail: 3
   - country: 4

3. 相同分數時，有 TG 聯絡資訊的記錄優先

### JSON 資料結構 / Data Structure

```json
{
  "country": "Japan",
  "city": "Tokyo",
  "area": "Senso-ji Temple",
  "sub_area": "Asakusa District",
  "nickname": "Thunder Gate Temple",
  "address_detail": "2-3-1 Asakusa, Taito City",
  "types": ["temple", "cultural landmark", "shopping street"],
  "price_range": "JPY 0 (free entry)",
  "tg_contacts": ["@tokyotravelguide", "t.me/japantourism"],
  "notes": "Tokyo's oldest temple...",
  "last_update": "2025-12"
}
```

## 📊 資料涵蓋 / Data Coverage

包含 45+ 筆全球知名景點：

| 地區 | 景點數 | 範例 |
|------|--------|------|
| 🌏 亞洲 | 20+ | 東京、京都、曼谷、台北、香港、新加坡、首爾 |
| 🌍 歐洲 | 10+ | 巴黎、羅馬、倫敦、阿姆斯特丹、柏林、巴塞隆納 |
| 🌎 美洲 | 8+ | 紐約、舊金山、里約、庫斯科、坎昆 |
| 🌐 其他 | 7+ | 雪梨、開羅、伊斯坦堡、杜拜、開普敦 |

## 📝 學習重點 / Learning Points

這個專案展示了以下技術：

1. **aiogram 3.x**
   - Router 和 Filter 使用
   - Inline Keyboard 建立
   - Callback Query 處理
   - Markdown 格式化

2. **模糊搜尋**
   - fuzzywuzzy 多種演算法
   - 優先級權重設計
   - 門檻值調整

3. **Python 最佳實踐**
   - 模組化程式碼結構
   - 類型提示 (Type Hints)
   - 環境變數管理
   - 完整的錯誤處理

## ⚠️ 免責聲明 / Disclaimer

- 本專案僅供程式學習使用
- 資料為虛構範例，不保證準確性
- 請勿用於商業或公開服務
- This project is for learning purposes only
- Data is fictional and may not be accurate
- Do not use commercially or deploy publicly

## 📄 授權 / License

此專案僅供教育用途。
This project is for educational purposes only.
