# Telegram-bot

---

## 兒童版魷魚遊戲合集 (Kid-Friendly Squid Games)

適合 5 歲小朋友的超可愛遊戲！完全沒有任何可怕元素，只有可愛、搞笑、正向鼓勵！

### macOS 安裝與執行

```bash
# 如果 Homebrew Python 不讓你直接 pip，用 venv：
cd ~/Telegram-bot
python3.12 -m venv venv
source venv/bin/activate
pip install pygame
```

> 需要先安裝 Python 3.12：`brew install python@3.12`
> Python 3.14 的 pygame 支援尚未完整，建議用 3.12

### Windows 安裝與執行

```bash
pip install pygame
```

---

### 遊戲 1: 魔法跳跳橋 (Glass Bridge)

```bash
python3 magic_bridge_game.py
```

踩墊子過橋！踩到彈跳墊子會可愛地掉下去再彈回來。

| 操作 | 說明 |
|------|------|
| 滑鼠點畫面上半部 / 按 ↑ 或 ← | 選上面的墊子 |
| 滑鼠點畫面下半部 / 按 ↓ 或 → | 選下面的墊子 |
| 空格鍵 | 開始遊戲 |
| R 鍵 | 重新開始 |

---

### 遊戲 2: 魔法跳繩橋 (Jump Rope)

```bash
python3 magic_jumprope_game.py
```

和英熙姐姐、哲秀哥哥一起跳繩過橋！繩子轉過來的時候按空格跳起來！

| 操作 | 說明 |
|------|------|
| 空格鍵 或 滑鼠左鍵 | 跳躍 |
| 空格鍵 | 開始遊戲 |
| R 鍵 | 重新開始 |
| ESC | 離開遊戲 |