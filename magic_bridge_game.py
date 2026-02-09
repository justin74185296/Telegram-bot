#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌈 魔法跳跳橋 - 兒童版踩玻璃遊戲 🌈
Magic Bouncy Bridge - Kid-Friendly Glass Bridge Game

適合 5 歲小朋友玩的超可愛跳跳橋遊戲！
靈感來自魷魚遊戲的玻璃橋，但完全沒有可怕元素，
只有可愛的小動物、搞笑的墜落、和滿滿的鼓勵！

安裝方式：
  Python 3.14 → pip3 install pygame-ce  （社群版，支援最新 Python）
  其他版本   → pip3 install pygame

執行方式：python3 magic_bridge_game.py

操作：
  - 滑鼠點擊畫面左半邊 = 選上面的墊子
  - 滑鼠點擊畫面右半邊 = 選下面的墊子
  - 左右方向鍵也可以選擇（備用操作）
  - 空白鍵 = 開始遊戲
  - R 鍵 = 重新開始

Python 版本相容：3.10+（含 3.14，使用 pygame-ce）
"""

# ============================================================
# 匯入模組（支援 pygame 和 pygame-ce 兩種）
# ============================================================
import random
import math
import sys
import os

# 嘗試匯入 pygame（支援 pygame-ce 和標準 pygame）
try:
    import pygame
except ImportError:
    print("=" * 50)
    print("找不到 pygame 模組！")
    print("")
    print("請先安裝：")
    print("  Python 3.14 → pip3 install pygame-ce")
    print("  其他版本    → pip3 install pygame")
    print("=" * 50)
    sys.exit(1)

# ============================================================
# 初始化 Pygame
# ============================================================
# 嘗試初始化音效（如果失敗也不影響遊戲，靜音模式繼續玩）
SOUND_ENABLED = False
try:
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.init()
    pygame.mixer.init()
    SOUND_ENABLED = True
except Exception:
    # 音效初始化失敗，用靜音模式
    try:
        pygame.init()
    except Exception:
        pass
    SOUND_ENABLED = False

# ============================================================
# 遊戲常數設定（容易修改）
# ============================================================
SCREEN_WIDTH = 800          # 畫面寬度
SCREEN_HEIGHT = 600         # 畫面高度
FPS = 60                    # 每秒幀數

# 墜落動畫參數（可調整）
GRAVITY = 0.35              # 重力加速度（越大掉越快）
FALL_TARGET_Y = SCREEN_HEIGHT * 0.72  # 墜落到畫面 72% 高度
BOUNCE_VELOCITY = -8.0      # 彈回初速度（負值 = 往上）
FALL_SWING_AMPLITUDE = 25   # 墜落時左右搖擺幅度
FALL_SWING_SPEED = 6.0      # 搖擺速度
MAX_FALL_TIME = 1.5         # 最大墜落+彈回時間（秒）
SCREEN_SHAKE_AMOUNT = 4     # 螢幕抖動幅度

# 墊子設定
TOTAL_STEPS = 12            # 總共幾格墊子（10-14）
BOUNCE_CHANCE = 0.25        # 彈跳墊子機率（25%，讓小孩容易過關）

# 顏色定義（鮮豔卡通色）
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 250)
LIGHT_BLUE = (173, 216, 255)
SAFE_GREEN = (100, 220, 100)
SAFE_GREEN_DARK = (70, 180, 70)
BOUNCE_PINK = (255, 150, 200)
BOUNCE_PINK_DARK = (220, 120, 170)
BOUNCE_YELLOW = (255, 230, 100)
GOLD = (255, 215, 0)
RED = (255, 100, 100)
ORANGE = (255, 180, 80)
PURPLE = (180, 130, 255)
RAINBOW_COLORS = [
    (255, 100, 100), (255, 180, 80), (255, 230, 100),
    (100, 220, 100), (100, 180, 255), (180, 130, 255)
]
CLOUD_WHITE = (255, 255, 255)
CLOUD_LIGHT = (240, 248, 255)
BALLOON_RED = (255, 80, 80)
BALLOON_BLUE = (80, 150, 255)
BALLOON_YELLOW = (255, 230, 50)
BALLOON_GREEN = (80, 220, 120)

# ============================================================
# 音效生成（用程式產生簡單音效，不需外部檔案）
# ============================================================
def generate_tone(frequency, duration_ms, volume=0.3, wave_type='sine'):
    """用程式產生簡單的音效（不需要外部音效檔案）"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)  # 16-bit mono
        max_val = int(32767 * volume)
        for i in range(n_samples):
            t = i / sample_rate
            if wave_type == 'sine':
                val = math.sin(2.0 * math.pi * frequency * t)
            elif wave_type == 'square':
                val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
            else:
                val = math.sin(2.0 * math.pi * frequency * t)
            # 淡出效果
            fade = 1.0 - (i / n_samples) * 0.5
            sample = int(val * max_val * fade)
            sample = max(-32768, min(32767, sample))
            # 寫入 little-endian 16-bit
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    except Exception:
        return None


def generate_happy_jump_sound():
    """快樂跳躍音效：上升的叮叮聲"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        duration_ms = 200
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)
        max_val = int(32767 * 0.25)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 600 + (i / n_samples) * 400  # 頻率上升
            val = math.sin(2.0 * math.pi * freq * t)
            fade = 1.0 - (i / n_samples) * 0.3
            sample = int(val * max_val * fade)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


def generate_fall_sound():
    """墜落音效：下降的呼～聲"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        duration_ms = 400
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)
        max_val = int(32767 * 0.2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 500 - (i / n_samples) * 300  # 頻率下降
            val = math.sin(2.0 * math.pi * freq * t)
            fade = 1.0 - (i / n_samples) * 0.5
            sample = int(val * max_val * fade)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


def generate_bounce_sound():
    """彈回音效：啵～彈起來的聲音"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        duration_ms = 250
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)
        max_val = int(32767 * 0.3)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 300 + (i / n_samples) * 600  # 頻率快速上升
            val = math.sin(2.0 * math.pi * freq * t)
            # 加入一點震動感
            val += 0.3 * math.sin(2.0 * math.pi * freq * 2 * t)
            fade = 1.0 - (i / n_samples) * 0.4
            sample = int(val * max_val * fade)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


def generate_victory_sound():
    """勝利音效：啦啦啦上升和弦"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        duration_ms = 800
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)
        max_val = int(32767 * 0.25)
        notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
        for i in range(n_samples):
            t = i / sample_rate
            progress = i / n_samples
            # 依時間切換音符
            note_idx = min(int(progress * len(notes)), len(notes) - 1)
            freq = notes[note_idx]
            val = math.sin(2.0 * math.pi * freq * t)
            val += 0.5 * math.sin(2.0 * math.pi * freq * 2 * t)
            fade = 1.0 - progress * 0.3
            sample = int(val * max_val * fade)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


# ============================================================
# 音效物件
# ============================================================
snd_jump = generate_happy_jump_sound()
snd_fall = generate_fall_sound()
snd_bounce = generate_bounce_sound()
snd_victory = generate_victory_sound()


def play_sound(sound):
    """安全播放音效"""
    if sound and SOUND_ENABLED:
        try:
            sound.play()
        except Exception:
            pass


