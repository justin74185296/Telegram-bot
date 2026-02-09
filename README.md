# 🌈 魔法跳跳橋 Magic Bouncy Bridge 🌈

超可愛的兒童版踩墊子遊戲！適合 5 歲小朋友玩～
靈感來自魷魚遊戲的玻璃橋，但完全沒有可怕元素，只有可愛的墜落和滿滿的鼓勵！

---

## 📦 安裝方式

### 第一步：下載遊戲

**方法 A：用 Git 下載（推薦）**
```bash
git clone https://github.com/justin74185296/Telegram-bot.git
cd Telegram-bot
git checkout cursor/magic-bouncy-bridge-6031
```

**方法 B：直接下載**
到 GitHub 頁面下載 `magic_bridge_game.py` 這個檔案就好。

### 第二步：安裝 Pygame

> ⚠️ **Python 3.14 使用者注意！**
> 如果你的 Python 是 3.14 版，`pygame` 可能還沒支援。
> 請改用 `pygame-ce`（社群版，更新比較快）：

```bash
# 方法 1：先試試 pygame-ce（推薦 Python 3.14 使用者）
pip3 install pygame-ce

# 方法 2：如果上面失敗，試試標準 pygame
pip3 install pygame

# 如果兩個都裝不上，建議用 Python 3.12 或 3.13：
# brew install python@3.13
# python3.13 -m pip install pygame
# python3.13 magic_bridge_game.py
```

### 第三步：執行遊戲 🎮

```bash
# 切到遊戲所在的資料夾
cd Telegram-bot  # 或者你放 magic_bridge_game.py 的地方

# 執行遊戲！
python3 magic_bridge_game.py
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
