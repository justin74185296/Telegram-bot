# 🌈 魔法跳跳橋 Magic Bouncy Bridge 🌈

超可愛的兒童版踩墊子遊戲！適合 5 歲小朋友玩～
靈感來自魷魚遊戲的玻璃橋，但完全沒有可怕元素，只有可愛的墜落和滿滿的鼓勵！

---

## 📦 安裝 & 執行（超簡單！）

### 方法一：一鍵啟動（推薦！什麼都不用裝）

```bash
git clone https://github.com/justin74185296/Telegram-bot.git
cd Telegram-bot
git checkout cursor/magic-bouncy-bridge-6031
bash start_game.sh
```

腳本會自動：建虛擬環境 → 裝 pygame → 啟動遊戲 ✅
之後每次只要 `bash start_game.sh` 就好，不用重新安裝！

### 方法二：手動安裝

```bash
git clone https://github.com/justin74185296/Telegram-bot.git
cd Telegram-bot
git checkout cursor/magic-bouncy-bridge-6031

# 建立虛擬環境（macOS Homebrew Python 必須）
python3 -m venv .venv_game
source .venv_game/bin/activate

# 安裝 pygame（Python 3.14 用 pygame-ce）
pip install pygame-ce

# 啟動遊戲！
python magic_bridge_game.py
```

---

## 🎮 操作方式（超簡單！）

| 操作 | 方式 |
|------|------|
| 選上面墊子 | 滑鼠點畫面**左半邊** 或 按 **← 左方向鍵** |
| 選下面墊子 | 滑鼠點畫面**右半邊** 或 按 **→ 右方向鍵** |
| 開始遊戲 | 按 **空白鍵** 或 **滑鼠點一下** |
| 重新開始 | 按 **R** |

---

## 🎪 遊戲特色

- 🐻 超可愛小熊角色（三種表情：開心、驚訝、超開心）
- 🌉 12 格魔法橋，每次隨機生成
- ✅ 綠色安全墊子（笑臉）→ 開心跳過！
- 🎀 粉色彈跳墊子（彈簧）→ 可愛墜落 + 馬上彈回！
- ☁️ 墜落時雲朵接住、氣球帶著飛回來
- ⭐ 滿滿的星星、彩帶、泡泡特效
- 🌈 過關放煙火 + 大彩虹慶祝
- 💬 超多正向鼓勵語：「沒事沒事～我們是最強的！」
- 🔊 程式自動產生音效（不需要額外檔案）
- ❌ 完全沒有死亡、淘汰或可怕元素！

---

## ⚙️ 自訂調整

打開 `magic_bridge_game.py`，在檔案最上方可以輕鬆調整：

```python
GRAVITY = 0.35              # 重力（越大掉越快）
FALL_TARGET_Y = 畫面高度*0.72  # 墜落多深
BOUNCE_VELOCITY = -8.0      # 彈回力道
TOTAL_STEPS = 12            # 橋的格數（10-14）
BOUNCE_CHANCE = 0.25        # 彈跳墊機率（0.2-0.3）
FALL_SWING_AMPLITUDE = 25   # 墜落左右搖擺幅度
SCREEN_SHAKE_AMOUNT = 4     # 螢幕抖動幅度
```

---

## 📋 系統需求

- Python 3.10 以上
- pygame 或 pygame-ce
- macOS / Windows / Linux 都可以