# ============================================================
# 畫面設定
# ============================================================
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🌈 魔法跳跳橋 - Magic Bouncy Bridge 🌈")
clock = pygame.time.Clock()

# ============================================================
# 字型設定（支援 macOS / Windows / Linux 中文字型）
# ============================================================
import warnings as _warnings
import platform as _platform

# 暫時關閉 pygame 字型警告（找不到字型時不會刷滿螢幕）
_warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

# 快取：找到的中文字型路徑或名稱（只搜尋一次）
_cached_chinese_font_path = None
_font_search_done = False


def _find_chinese_font():
    """
    搜尋系統中文字型（只執行一次，結果快取）
    優先嘗試直接從檔案路徑載入（最快、最可靠）
    """
    global _cached_chinese_font_path, _font_search_done
    if _font_search_done:
        return _cached_chinese_font_path
    _font_search_done = True

    system = _platform.system()

    # === 方法 1：直接從檔案路徑載入（最可靠） ===
    font_file_paths = []

    if system == "Darwin":  # macOS
        font_file_paths = [
            # macOS 內建中文字型（幾乎所有 Mac 都有）
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/Supplemental/STHeiti Light.ttc",
            "/System/Library/Fonts/Supplemental/STHeiti Medium.ttc",
            "/System/Library/Fonts/Supplemental/Hiragino Sans GB W3.otf",
        ]
    elif system == "Windows":
        font_file_paths = [
            "C:/Windows/Fonts/msjh.ttc",      # 微軟正黑體
            "C:/Windows/Fonts/msyh.ttc",       # 微軟雅黑
            "C:/Windows/Fonts/simhei.ttf",     # 黑體
            "C:/Windows/Fonts/simsun.ttc",     # 宋體
        ]
    else:  # Linux
        font_file_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]

    for path in font_file_paths:
        if os.path.exists(path):
            try:
                test_font = pygame.font.Font(path, 24)
                test_render = test_font.render("測試", True, (255, 255, 255))
                if test_render.get_width() > 20:
                    _cached_chinese_font_path = path
                    return path
            except Exception:
                continue

    # === 方法 2：用 pygame SysFont（備用，macOS 用小寫無空格名） ===
    if system == "Darwin":
        sys_names = ["pingfangtc", "pingfangsc", "stheitilight", "stheitimedium",
                     "hiraginosans", "hiraginosansgb", "applegothic"]
    elif system == "Windows":
        sys_names = ["microsoftjhenghei", "microsoftyahei", "simhei", "simsun"]
    else:
        sys_names = ["notosanscjktc", "notosanscjksc", "wenquanyimicrohei",
                     "droidsansfallback", "notosanstc"]

    for name in sys_names:
        try:
            f = pygame.font.SysFont(name, 24)
            test = f.render("測試", True, (255, 255, 255))
            if test.get_width() > 20:
                _cached_chinese_font_path = name  # 存名稱（非路徑）
                return name
        except Exception:
            continue

    return None


def get_font(size):
    """取得支援中文的字型（使用快取，超快）"""
    font_ref = _find_chinese_font()

    if font_ref is not None:
        try:
            if os.path.sep in str(font_ref) or font_ref.endswith(('.ttf', '.ttc', '.otf')):
                # 從檔案路徑載入
                return pygame.font.Font(font_ref, size)
            else:
                # 從系統字型名稱載入
                return pygame.font.SysFont(font_ref, size)
        except Exception:
            pass

    # 找不到中文字型，用預設字型
    return pygame.font.Font(None, size)


# 預載字型（因為有快取，只會搜尋一次字型）
font_large = get_font(42)
font_medium = get_font(30)
font_small = get_font(22)
font_tiny = get_font(18)
font_emoji = get_font(48)

# 測試中文是否可顯示
_test_surface = font_medium.render("測試中文", True, WHITE)
CHINESE_SUPPORTED = _test_surface.get_width() > 30

# 恢復警告設定
_warnings.filterwarnings("default", category=UserWarning, module="pygame")


# 如果中文無法顯示，提供英文替代文字
def txt(chinese, english):
    """根據字型支援返回中文或英文"""
    return chinese if CHINESE_SUPPORTED else english


# ============================================================
# 粒子系統（星星、泡泡、彩帶）
# ============================================================
class Particle:
    """粒子物件：用於星星、泡泡、彩帶等特效"""
    def __init__(self, x, y, vx, vy, color, lifetime, shape='circle', size=5):
        self.x = x
        self.y = y
        self.vx = vx          # x 方向速度
        self.vy = vy           # y 方向速度
        self.color = color
        self.lifetime = lifetime  # 存活時間（幀數）
        self.max_lifetime = lifetime
        self.shape = shape     # 'circle', 'star', 'confetti'
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        """更新粒子位置和生命週期"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # 微重力
        self.lifetime -= 1
        self.rotation += self.rot_speed

    def draw(self, surface, offset_x=0, offset_y=0):
        """繪製粒子"""
        if self.lifetime <= 0:
            return
        alpha = max(0, self.lifetime / self.max_lifetime)
        size = max(1, int(self.size * alpha))
        dx = int(self.x) + offset_x
        dy = int(self.y) + offset_y

        if self.shape == 'circle':
            pygame.draw.circle(surface, self.color, (dx, dy), size)
        elif self.shape == 'star':
            draw_star(surface, dx, dy, size, self.color, self.rotation)
        elif self.shape == 'confetti':
            w = max(2, size * 2)
            h = max(1, size)
            rect = pygame.Rect(dx - w // 2, dy - h // 2, w, h)
            pygame.draw.rect(surface, self.color, rect)

    @property
    def alive(self):
        return self.lifetime > 0


def draw_star(surface, x, y, size, color, rotation=0):
    """繪製五角星"""
    points = []
    for i in range(10):
        angle = math.radians(rotation + i * 36 - 90)
        r = size if i % 2 == 0 else size * 0.4
        px = x + r * math.cos(angle)
        py = y + r * math.sin(angle)
        points.append((px, py))
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, points)


# ============================================================
# 全域粒子列表
# ============================================================
particles = []


def spawn_stars(x, y, count=8):
    """在指定位置生成星星粒子"""
    for _ in range(count):
        vx = random.uniform(-3, 3)
        vy = random.uniform(-4, -1)
        color = random.choice(RAINBOW_COLORS + [GOLD, WHITE])
        size = random.randint(4, 8)
        lifetime = random.randint(30, 50)
        particles.append(Particle(x, y, vx, vy, color, lifetime, 'star', size))


def spawn_confetti(x, y, count=15):
    """在指定位置生成彩帶粒子"""
    for _ in range(count):
        vx = random.uniform(-5, 5)
        vy = random.uniform(-6, -1)
        color = random.choice(RAINBOW_COLORS)
        size = random.randint(3, 7)
        lifetime = random.randint(40, 70)
        particles.append(Particle(x, y, vx, vy, color, lifetime, 'confetti', size))


def spawn_bubbles(x, y, count=6):
    """在指定位置生成泡泡粒子（墜落時用）"""
    for _ in range(count):
        vx = random.uniform(-2, 2)
        vy = random.uniform(-3, -0.5)
        color = random.choice([LIGHT_BLUE, CLOUD_WHITE, (200, 230, 255), PURPLE])
        size = random.randint(5, 12)
        lifetime = random.randint(25, 45)
        particles.append(Particle(x, y, vx, vy, color, lifetime, 'circle', size))


def spawn_victory_fireworks(x, y, count=30):
    """勝利煙火粒子"""
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 7)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(RAINBOW_COLORS + [GOLD, WHITE])
        size = random.randint(4, 10)
        lifetime = random.randint(40, 80)
        shape = random.choice(['star', 'confetti', 'circle'])
        particles.append(Particle(x, y, vx, vy, color, lifetime, shape, size))


# ============================================================
# 小動物角色繪製
# ============================================================
def draw_bear(surface, x, y, size, expression='happy', rotation=0):
    """
    繪製小熊角色
    expression: 'happy' (開心), 'surprised' (墜落驚訝), 'super_happy' (超開心彈回)
    """
    # 套用旋轉：建立臨時 surface 再旋轉
    temp_size = size * 3
    temp = pygame.Surface((temp_size, temp_size), pygame.SRCALPHA)
    cx, cy = temp_size // 2, temp_size // 2

    body_color = (180, 130, 80)     # 棕色身體
    belly_color = (240, 210, 170)   # 淺色肚子
    ear_color = (150, 100, 60)
    cheek_color = (255, 180, 180)

    s = size  # 縮寫

    # 身體（橢圓）
    body_rect = pygame.Rect(cx - s * 0.5, cy - s * 0.3, s, s * 1.1)
    pygame.draw.ellipse(temp, body_color, body_rect)

    # 肚子
    belly_rect = pygame.Rect(cx - s * 0.3, cy + s * 0.05, s * 0.6, s * 0.6)
    pygame.draw.ellipse(temp, belly_color, belly_rect)

    # 頭
    head_rect = pygame.Rect(cx - s * 0.45, cy - s * 0.8, s * 0.9, s * 0.75)
    pygame.draw.ellipse(temp, body_color, head_rect)

    # 耳朵
    pygame.draw.circle(temp, ear_color, (cx - int(s * 0.35), cy - int(s * 0.75)), int(s * 0.18))
    pygame.draw.circle(temp, cheek_color, (cx - int(s * 0.35), cy - int(s * 0.75)), int(s * 0.1))
    pygame.draw.circle(temp, ear_color, (cx + int(s * 0.35), cy - int(s * 0.75)), int(s * 0.18))
    pygame.draw.circle(temp, cheek_color, (cx + int(s * 0.35), cy - int(s * 0.75)), int(s * 0.1))

    # 臉部表情
    face_cx = cx
    face_cy = cy - int(s * 0.45)

    # 腮紅
    pygame.draw.circle(temp, cheek_color, (face_cx - int(s * 0.25), face_cy + int(s * 0.1)), int(s * 0.1))
    pygame.draw.circle(temp, cheek_color, (face_cx + int(s * 0.25), face_cy + int(s * 0.1)), int(s * 0.1))

    # 鼻子
    pygame.draw.circle(temp, (80, 50, 30), (face_cx, face_cy + int(s * 0.05)), int(s * 0.08))

    if expression == 'happy':
        # 開心眼睛（小圓點）
        pygame.draw.circle(temp, BLACK, (face_cx - int(s * 0.15), face_cy - int(s * 0.05)), int(s * 0.06))
        pygame.draw.circle(temp, BLACK, (face_cx + int(s * 0.15), face_cy - int(s * 0.05)), int(s * 0.06))
        # 眼睛亮點
        pygame.draw.circle(temp, WHITE, (face_cx - int(s * 0.13), face_cy - int(s * 0.07)), int(s * 0.025))
        pygame.draw.circle(temp, WHITE, (face_cx + int(s * 0.17), face_cy - int(s * 0.07)), int(s * 0.025))
        # 微笑
        smile_rect = pygame.Rect(face_cx - int(s * 0.12), face_cy + int(s * 0.05), int(s * 0.24), int(s * 0.12))
        pygame.draw.arc(temp, (80, 50, 30), smile_rect, math.pi + 0.2, 2 * math.pi - 0.2, 2)

    elif expression == 'surprised':
        # 驚訝眼睛（大圓，星星眼）
        # 左眼星星
        draw_star(temp, face_cx - int(s * 0.15), face_cy - int(s * 0.05), int(s * 0.1), GOLD)
        # 右眼星星
        draw_star(temp, face_cx + int(s * 0.15), face_cy - int(s * 0.05), int(s * 0.1), GOLD)
        # 嘴巴 O 型
        pygame.draw.circle(temp, (80, 50, 30), (face_cx, face_cy + int(s * 0.12)), int(s * 0.08))
        pygame.draw.circle(temp, (255, 150, 150), (face_cx, face_cy + int(s * 0.12)), int(s * 0.05))

    elif expression == 'super_happy':
        # 超開心彈回（瞇眼笑）
        # 左眼 ^_^
        pygame.draw.arc(temp, BLACK,
                        pygame.Rect(face_cx - int(s * 0.22), face_cy - int(s * 0.12), int(s * 0.14), int(s * 0.12)),
                        0, math.pi, 2)
        # 右眼
        pygame.draw.arc(temp, BLACK,
                        pygame.Rect(face_cx + int(s * 0.08), face_cy - int(s * 0.12), int(s * 0.14), int(s * 0.12)),
                        0, math.pi, 2)
        # 大笑嘴巴
        smile_rect = pygame.Rect(face_cx - int(s * 0.15), face_cy + int(s * 0.02), int(s * 0.3), int(s * 0.18))
        pygame.draw.arc(temp, (80, 50, 30), smile_rect, math.pi + 0.1, 2 * math.pi - 0.1, 2)
        # 嘴巴填色（開心大嘴）
        pygame.draw.ellipse(temp, (255, 150, 150),
                            pygame.Rect(face_cx - int(s * 0.1), face_cy + int(s * 0.06), int(s * 0.2), int(s * 0.1)))

    # 手（在墜落時揮手）
    if expression == 'surprised':
        # 雙手舉高揮手
        arm_y = cy - int(s * 0.2)
        pygame.draw.line(temp, body_color, (cx - int(s * 0.5), arm_y),
                         (cx - int(s * 0.75), arm_y - int(s * 0.3)), max(3, int(s * 0.12)))
        pygame.draw.line(temp, body_color, (cx + int(s * 0.5), arm_y),
                         (cx + int(s * 0.75), arm_y - int(s * 0.3)), max(3, int(s * 0.12)))
        # 小手掌
        pygame.draw.circle(temp, belly_color, (cx - int(s * 0.75), arm_y - int(s * 0.3)), int(s * 0.08))
        pygame.draw.circle(temp, belly_color, (cx + int(s * 0.75), arm_y - int(s * 0.3)), int(s * 0.08))

    # 旋轉
    if rotation != 0:
        temp = pygame.transform.rotate(temp, rotation)

    # 繪製到主 surface
    rect = temp.get_rect(center=(int(x), int(y)))
    surface.blit(temp, rect)


# ============================================================
# 雲朵繪製
# ============================================================
def draw_cloud(surface, x, y, scale=1.0, color=CLOUD_WHITE):
    """繪製可愛的雲朵"""
    s = scale
    pygame.draw.circle(surface, color, (int(x), int(y)), int(25 * s))
    pygame.draw.circle(surface, color, (int(x - 20 * s), int(y + 5 * s)), int(20 * s))
    pygame.draw.circle(surface, color, (int(x + 20 * s), int(y + 5 * s)), int(20 * s))
    pygame.draw.circle(surface, color, (int(x - 10 * s), int(y - 10 * s)), int(18 * s))
    pygame.draw.circle(surface, color, (int(x + 10 * s), int(y - 10 * s)), int(18 * s))


# ============================================================
# 氣球繪製
# ============================================================
def draw_balloon(surface, x, y, color, size=20):
    """繪製氣球"""
    # 氣球本體
    pygame.draw.ellipse(surface, color,
                        (int(x - size * 0.6), int(y - size), int(size * 1.2), int(size * 1.4)))
    # 氣球亮點
    highlight_color = tuple(min(255, c + 60) for c in color)
    pygame.draw.circle(surface, highlight_color,
                       (int(x - size * 0.15), int(y - size * 0.5)), int(size * 0.2))
    # 氣球底部小三角
    triangle_pts = [
        (int(x), int(y + size * 0.4)),
        (int(x - size * 0.15), int(y + size * 0.3)),
        (int(x + size * 0.15), int(y + size * 0.3))
    ]
    pygame.draw.polygon(surface, color, triangle_pts)
    # 氣球線
    pygame.draw.line(surface, (150, 150, 150), (int(x), int(y + size * 0.4)),
                     (int(x), int(y + size * 0.9)), 1)


# ============================================================
# 彩虹繪製
# ============================================================
def draw_rainbow(surface, x, y, radius=60):
    """繪製半圓形彩虹"""
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0),
        (0, 200, 0), (0, 150, 255), (75, 0, 130), (148, 0, 211)
    ]
    for i, color in enumerate(colors):
        r = radius - i * 6
        if r > 5:
            rect = pygame.Rect(int(x - r), int(y - r), r * 2, r * 2)
            pygame.draw.arc(surface, color, rect, 0, math.pi, 4)


# ============================================================
# 墊子（Pad）類別
# ============================================================
class Pad:
    """墊子物件：安全墊子 or 魔法彈跳墊子"""
    def __init__(self, index, is_left, is_safe):
        self.index = index      # 第幾格
        self.is_left = is_left  # 左邊或右邊
        self.is_safe = is_safe  # True=安全, False=彈跳
        self.revealed = False   # 是否已揭露
        self.spring_anim = 0    # 彈簧動畫計數器
        self.bounce_offset = 0  # 彈跳墊壓下動畫 y 偏移

        # 計算墊子位置
        pad_area_start_x = 80
        pad_area_end_x = SCREEN_WIDTH - 80
        pad_spacing = (pad_area_end_x - pad_area_start_x) / (TOTAL_STEPS + 1)

        self.width = 52
        self.height = 40
        self.base_x = int(pad_area_start_x + pad_spacing * (index + 1))

        if is_left:
            self.base_y = 280
        else:
            self.base_y = 340

        self.x = self.base_x
        self.y = self.base_y

    def update(self):
        """更新墊子動畫"""
        if self.spring_anim > 0:
            self.spring_anim -= 1
            # 彈簧壓下再彈起的動畫
            progress = self.spring_anim / 20.0
            self.bounce_offset = math.sin(progress * math.pi * 3) * 8 * progress
        else:
            self.bounce_offset = 0

    def trigger_spring(self):
        """觸發彈簧動畫"""
        self.spring_anim = 20

    def draw(self, surface, highlight=False):
        """繪製墊子"""
        draw_y = self.y + int(self.bounce_offset)

        if self.revealed:
            if self.is_safe:
                # 安全墊子：綠色/藍色 + 笑臉
                color = SAFE_GREEN
                dark_color = SAFE_GREEN_DARK
            else:
                # 彈跳墊子：粉色 + 彈簧圖案
                color = BOUNCE_PINK
                dark_color = BOUNCE_PINK_DARK
        else:
            # 未揭露：神秘的淡紫色
            color = (200, 180, 255)
            dark_color = (170, 150, 220)

        # 墊子陰影
        shadow_rect = pygame.Rect(self.x - self.width // 2 + 3, draw_y - self.height // 2 + 3,
                                  self.width, self.height)
        pygame.draw.rect(surface, (100, 100, 120), shadow_rect, border_radius=8)

        # 墊子主體
        pad_rect = pygame.Rect(self.x - self.width // 2, draw_y - self.height // 2,
                               self.width, self.height)
        pygame.draw.rect(surface, color, pad_rect, border_radius=8)
        pygame.draw.rect(surface, dark_color, pad_rect, 3, border_radius=8)

        # 高亮效果（目前可選的墊子）
        if highlight:
            glow_rect = pygame.Rect(self.x - self.width // 2 - 4, draw_y - self.height // 2 - 4,
                                    self.width + 8, self.height + 8)
            pygame.draw.rect(surface, GOLD, glow_rect, 3, border_radius=10)

        # 墊子上的圖案
        if self.revealed:
            if self.is_safe:
                # 笑臉
                face_x = self.x
                face_y = draw_y
                pygame.draw.circle(surface, BLACK, (face_x - 7, face_y - 5), 3)
                pygame.draw.circle(surface, BLACK, (face_x + 7, face_y - 5), 3)
                smile = pygame.Rect(face_x - 8, face_y, 16, 8)
                pygame.draw.arc(surface, BLACK, smile, math.pi + 0.3, 2 * math.pi - 0.3, 2)
            else:
                # 彈簧圖案
                spring_x = self.x
                spring_y = draw_y - 5
                for i in range(4):
                    y_off = spring_y + i * 5
                    x_off = 6 if i % 2 == 0 else -6
                    pygame.draw.line(surface, BOUNCE_YELLOW,
                                     (spring_x - x_off, y_off),
                                     (spring_x + x_off, y_off + 5), 2)
                # 頂部小星星
                draw_star(surface, spring_x, spring_y - 6, 6, GOLD)
        else:
            # 未揭露時畫問號
            q_text = font_small.render("?", True, WHITE)
            q_rect = q_text.get_rect(center=(self.x, draw_y))
            surface.blit(q_text, q_rect)


# ============================================================
# 遊戲主類別
# ============================================================
class Game:
    """魔法跳跳橋遊戲主程式"""

    # 遊戲狀態常數
    STATE_TITLE = 'title'
    STATE_PLAYING = 'playing'
    STATE_FALLING = 'falling'
    STATE_BOUNCING = 'bouncing'
    STATE_MESSAGE = 'message'
    STATE_ADVANCING = 'advancing'
    STATE_VICTORY = 'victory'

    def __init__(self):
        """初始化遊戲"""
        self.state = self.STATE_TITLE
        self.total_wins = 0       # 總共過了幾次橋
        self.current_step = 0     # 目前在第幾格
        self.pads = []            # 墊子列表
        self.generate_pads()

        # 小動物位置
        self.bear_x = 40.0
        self.bear_y = 260.0
        self.bear_target_x = 40.0
        self.bear_target_y = 260.0

        # 墜落動畫變數
        # -------------------------------------------------------
        # 墜落感實現原理：
        # 1. 進入墜落狀態時，velocity_y 從 0 開始
        # 2. 每幀 velocity_y += GRAVITY（模擬重力加速度）
        # 3. bear_y += velocity_y（位置往下移動）
        # 4. 同時 bear_x 用 sin(fall_time * FALL_SWING_SPEED) 做左右搖擺
        # 5. 當 bear_y 超過 FALL_TARGET_Y 時，切換到「彈回」狀態
        # 6. 彈回時 velocity_y 設為 BOUNCE_VELOCITY（負值，往上）
        # 7. 彈回同時顯示雲朵/氣球動畫
        # 8. 回到原位後恢復正常狀態
        # -------------------------------------------------------
        self.velocity_y = 0.0      # y 方向速度
        self.fall_time = 0.0       # 墜落經過時間
        self.fall_start_x = 0.0    # 墜落起始 x
        self.fall_start_y = 0.0    # 墜落起始 y
        self.fall_rotation = 0.0   # 墜落旋轉角度
        self.bear_expression = 'happy'

        # 彈回動畫
        self.bounce_cloud_y = 0.0   # 雲朵接住的 y 位置
        self.bounce_phase = 0       # 0=下落中, 1=雲朵接住, 2=氣球飛回
        self.balloon_y = 0.0        # 氣球 y 位置

        # 螢幕抖動
        self.shake_timer = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        # 訊息顯示
        self.message_text = ""
        self.message_timer = 0
        self.message_sub_text = ""

        # 前進動畫
        self.advance_timer = 0

        # 勝利動畫
        self.victory_timer = 0
        self.firework_timer = 0

        # 標題動畫
        self.title_time = 0
        self.blink_timer = 0

        # 背景雲朵裝飾
        self.bg_clouds = []
        for _ in range(5):
            self.bg_clouds.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(30, 180),
                'speed': random.uniform(0.2, 0.6),
                'scale': random.uniform(0.5, 1.0)
            })

        # 鼓勵語列表
        self.encouragements = [
            txt("哎呀～掉下去啦！哈哈～", "Oops! Haha~"),
            txt("沒關係，我們再跳一次！加油喔～", "Try again! You can do it!"),
            txt("哇哦～飛起來了！哈哈～", "Wheee~ Flying! Haha~"),
            txt("沒事沒事～我們是最強的！", "No worries~ We're the best!"),
            txt("啵～彈起來啦！好好玩！", "Boing~ Bounced back! So fun!"),
            txt("哈哈～掉下去也超可愛的！", "Haha~ Even falling is cute!"),
            txt("加油加油！你超棒的！", "Go go go! You're awesome!"),
            txt("魔法彈簧救你啦～飛上來！", "Magic spring saved you~!"),
        ]

    def generate_pads(self):
        """隨機生成墊子序列"""
        self.pads = []
        for i in range(TOTAL_STEPS):
            # 隨機決定左邊或右邊是安全的
            left_safe = random.random() > BOUNCE_CHANCE
            # 確保至少有一邊是安全的
            if not left_safe:
                right_safe = True
            else:
                right_safe = random.random() > BOUNCE_CHANCE
                if not right_safe and not left_safe:
                    # 保證至少一邊安全
                    if random.random() > 0.5:
                        left_safe = True
                    else:
                        right_safe = True

            self.pads.append({
                'left': Pad(i, True, left_safe),
                'right': Pad(i, False, right_safe),
            })

    def reset_game(self):
        """重置遊戲（保留總過橋次數）"""
        self.state = self.STATE_PLAYING
        self.current_step = 0
        self.generate_pads()
        self.bear_x = 40.0
        self.bear_y = 260.0
        self.bear_target_x = 40.0
        self.bear_target_y = 260.0
        self.velocity_y = 0.0
        self.fall_time = 0.0
        self.bear_expression = 'happy'
        self.message_timer = 0
        self.victory_timer = 0
        particles.clear()

    def get_pad_position(self, step_index, is_left):
        """取得某格墊子的中心位置"""
        if step_index < 0 or step_index >= TOTAL_STEPS:
            return 40.0, 260.0
        side = 'left' if is_left else 'right'
        pad = self.pads[step_index][side]
        return float(pad.x), float(pad.y - 25)  # 站在墊子上方

    def handle_choice(self, is_left):
        """處理玩家選擇（左或右墊子）"""
        if self.state != self.STATE_PLAYING:
            return
        if self.current_step >= TOTAL_STEPS:
            return

        side = 'left' if is_left else 'right'
        pad = self.pads[self.current_step][side]
        other_side = 'right' if is_left else 'left'
        other_pad = self.pads[self.current_step][other_side]

        # 揭露兩邊墊子
        pad.revealed = True
        other_pad.revealed = True

        if pad.is_safe:
            # 踩到安全墊子！開心前進！
            play_sound(snd_jump)
            target_x, target_y = self.get_pad_position(self.current_step, is_left)
            self.bear_target_x = target_x
            self.bear_target_y = target_y
            self.state = self.STATE_ADVANCING
            self.advance_timer = 25
            self.bear_expression = 'happy'
            # 生成星星特效
            spawn_stars(target_x, target_y - 10, 10)
        else:
            # 踩到彈跳墊子！觸發可愛墜落！
            play_sound(snd_fall)
            pad.trigger_spring()  # 觸發彈簧動畫

            # 設定墜落動畫初始值
            target_x, target_y = self.get_pad_position(self.current_step, is_left)
            self.bear_x = target_x
            self.bear_y = target_y
            self.fall_start_x = target_x
            self.fall_start_y = target_y
            self.velocity_y = -3.0   # 先微微往上跳一下再掉（更有彈跳感）
            self.fall_time = 0.0
            self.fall_rotation = 0.0
            self.bounce_phase = 0
            self.bear_expression = 'surprised'
            self.state = self.STATE_FALLING
            self.shake_timer = 10  # 輕微螢幕抖動

    def update_falling(self):
        """
        更新墜落動畫
        -------------------------------------------------------
        墜落動畫實現說明：
        1. velocity_y 每幀增加 GRAVITY（模擬重力加速度 g=0.35）
        2. bear_y 每幀增加 velocity_y（位置下移）
        3. bear_x 使用 sin(fall_time * SWING_SPEED) * AMPLITUDE 做搖擺
        4. fall_rotation 隨時間增加（小動物轉圈圈）
        5. 定期產生泡泡和星星粒子
        6. 掉到 FALL_TARGET_Y 時切換到彈回階段
        -------------------------------------------------------
        """
        dt = 1.0 / FPS
        self.fall_time += dt

        if self.bounce_phase == 0:
            # === 階段 0：自由墜落 ===
            self.velocity_y += GRAVITY               # 重力加速度
            self.bear_y += self.velocity_y            # 更新 y 位置

            # 左右搖擺（sin wave）
            swing = math.sin(self.fall_time * FALL_SWING_SPEED) * FALL_SWING_AMPLITUDE
            self.bear_x = self.fall_start_x + swing

            # 旋轉（搞笑轉圈）
            self.fall_rotation += 3.0

            # 產生墜落粒子（泡泡和星星）
            if random.random() < 0.3:
                spawn_bubbles(self.bear_x, self.bear_y + 15, 2)
            if random.random() < 0.15:
                spawn_stars(self.bear_x + random.randint(-20, 20),
                            self.bear_y + random.randint(-10, 10), 1)

            # 檢查是否到達墜落目標位置
            if self.bear_y >= FALL_TARGET_Y:
                self.bear_y = FALL_TARGET_Y
                self.bounce_phase = 1
                self.bounce_cloud_y = FALL_TARGET_Y + 20
                play_sound(snd_bounce)
                self.shake_timer = 8
                # 大量泡泡和星星！
                spawn_bubbles(self.bear_x, self.bear_y + 20, 12)
                spawn_stars(self.bear_x, self.bear_y, 15)

        elif self.bounce_phase == 1:
            # === 階段 1：雲朵接住 + 準備彈回 ===
            # 短暫停留在雲朵上（0.15 秒）
            self.fall_rotation *= 0.9  # 旋轉慢慢停下
            self.bear_expression = 'super_happy'

            if self.fall_time > 0.8:  # 給足夠時間到這個階段
                self.bounce_phase = 2
                self.velocity_y = BOUNCE_VELOCITY  # 往上彈！
                self.balloon_y = self.bear_y

        elif self.bounce_phase == 2:
            # === 階段 2：氣球帶著飛回去 ===
            self.velocity_y += GRAVITY * 0.3  # 上升時重力小一點（氣球浮力）
            self.bear_y += self.velocity_y
            self.fall_rotation *= 0.95

            # 慢慢回到 x 起始位置
            self.bear_x += (self.fall_start_x - self.bear_x) * 0.08

            # 彩帶特效
            if random.random() < 0.2:
                spawn_confetti(self.bear_x, self.bear_y + 20, 3)
            if random.random() < 0.15:
                spawn_stars(self.bear_x, self.bear_y - 10, 2)

            # 回到原位
            if self.bear_y <= self.fall_start_y:
                self.bear_y = self.fall_start_y
                self.bear_x = self.fall_start_x
                self.velocity_y = 0
                self.fall_rotation = 0
                self.bear_expression = 'super_happy'
                self.state = self.STATE_MESSAGE

                # 隨機選鼓勵語
                enc = random.choice(self.encouragements)
                self.message_text = enc
                self.message_sub_text = random.choice([
                    txt("氣球救你啦～飛上來！", "Balloon saved you~!"),
                    txt("雲朵接住你了！好棒！", "Cloud caught you! Great!"),
                    txt("魔法彈簧～咻～彈回來！", "Magic spring~ Boing~!"),
                ])
                self.message_timer = 100  # 顯示約 1.7 秒

                # 大量愛心和星星
                spawn_confetti(self.bear_x, self.bear_y, 20)
                spawn_stars(self.bear_x, self.bear_y - 20, 10)

        # 安全閥：超過最長墜落時間強制結束
        if self.fall_time > MAX_FALL_TIME + 1.0:
            self.bear_y = self.fall_start_y
            self.bear_x = self.fall_start_x
            self.velocity_y = 0
            self.state = self.STATE_MESSAGE
            self.message_text = txt("啵～彈回來了！", "Boing~ Back!")
            self.message_sub_text = txt("我們再試一次！加油！", "Let's try again!")
            self.message_timer = 80

    def update_advancing(self):
        """更新前進動畫"""
        if self.advance_timer > 0:
            # 平滑移動到目標位置
            self.bear_x += (self.bear_target_x - self.bear_x) * 0.15
            self.bear_y += (self.bear_target_y - self.bear_y) * 0.15
            self.advance_timer -= 1

            # 小跳躍效果
            jump_offset = math.sin(self.advance_timer * 0.3) * 8
            self.bear_y += jump_offset

        if self.advance_timer <= 0:
            self.bear_x = self.bear_target_x
            self.bear_y = self.bear_target_y
            self.current_step += 1

            # 檢查是否過關
            if self.current_step >= TOTAL_STEPS:
                self.state = self.STATE_VICTORY
                self.victory_timer = 0
                self.total_wins += 1
                play_sound(snd_victory)
                # 大煙火！
                for _ in range(5):
                    fx = random.randint(100, SCREEN_WIDTH - 100)
                    fy = random.randint(100, 300)
                    spawn_victory_fireworks(fx, fy, 25)
            else:
                self.state = self.STATE_PLAYING

    def update_message(self):
        """更新訊息顯示"""
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.message_timer <= 0:
            self.state = self.STATE_PLAYING

    def update_victory(self):
        """更新勝利動畫"""
        self.victory_timer += 1
        self.firework_timer += 1

        # 定期放煙火
        if self.firework_timer % 30 == 0:
            fx = random.randint(100, SCREEN_WIDTH - 100)
            fy = random.randint(80, 250)
            spawn_victory_fireworks(fx, fy, 20)
            spawn_confetti(fx, fy, 15)

        # 小動物跳舞
        self.bear_y = self.bear_target_y + math.sin(self.victory_timer * 0.1) * 15
        self.bear_expression = 'super_happy'

    def update_screen_shake(self):
        """更新螢幕抖動效果"""
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_offset_x = random.randint(-SCREEN_SHAKE_AMOUNT, SCREEN_SHAKE_AMOUNT)
            self.shake_offset_y = random.randint(-SCREEN_SHAKE_AMOUNT, SCREEN_SHAKE_AMOUNT)
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

    def update(self):
        """主更新函數（每幀呼叫）"""
        self.title_time += 1
        self.blink_timer += 1

        # 更新背景雲朵
        for cloud in self.bg_clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > SCREEN_WIDTH + 50:
                cloud['x'] = -50
                cloud['y'] = random.randint(30, 180)

        # 更新墊子動畫
        for pair in self.pads:
            pair['left'].update()
            pair['right'].update()

        # 更新粒子
        for p in particles:
            p.update()
        # 移除死亡粒子
        particles[:] = [p for p in particles if p.alive]

        # 螢幕抖動
        self.update_screen_shake()

        # 根據狀態更新
        if self.state == self.STATE_FALLING:
            self.update_falling()
        elif self.state == self.STATE_ADVANCING:
            self.update_advancing()
        elif self.state == self.STATE_MESSAGE:
            self.update_message()
        elif self.state == self.STATE_VICTORY:
            self.update_victory()

    def draw_background(self, surface):
        """繪製背景"""
        # 漸層天空
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(135 + (200 - 135) * ratio)
            g = int(206 + (230 - 206) * ratio)
            b = int(250 + (255 - 250) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 背景雲朵
        for cloud in self.bg_clouds:
            draw_cloud(surface, cloud['x'], cloud['y'], cloud['scale'], CLOUD_LIGHT)

        # 地面（草地）
        grass_y = SCREEN_HEIGHT - 60
        pygame.draw.rect(surface, (120, 200, 80), (0, grass_y, SCREEN_WIDTH, 60))
        pygame.draw.rect(surface, (100, 180, 60), (0, grass_y, SCREEN_WIDTH, 5))

        # 小花朵裝飾
        for i in range(15):
            fx = (i * 57 + 20) % SCREEN_WIDTH
            fy = grass_y + 15 + (i * 13) % 30
            color = random.choice(RAINBOW_COLORS) if self.title_time % 120 < 2 else \
                RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
            pygame.draw.circle(surface, color, (fx, fy), 4)
            pygame.draw.circle(surface, GOLD, (fx, fy), 2)

    def draw_bridge(self, surface):
        """繪製橋和墊子"""
        # 橋的框架（兩條繩子）
        rope_y_top = 265
        rope_y_bottom = 355
        pygame.draw.line(surface, (180, 140, 100), (60, rope_y_top), (SCREEN_WIDTH - 60, rope_y_top), 3)
        pygame.draw.line(surface, (180, 140, 100), (60, rope_y_bottom), (SCREEN_WIDTH - 60, rope_y_bottom), 3)

        # 起點標誌
        start_text = font_small.render(txt("起點", "START"), True, ORANGE)
        surface.blit(start_text, (10, 240))

        # 終點標誌（彩虹 + 蛋糕）
        end_x = SCREEN_WIDTH - 45
        draw_rainbow(surface, end_x, 230, 40)

        # 大星星（終點）
        star_pulse = math.sin(self.title_time * 0.05) * 5
        draw_star(surface, end_x, 200, int(20 + star_pulse), GOLD)

        goal_text = font_small.render(txt("終點!", "GOAL!"), True, RED)
        surface.blit(goal_text, (end_x - 20, 250))

        # 繪製墊子
        for i, pair in enumerate(self.pads):
            # 高亮目前可以選擇的墊子
            is_current = (i == self.current_step and self.state == self.STATE_PLAYING)
            pair['left'].draw(surface, highlight=is_current)
            pair['right'].draw(surface, highlight=is_current)

            # 在墊子對之間畫標號
            lp = pair['left']
            rp = pair['right']
            mid_y = (lp.y + rp.y) // 2
            num_text = font_tiny.render(str(i + 1), True, (150, 150, 180))
            num_rect = num_text.get_rect(center=(lp.x, mid_y))
            surface.blit(num_text, num_rect)

    def draw_bear_character(self, surface):
        """繪製小熊角色"""
        if self.state == self.STATE_TITLE:
            # 標題畫面的小熊（眨眼動畫）
            blink = (self.blink_timer % 120) < 8
            expr = 'super_happy' if blink else 'happy'
            # 小跳動
            jump = math.sin(self.title_time * 0.08) * 5
            draw_bear(surface, 400, 320 + jump, 35, expr)
        else:
            draw_bear(surface, self.bear_x, self.bear_y, 30,
                      self.bear_expression, self.fall_rotation)

    def draw_falling_effects(self, surface):
        """繪製墜落時的特效"""
        if self.state != self.STATE_FALLING:
            return

        if self.bounce_phase == 1:
            # 雲朵接住動畫
            draw_cloud(surface, self.bear_x, self.bounce_cloud_y, 1.5, CLOUD_WHITE)
            # 文字
            catch_text = font_small.render(
                txt("雲朵接住你了！", "Cloud caught you!"), True, WHITE)
            catch_rect = catch_text.get_rect(center=(self.bear_x, self.bounce_cloud_y + 40))
            surface.blit(catch_text, catch_rect)

        elif self.bounce_phase == 2:
            # 氣球帶著飛回去
            balloon_colors = [BALLOON_RED, BALLOON_BLUE, BALLOON_YELLOW, BALLOON_GREEN]
            for i, bc in enumerate(balloon_colors):
                bx = self.bear_x + (i - 1.5) * 18
                by = self.bear_y - 45
                draw_balloon(surface, bx, by, bc, 14)

            # 飛上來的文字
            fly_text = font_tiny.render(
                txt("氣球救你啦～飛上來！", "Balloon rescue~ Flying up!"), True, GOLD)
            fly_rect = fly_text.get_rect(center=(self.bear_x, self.bear_y - 70))
            surface.blit(fly_text, fly_rect)

        # 墜落時的搞笑對話泡泡
        if self.bounce_phase == 0 and self.fall_time > 0.2:
            bubble_texts = [
                txt("哇～～～", "Wheeee~"),
                txt("飛起來了！", "Flying~!"),
                txt("好好玩！", "So fun!"),
            ]
            bt = bubble_texts[int(self.fall_time * 2) % len(bubble_texts)]
            bubble_text = font_tiny.render(bt, True, BLACK)
            bx = self.bear_x + 40
            by = self.bear_y - 30

            # 對話泡泡背景
            br = bubble_text.get_rect(center=(bx, by))
            bubble_bg = br.inflate(16, 10)
            pygame.draw.ellipse(surface, WHITE, bubble_bg)
            pygame.draw.ellipse(surface, BLACK, bubble_bg, 2)
            surface.blit(bubble_text, br)

    def draw_message(self, surface):
        """繪製鼓勵訊息"""
        if self.state != self.STATE_MESSAGE or self.message_timer <= 0:
            return

        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))
        surface.blit(overlay, (0, 200))

        # 主要鼓勵文字
        msg_surface = font_medium.render(self.message_text, True, (80, 50, 150))
        msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 240))
        surface.blit(msg_surface, msg_rect)

        # 副文字
        if self.message_sub_text:
            sub_surface = font_small.render(self.message_sub_text, True, (200, 100, 150))
            sub_rect = sub_surface.get_rect(center=(SCREEN_WIDTH // 2, 280))
            surface.blit(sub_surface, sub_rect)

        # 愛心裝飾
        heart_text = font_medium.render("♥ ♥ ♥", True, RED)
        heart_rect = heart_text.get_rect(center=(SCREEN_WIDTH // 2, 305))
        surface.blit(heart_text, heart_rect)

    def draw_hud(self, surface):
        """繪製遊戲資訊（HUD）"""
        if self.state in [self.STATE_TITLE]:
            return

        # 進度
        progress_text = font_tiny.render(
            txt(f"第 {self.current_step}/{TOTAL_STEPS} 格", f"Step {self.current_step}/{TOTAL_STEPS}"),
            True, (80, 80, 120))
        surface.blit(progress_text, (10, 10))

        # 過橋次數
        wins_text = font_tiny.render(
            txt(f"已過 {self.total_wins} 次橋！", f"Bridges: {self.total_wins}"),
            True, GOLD)
        surface.blit(wins_text, (10, 35))

        # 操作提示
        if self.state == self.STATE_PLAYING:
            hint_text = font_tiny.render(
                txt("點左邊=選上面墊子  點右邊=選下面墊子", "Click LEFT=top pad  RIGHT=bottom pad"),
                True, (120, 120, 160))
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
            surface.blit(hint_text, hint_rect)

            # 左右方向鍵提示
            key_hint = font_tiny.render(
                txt("(或按 ← → 方向鍵)", "(or use arrow keys)"),
                True, (150, 150, 180))
            key_rect = key_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 5))
            surface.blit(key_hint, key_rect)

    def draw_title_screen(self, surface):
        """繪製標題畫面"""
        # 標題文字（彩色波浪效果）
        title_str = txt("魔法跳跳橋", "Magic Bouncy Bridge")
        title_surface = font_large.render(title_str, True, PURPLE)
        # 陰影
        title_shadow = font_large.render(title_str, True, (100, 80, 150))
        surface.blit(title_shadow,
                     title_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 102)))
        surface.blit(title_surface,
                     title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        # 副標題
        sub_str = txt("兒童版踩墊子大冒險！", "Kid's Pad Adventure!")
        sub_surface = font_medium.render(sub_str, True, ORANGE)
        surface.blit(sub_surface,
                     sub_surface.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        # 裝飾星星
        for i in range(8):
            angle = self.title_time * 0.02 + i * math.pi / 4
            sx = SCREEN_WIDTH // 2 + math.cos(angle) * 200
            sy = 120 + math.sin(angle) * 50
            star_size = 8 + math.sin(self.title_time * 0.05 + i) * 3
            draw_star(surface, sx, sy, int(star_size),
                      RAINBOW_COLORS[i % len(RAINBOW_COLORS)])

        # 操作說明
        y_offset = 400
        instructions = [
            txt("點畫面左半邊 → 選上面墊子", "Click LEFT side -> Top pad"),
            txt("點畫面右半邊 → 選下面墊子", "Click RIGHT side -> Bottom pad"),
            txt("(方向鍵 ← → 也可以喔！)", "(Arrow keys work too!)"),
        ]
        for i, inst in enumerate(instructions):
            inst_surface = font_small.render(inst, True, (100, 100, 140))
            inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset + i * 30))
            surface.blit(inst_surface, inst_rect)

        # 開始提示（閃爍）
        if (self.title_time // 30) % 2 == 0:
            start_str = txt("按空白鍵開始遊戲！", "Press SPACE to start!")
            start_surface = font_medium.render(start_str, True, RED)
            start_rect = start_surface.get_rect(center=(SCREEN_WIDTH // 2, 520))
            surface.blit(start_surface, start_rect)

        # 彩虹裝飾
        draw_rainbow(surface, 100, 200, 35)
        draw_rainbow(surface, SCREEN_WIDTH - 100, 200, 35)

    def draw_victory_screen(self, surface):
        """繪製勝利畫面"""
        # 大彩虹
        draw_rainbow(surface, SCREEN_WIDTH // 2, 120, 80)

        # 勝利文字
        pulse = math.sin(self.victory_timer * 0.08) * 5
        win_str = txt("哇！你過魔法橋啦！", "Wow! You crossed the bridge!")
        win_surface = font_large.render(win_str, True, GOLD)
        win_rect = win_surface.get_rect(center=(SCREEN_WIDTH // 2, 80 + pulse))
        # 文字陰影
        shadow = font_large.render(win_str, True, ORANGE)
        surface.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 82 + pulse)))
        surface.blit(win_surface, win_rect)

        # 副文字
        brave_str = txt("超勇敢！耶～ 你是最棒的！", "So brave! Yay~ You're the best!")
        brave_surface = font_medium.render(brave_str, True, PURPLE)
        surface.blit(brave_surface,
                     brave_surface.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        # 計分
        score_str = txt(f"你已經過了 {self.total_wins} 次橋！最棒寶貝！",
                        f"Bridges crossed: {self.total_wins}! Best kid ever!")
        score_surface = font_small.render(score_str, True, (100, 80, 150))
        surface.blit(score_surface,
                     score_surface.get_rect(center=(SCREEN_WIDTH // 2, 185)))

        # 再玩一次提示
        if self.victory_timer > 60:
            again_str = txt("按 R 再玩一次！", "Press R to play again!")
            again_surface = font_medium.render(again_str, True, SAFE_GREEN)
            surface.blit(again_surface,
                         again_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))

            thanks_str = txt("謝謝玩遊戲！你是最可愛的小冒險家！",
                             "Thanks for playing! You're the cutest adventurer!")
            thanks_surface = font_small.render(thanks_str, True, (180, 130, 200))
            surface.blit(thanks_surface,
                         thanks_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 45)))

        # 大星星裝飾
        for i in range(12):
            angle = self.victory_timer * 0.03 + i * math.pi / 6
            sx = SCREEN_WIDTH // 2 + math.cos(angle) * (150 + i * 15)
            sy = 130 + math.sin(angle) * 60
            star_size = 10 + math.sin(self.victory_timer * 0.06 + i) * 4
            draw_star(surface, sx, sy, int(star_size),
                      RAINBOW_COLORS[i % len(RAINBOW_COLORS)])

    def draw(self):
        """主繪製函數"""
        # 建立繪製用 surface（用於螢幕抖動）
        draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # 背景
        self.draw_background(draw_surface)

        if self.state == self.STATE_TITLE:
            self.draw_title_screen(draw_surface)
            self.draw_bear_character(draw_surface)
        else:
            # 繪製橋和墊子
            self.draw_bridge(draw_surface)

            # 繪製粒子（在角色下方）
            for p in particles:
                p.draw(draw_surface)

            # 繪製墜落特效（雲朵、氣球等）
            self.draw_falling_effects(draw_surface)

            # 繪製小熊
            self.draw_bear_character(draw_surface)

            # 繪製訊息
            self.draw_message(draw_surface)

            # 繪製 HUD
            self.draw_hud(draw_surface)

            # 勝利畫面
            if self.state == self.STATE_VICTORY:
                self.draw_victory_screen(draw_surface)

        # 套用螢幕抖動並繪製到實際螢幕
        screen.blit(draw_surface, (self.shake_offset_x, self.shake_offset_y))

    def handle_event(self, event):
        """處理輸入事件"""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if self.state == self.STATE_TITLE:
                if event.key == pygame.K_SPACE:
                    self.reset_game()
            elif self.state == self.STATE_PLAYING:
                if event.key == pygame.K_LEFT:
                    self.handle_choice(True)   # 左 = 上面墊子
                elif event.key == pygame.K_RIGHT:
                    self.handle_choice(False)  # 右 = 下面墊子
            elif self.state == self.STATE_VICTORY:
                if event.key == pygame.K_r:
                    self.reset_game()

            # 任何狀態下按 R 都可以重來
            if event.key == pygame.K_r and self.state not in [self.STATE_TITLE]:
                self.reset_game()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == self.STATE_TITLE:
                self.reset_game()
            elif self.state == self.STATE_PLAYING:
                mx, my = event.pos
                if mx < SCREEN_WIDTH // 2:
                    self.handle_choice(True)   # 點左半邊 = 上面墊子
                else:
                    self.handle_choice(False)  # 點右半邊 = 下面墊子
            elif self.state == self.STATE_VICTORY:
                if self.victory_timer > 60:
                    self.reset_game()

        return True


# ============================================================
# 主程式入口
# ============================================================
def main():
    """遊戲主迴圈"""
    game = Game()
    running = True

    while running:
        # 處理事件
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False

        # 更新遊戲邏輯
        game.update()

        # 繪製畫面
        game.draw()

        # 更新顯示
        pygame.display.flip()

        # 控制幀率
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
