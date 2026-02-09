#!/usr/bin/env python3
"""
🌈 魔法跳跳橋 - 兒童版踩玻璃遊戲 🌈
Magic Bouncy Bridge - A Kid-Friendly Glass Bridge Game

適合 5 歲小朋友玩的超可愛跳跳橋遊戲！
靈感來自魷魚遊戲的玻璃橋，但完全沒有任何可怕元素，
只有可愛的小恐龍、搞笑的墜落動畫、和滿滿的正向鼓勵！

安裝：pip install pygame
執行：python magic_bridge_game.py

操作方式：
  - 滑鼠點擊畫面左半邊 = 選左邊墊子
  - 滑鼠點擊畫面右半邊 = 選右邊墊子
  - 也可以用鍵盤左右方向鍵
  - 空格鍵開始遊戲
  - R 鍵重新開始

墜落動畫說明：
  - 使用重力模擬：velocity += GRAVITY 每幀，y += velocity
  - 左右晃動用 sin(time) 產生 x 偏移
  - 掉到畫面 70% 高度後觸發彈回（velocity 反轉）
  - 彈回時有氣球接住動畫 + 粒子效果
  - 整個過程約 1.5 秒，不會讓小孩害怕
"""

import pygame
import sys
import math
import random
import os

# ============================================================
# 初始化 Pygame
# ============================================================
pygame.init()

# 嘗試初始化音效（如果環境不支援也不會崩潰）
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    SOUND_ENABLED = True
except Exception:
    SOUND_ENABLED = False

# ============================================================
# 遊戲常數設定（方便調整）
# ============================================================
SCREEN_WIDTH = 800       # 畫面寬度
SCREEN_HEIGHT = 600      # 畫面高度
FPS = 60                 # 每秒幀數

# 墜落動畫參數（可自由調整！）
GRAVITY = 0.35           # 重力加速度（越大掉越快）
FALL_MAX_Y = SCREEN_HEIGHT * 0.70   # 墜落到畫面 70% 高度觸發彈回
BOUNCE_VELOCITY = -8.0   # 彈回初始速度（負值 = 往上）
SWING_AMPLITUDE = 30     # 墜落時左右晃動幅度（像素）
SWING_SPEED = 8          # 左右晃動速度

# 墊子設定
NUM_STEPS = 12           # 總共幾格墊子（10~14 格）
BOUNCE_CHANCE = 0.25     # 彈跳墊子的機率（20~30%）

# 顏色定義 🎨
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 250)
LIGHT_BLUE = (173, 216, 240)
GRASS_GREEN = (124, 205, 124)
SAFE_GREEN = (100, 210, 130)
SAFE_BLUE = (100, 180, 240)
BOUNCE_PINK = (255, 150, 180)
BOUNCE_YELLOW = (255, 230, 100)
CLOUD_WHITE = (245, 245, 255)
ORANGE = (255, 180, 80)
RED_SOFT = (255, 120, 120)
GOLD = (255, 215, 0)
PURPLE = (180, 130, 255)
RAINBOW_COLORS = [
    (255, 100, 100), (255, 180, 80), (255, 255, 100),
    (100, 220, 100), (100, 180, 255), (150, 100, 255),
    (255, 150, 220),
]
DINO_GREEN = (80, 180, 80)
DINO_BELLY = (200, 240, 180)
BALLOON_RED = (255, 100, 100)
BALLOON_BLUE = (100, 150, 255)
BALLOON_YELLOW = (255, 240, 100)
BALLOON_PINK = (255, 160, 200)
HEART_PINK = (255, 130, 170)

# ============================================================
# 畫面初始化
# ============================================================
# 嘗試用硬體加速，如果失敗就用軟體渲染
try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
except Exception:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🌈 魔法跳跳橋 - Magic Bouncy Bridge 🌈")
clock = pygame.time.Clock()

# ============================================================
# 字體設定（嘗試載入支援中文的字體）
# ============================================================
def get_font(size):
    """嘗試取得支援中文的字體"""
    # 嘗試常見的中文字體路徑
    chinese_font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in chinese_font_paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    # 如果找不到中文字體，用預設字體（中文可能顯示為方框）
    return pygame.font.Font(None, size)

font_large = get_font(42)
font_medium = get_font(28)
font_small = get_font(22)
font_tiny = get_font(18)
font_huge = get_font(56)

# ============================================================
# 音效生成（用程式碼生成簡單音效，不需要外部檔案）
# ============================================================
def generate_sound(frequency, duration_ms, volume=0.3, wave_type='sine'):
    """用程式碼生成簡單的音效"""
    if not SOUND_ENABLED:
        return None
    try:
        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000.0)
        buf = bytearray(n_samples * 2)  # 16-bit mono
        max_val = 32767
        for i in range(n_samples):
            t = i / sample_rate
            # 音量淡出
            envelope = max(0, 1.0 - (i / n_samples) * 0.8)
            if wave_type == 'sine':
                val = math.sin(2 * math.pi * frequency * t) * volume * envelope
            elif wave_type == 'bounce':
                # 彈跳音：頻率上升
                f = frequency + (i / n_samples) * 400
                val = math.sin(2 * math.pi * f * t) * volume * envelope
            elif wave_type == 'fall':
                # 墜落音：頻率下降
                f = frequency - (i / n_samples) * 300
                val = math.sin(2 * math.pi * max(100, f) * t) * volume * envelope
            elif wave_type == 'victory':
                # 勝利音：和弦
                val = (math.sin(2 * math.pi * frequency * t) +
                       math.sin(2 * math.pi * frequency * 1.25 * t) +
                       math.sin(2 * math.pi * frequency * 1.5 * t)) / 3 * volume * envelope
            else:
                val = math.sin(2 * math.pi * frequency * t) * volume * envelope

            sample = int(val * max_val)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF

        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    except Exception:
        return None

# 生成各種音效
snd_jump = generate_sound(600, 150, 0.2, 'bounce')      # 跳躍「叮～」
snd_fall = generate_sound(500, 400, 0.15, 'fall')        # 墜落「呼～」
snd_bounce = generate_sound(400, 300, 0.25, 'bounce')    # 彈回「啵～」
snd_victory = generate_sound(523, 800, 0.2, 'victory')   # 勝利「啦啦啦～」
snd_click = generate_sound(800, 80, 0.15, 'sine')        # 點擊「嗶」

def play_sound(sound):
    """安全地播放音效"""
    if sound and SOUND_ENABLED:
        try:
            sound.play()
        except Exception:
            pass

# ============================================================
# 粒子系統 ✨（星星、泡泡、彩帶、愛心）
# ============================================================
class Particle:
    """一個粒子（星星/泡泡/彩帶/愛心）"""
    def __init__(self, x, y, ptype='star'):
        self.x = x
        self.y = y
        self.ptype = ptype
        self.age = 0
        self.max_age = random.randint(30, 70)
        self.color = random.choice(RAINBOW_COLORS)
        self.size = random.randint(3, 8)

        if ptype == 'star':
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-3, -0.5)
        elif ptype == 'bubble':
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-2, -0.3)
            self.size = random.randint(4, 12)
            self.color = random.choice([LIGHT_BLUE, CLOUD_WHITE, BOUNCE_PINK, BALLOON_YELLOW])
        elif ptype == 'confetti':
            self.vx = random.uniform(-4, 4)
            self.vy = random.uniform(-5, -1)
            self.size = random.randint(3, 7)
            self.rotation = random.uniform(0, 360)
            self.rot_speed = random.uniform(-10, 10)
        elif ptype == 'heart':
            self.vx = random.uniform(-1.5, 1.5)
            self.vy = random.uniform(-2.5, -0.5)
            self.size = random.randint(5, 10)
            self.color = random.choice([HEART_PINK, RED_SOFT, BOUNCE_PINK])
        elif ptype == 'firework':
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.size = random.randint(2, 5)
            self.max_age = random.randint(20, 50)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1
        if self.ptype in ('star', 'confetti', 'firework', 'heart'):
            self.vy += 0.05  # 輕微重力
        if self.ptype == 'confetti':
            self.rotation += self.rot_speed
        return self.age < self.max_age

    def draw(self, surface, offset_x=0, offset_y=0):
        alpha = max(0, 1 - self.age / self.max_age)
        x = int(self.x + offset_x)
        y = int(self.y + offset_y)
        size = max(1, int(self.size * alpha))

        if self.ptype == 'star':
            draw_star(surface, x, y, size, self.color)
        elif self.ptype == 'bubble':
            pygame.draw.circle(surface, self.color, (x, y), size, 1)
            # 泡泡亮點
            pygame.draw.circle(surface, WHITE, (x - size // 3, y - size // 3), max(1, size // 4))
        elif self.ptype == 'confetti':
            s = pygame.Surface((size * 2, size), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.color, int(255 * alpha)), (0, 0, size * 2, size))
            rotated = pygame.transform.rotate(s, self.rotation)
            surface.blit(rotated, (x - rotated.get_width() // 2, y - rotated.get_height() // 2))
        elif self.ptype == 'heart':
            draw_heart(surface, x, y, size, self.color)
        elif self.ptype == 'firework':
            pygame.draw.circle(surface, self.color, (x, y), size)


def draw_star(surface, x, y, size, color):
    """畫一個可愛的五角星 ⭐"""
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.4
        px = x + int(math.cos(angle) * r)
        py = y - int(math.sin(angle) * r)
        points.append((px, py))
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, points)


def draw_heart(surface, x, y, size, color):
    """畫一個可愛的愛心 ❤️"""
    s = max(2, size)
    pygame.draw.circle(surface, color, (x - s // 3, y - s // 4), s // 2)
    pygame.draw.circle(surface, color, (x + s // 3, y - s // 4), s // 2)
    points = [(x - s, y), (x, y + s), (x + s, y)]
    pygame.draw.polygon(surface, color, points)


# 全域粒子列表
particles = []

def spawn_particles(x, y, ptype='star', count=10):
    """在指定位置產生粒子"""
    for _ in range(count):
        particles.append(Particle(x, y, ptype))


# ============================================================
# 雲朵繪製 ☁️
# ============================================================
def draw_cloud(surface, x, y, size=40, color=CLOUD_WHITE):
    """畫一朵蓬鬆的雲"""
    pygame.draw.ellipse(surface, color, (x, y, size * 2, size))
    pygame.draw.ellipse(surface, color, (x + size * 0.3, y - size * 0.4, size * 1.4, size))
    pygame.draw.ellipse(surface, color, (x - size * 0.3, y - size * 0.1, size, size * 0.8))
    pygame.draw.ellipse(surface, color, (x + size * 1.1, y - size * 0.1, size, size * 0.8))


# ============================================================
# 氣球繪製 🎈
# ============================================================
def draw_balloon(surface, x, y, color, size=20):
    """畫一個氣球"""
    # 氣球本體
    pygame.draw.ellipse(surface, color, (x - size, y - size * 1.3, size * 2, size * 2.6))
    # 亮點
    pygame.draw.ellipse(surface, WHITE, (x - size * 0.4, y - size * 0.8, size * 0.5, size * 0.8))
    # 繩子
    pygame.draw.line(surface, BLACK, (x, y + size * 1.3), (x + 3, y + size * 2), 2)
    # 氣球底部三角
    points = [(x - 4, y + size * 1.3), (x + 4, y + size * 1.3), (x, y + size * 1.5)]
    pygame.draw.polygon(surface, color, points)


# ============================================================
# 彩虹繪製 🌈
# ============================================================
def draw_rainbow(surface, x, y, radius=80):
    """畫一個彩虹"""
    rainbow = [(255, 0, 0), (255, 127, 0), (255, 255, 0),
               (0, 200, 0), (0, 150, 255), (75, 0, 130), (148, 0, 211)]
    for i, color in enumerate(rainbow):
        r = radius - i * 6
        if r > 0:
            rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
            pygame.draw.arc(surface, color, rect, 0, math.pi, 4)


# ============================================================
# 蛋糕繪製 🎂
# ============================================================
def draw_cake(surface, x, y, size=40):
    """畫一個可愛的蛋糕"""
    # 蛋糕底層
    pygame.draw.rect(surface, ORANGE, (x - size, y, size * 2, size))
    pygame.draw.rect(surface, BOUNCE_PINK, (x - size, y, size * 2, size // 3))
    # 蛋糕頂層
    pygame.draw.rect(surface, BOUNCE_YELLOW, (x - size * 0.7, y - size * 0.6, size * 1.4, size * 0.6))
    pygame.draw.rect(surface, BOUNCE_PINK, (x - size * 0.7, y - size * 0.6, size * 1.4, size * 0.2))
    # 蠟燭
    pygame.draw.rect(surface, RED_SOFT, (x - 3, y - size * 0.6 - 15, 6, 15))
    # 火焰
    pygame.draw.ellipse(surface, GOLD, (x - 4, y - size * 0.6 - 22, 8, 10))
    pygame.draw.ellipse(surface, BOUNCE_YELLOW, (x - 2, y - size * 0.6 - 20, 4, 6))
    # 奶油裝飾
    for i in range(5):
        cx = x - size + i * (size * 2 // 4)
        pygame.draw.circle(surface, WHITE, (cx, y), 6)


# ============================================================
# 小恐龍角色 🦕
# ============================================================
class Dino:
    """超可愛的小恐龍角色"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_y = y          # 基準 y 位置（站在墊子上的高度）
        self.velocity_y = 0      # y 方向速度
        self.state = 'idle'      # 狀態：idle / jumping / falling / bouncing / celebrating
        self.frame = 0           # 動畫幀計數器
        self.rotation = 0        # 旋轉角度（墜落時轉圈）
        self.fall_time = 0       # 墜落時間計數
        self.blink_timer = 0     # 眨眼計時器
        self.is_blinking = False
        self.jump_target_x = 0   # 跳躍目標 x
        self.jump_progress = 0   # 跳躍進度 0~1
        self.jump_start_x = 0    # 跳躍起點 x
        self.bounce_phase = 0    # 彈回階段：0=墜落中, 1=被接住, 2=彈回中, 3=完成
        self.size = 30           # 角色大小

    def start_jump(self, target_x):
        """開始跳躍到下一格"""
        self.state = 'jumping'
        self.jump_start_x = self.x
        self.jump_target_x = target_x
        self.jump_progress = 0
        play_sound(snd_jump)

    def start_fall(self):
        """
        開始墜落動畫！
        
        墜落邏輯說明：
        1. 設定狀態為 'falling'，velocity_y = 0
        2. 每幀 velocity_y += GRAVITY（模擬重力加速度）
        3. y += velocity_y（位置更新）
        4. 同時用 sin(fall_time * SWING_SPEED) * SWING_AMPLITUDE 做左右晃動
        5. 當 y > FALL_MAX_Y 時，觸發彈回：
           - 先顯示氣球接住動畫
           - 然後 velocity_y = BOUNCE_VELOCITY（往上彈）
        6. 當彈回到 base_y 附近時，結束動畫
        """
        self.state = 'falling'
        self.velocity_y = 0
        self.fall_time = 0
        self.rotation = 0
        self.bounce_phase = 0
        play_sound(snd_fall)

    def update(self):
        """每幀更新小恐龍狀態"""
        self.frame += 1

        # 眨眼
        self.blink_timer += 1
        if self.blink_timer > random.randint(120, 240):
            self.is_blinking = True
            self.blink_timer = 0
        if self.is_blinking and self.blink_timer > 8:
            self.is_blinking = False
            self.blink_timer = 0

        if self.state == 'jumping':
            # 跳躍動畫：拋物線
            self.jump_progress += 0.04
            if self.jump_progress >= 1.0:
                self.jump_progress = 1.0
                self.x = self.jump_target_x
                self.y = self.base_y
                self.state = 'idle'
                spawn_particles(self.x, self.y, 'star', 8)
            else:
                t = self.jump_progress
                self.x = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * t
                # 拋物線高度
                jump_height = -80 * math.sin(t * math.pi)
                self.y = self.base_y + jump_height

        elif self.state == 'falling':
            self.fall_time += 1

            if self.bounce_phase == 0:
                # 階段 0：自由墜落 + 左右晃動
                # 重力加速度：每幀速度增加 GRAVITY
                self.velocity_y += GRAVITY
                self.y += self.velocity_y

                # 左右搖擺（sin wave）讓墜落更有空中搖擺的感覺
                swing = math.sin(self.fall_time * SWING_SPEED * 0.1) * SWING_AMPLITUDE
                self.x = self.jump_target_x + swing

                # 旋轉（搞笑轉圈圈）
                self.rotation += 5

                # 墜落時灑星星和泡泡
                if self.frame % 4 == 0:
                    spawn_particles(self.x, self.y, 'star', 2)
                    spawn_particles(self.x, self.y, 'bubble', 1)

                # 到達墜落最低點 → 觸發氣球接住
                if self.y >= FALL_MAX_Y:
                    self.y = FALL_MAX_Y
                    self.bounce_phase = 1
                    self.velocity_y = 0
                    self.fall_time = 0
                    play_sound(snd_bounce)
                    spawn_particles(self.x, self.y, 'star', 15)
                    spawn_particles(self.x, self.y, 'bubble', 10)

            elif self.bounce_phase == 1:
                # 階段 1：被氣球接住，短暫停留
                self.rotation *= 0.9  # 慢慢停止轉圈
                self.fall_time += 1
                if self.fall_time > 20:  # 停留約 0.3 秒
                    self.bounce_phase = 2
                    self.velocity_y = BOUNCE_VELOCITY  # 往上彈！

            elif self.bounce_phase == 2:
                # 階段 2：彈回！往上飛！
                self.velocity_y += GRAVITY * 0.5  # 比較輕的重力
                self.y += self.velocity_y
                self.rotation *= 0.95

                # 彈回時灑更多彩帶！
                if self.frame % 3 == 0:
                    spawn_particles(self.x, self.y, 'confetti', 2)
                    spawn_particles(self.x, self.y, 'heart', 1)

                # 左右晃動慢慢減弱
                swing = math.sin(self.fall_time * 0.3) * SWING_AMPLITUDE * 0.3
                self.x = self.jump_target_x + swing

                # 回到原本高度 → 完成彈回
                if self.y <= self.base_y:
                    self.y = self.base_y
                    self.x = self.jump_target_x
                    self.rotation = 0
                    self.bounce_phase = 3
                    self.state = 'idle'
                    spawn_particles(self.x, self.y, 'heart', 8)
                    spawn_particles(self.x, self.y, 'star', 8)

        elif self.state == 'celebrating':
            # 慶祝動畫：上下跳動
            bounce = math.sin(self.frame * 0.15) * 10
            self.y = self.base_y + bounce
            if self.frame % 15 == 0:
                spawn_particles(self.x, self.y - 20, 'star', 3)
                spawn_particles(self.x, self.y - 20, 'confetti', 3)

    def draw(self, surface, shake_x=0, shake_y=0):
        """畫小恐龍"""
        # 根據旋轉創建旋轉的繪圖表面
        dino_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
        cx, cy = 40, 40  # 繪圖中心

        if self.state == 'falling' and self.bounce_phase == 0:
            # 墜落表情：驚訝大眼 + 張嘴
            self._draw_dino_body(dino_surface, cx, cy, expression='surprised')
        elif self.state == 'falling' and self.bounce_phase >= 1:
            # 彈回表情：開心
            self._draw_dino_body(dino_surface, cx, cy, expression='happy')
        elif self.state == 'celebrating':
            self._draw_dino_body(dino_surface, cx, cy, expression='celebrating')
        else:
            expr = 'blink' if self.is_blinking else 'normal'
            self._draw_dino_body(dino_surface, cx, cy, expression=expr)

        # 旋轉
        if abs(self.rotation) > 0.5:
            dino_surface = pygame.transform.rotate(dino_surface, -self.rotation)

        # 畫到主畫面
        rect = dino_surface.get_rect(center=(int(self.x + shake_x), int(self.y - 20 + shake_y)))
        surface.blit(dino_surface, rect)

    def _draw_dino_body(self, surface, cx, cy, expression='normal'):
        """畫小恐龍的身體和表情"""
        s = self.size

        # 身體（圓圓的）
        pygame.draw.ellipse(surface, DINO_GREEN, (cx - s, cy - s * 0.5, s * 2, s * 1.8))
        # 肚子
        pygame.draw.ellipse(surface, DINO_BELLY, (cx - s * 0.6, cy, s * 1.2, s * 1.1))

        # 頭
        pygame.draw.circle(surface, DINO_GREEN, (cx, cy - s * 0.5), int(s * 0.8))

        # 頭上的小角（三角形）
        for offset in [-6, 0, 6]:
            points = [
                (cx + offset - 4, cy - s * 0.5 - int(s * 0.6)),
                (cx + offset + 4, cy - s * 0.5 - int(s * 0.6)),
                (cx + offset, cy - s * 0.5 - int(s * 1.0))
            ]
            pygame.draw.polygon(surface, SAFE_GREEN, points)

        # 表情
        if expression == 'surprised':
            # 驚訝大眼 + 張嘴 O
            pygame.draw.circle(surface, WHITE, (cx - 8, cy - s * 0.6), 8)
            pygame.draw.circle(surface, WHITE, (cx + 8, cy - s * 0.6), 8)
            pygame.draw.circle(surface, BLACK, (cx - 8, cy - s * 0.6), 5)
            pygame.draw.circle(surface, BLACK, (cx + 8, cy - s * 0.6), 5)
            # 星星眼
            draw_star(surface, cx - 8, cy - s * 0.6, 3, GOLD)
            draw_star(surface, cx + 8, cy - s * 0.6, 3, GOLD)
            # 張嘴
            pygame.draw.ellipse(surface, RED_SOFT, (cx - 6, cy - s * 0.3, 12, 10))
            # 揮手
            arm_wave = math.sin(self.frame * 0.3) * 15
            pygame.draw.line(surface, DINO_GREEN,
                             (cx - s, cy + 5), (cx - s - 12, cy - 5 + int(arm_wave)), 4)
            pygame.draw.line(surface, DINO_GREEN,
                             (cx + s, cy + 5), (cx + s + 12, cy - 5 - int(arm_wave)), 4)

        elif expression == 'happy':
            # 超開心笑臉
            pygame.draw.circle(surface, WHITE, (cx - 8, cy - s * 0.6), 6)
            pygame.draw.circle(surface, WHITE, (cx + 8, cy - s * 0.6), 6)
            pygame.draw.circle(surface, BLACK, (cx - 8, cy - s * 0.6), 3)
            pygame.draw.circle(surface, BLACK, (cx + 8, cy - s * 0.6), 3)
            # 開心嘴巴（弧線）
            pygame.draw.arc(surface, RED_SOFT,
                            (cx - 8, cy - s * 0.4, 16, 10), math.pi, 2 * math.pi, 2)
            # 腮紅
            pygame.draw.circle(surface, BOUNCE_PINK, (cx - 14, cy - s * 0.35), 4)
            pygame.draw.circle(surface, BOUNCE_PINK, (cx + 14, cy - s * 0.35), 4)

        elif expression == 'celebrating':
            # 慶祝：閉眼笑 + 舉手
            # 開心閉眼
            pygame.draw.arc(surface, BLACK,
                            (cx - 12, cy - s * 0.8, 10, 8), 0, math.pi, 2)
            pygame.draw.arc(surface, BLACK,
                            (cx + 2, cy - s * 0.8, 10, 8), 0, math.pi, 2)
            # 大笑嘴巴
            pygame.draw.arc(surface, RED_SOFT,
                            (cx - 10, cy - s * 0.4, 20, 14), math.pi, 2 * math.pi, 3)
            # 腮紅
            pygame.draw.circle(surface, BOUNCE_PINK, (cx - 14, cy - s * 0.35), 5)
            pygame.draw.circle(surface, BOUNCE_PINK, (cx + 14, cy - s * 0.35), 5)
            # 舉手歡呼
            wave = math.sin(self.frame * 0.2) * 10
            pygame.draw.line(surface, DINO_GREEN,
                             (cx - s, cy + 5), (cx - s - 15, cy - 20 + int(wave)), 4)
            pygame.draw.line(surface, DINO_GREEN,
                             (cx + s, cy + 5), (cx + s + 15, cy - 20 - int(wave)), 4)

        elif expression == 'blink':
            # 眨眼
            pygame.draw.line(surface, BLACK, (cx - 12, cy - s * 0.6), (cx - 4, cy - s * 0.6), 2)
            pygame.draw.line(surface, BLACK, (cx + 4, cy - s * 0.6), (cx + 12, cy - s * 0.6), 2)
            # 微笑
            pygame.draw.arc(surface, BLACK,
                            (cx - 6, cy - s * 0.35, 12, 8), math.pi, 2 * math.pi, 2)

        else:  # normal
            # 正常可愛表情
            pygame.draw.circle(surface, WHITE, (cx - 8, cy - s * 0.6), 6)
            pygame.draw.circle(surface, WHITE, (cx + 8, cy - s * 0.6), 6)
            pygame.draw.circle(surface, BLACK, (cx - 8, cy - s * 0.6), 3)
            pygame.draw.circle(surface, BLACK, (cx + 8, cy - s * 0.6), 3)
            # 微笑
            pygame.draw.arc(surface, BLACK,
                            (cx - 6, cy - s * 0.35, 12, 8), math.pi, 2 * math.pi, 2)
            # 腮紅
            pygame.draw.circle(surface, BOUNCE_PINK, (cx - 14, cy - s * 0.35), 3)
            pygame.draw.circle(surface, BOUNCE_PINK, (cx + 14, cy - s * 0.35), 3)

        # 小尾巴
        tail_wave = math.sin(self.frame * 0.1) * 5
        pygame.draw.line(surface, DINO_GREEN,
                         (cx + s - 2, cy + s * 0.5),
                         (cx + s + 10, cy + s * 0.3 + int(tail_wave)), 4)

        # 腳
        pygame.draw.ellipse(surface, DINO_GREEN, (cx - s * 0.7, cy + s * 0.8, 12, 8))
        pygame.draw.ellipse(surface, DINO_GREEN, (cx + s * 0.2, cy + s * 0.8, 12, 8))


# ============================================================
# 墊子類別
# ============================================================
class Pad:
    """橋上的墊子（安全墊子 或 彈跳墊子）"""

    def __init__(self, x, y, index, is_safe, side):
        self.x = x
        self.y = y
        self.index = index       # 第幾格
        self.is_safe = is_safe   # True=安全, False=彈跳
        self.side = side         # 'left' 或 'right'
        self.width = 55
        self.height = 40
        self.spring_offset = 0   # 彈簧壓縮效果
        self.spring_velocity = 0
        self.revealed = False    # 是否已經被踩過/揭露
        self.bounce_anim = 0     # 彈簧動畫計時

    def trigger_spring(self):
        """觸發彈簧壓縮動畫"""
        self.spring_offset = 10
        self.spring_velocity = -2
        self.bounce_anim = 30

    def update(self):
        """更新彈簧動畫"""
        if self.spring_offset != 0:
            self.spring_velocity += 0.5
            self.spring_offset += self.spring_velocity
            if self.spring_offset >= 0:
                self.spring_offset = 0
                self.spring_velocity = 0
        if self.bounce_anim > 0:
            self.bounce_anim -= 1

    def draw(self, surface, shake_x=0, shake_y=0):
        """畫墊子"""
        x = int(self.x + shake_x)
        y = int(self.y + self.spring_offset + shake_y)
        w, h = self.width, self.height

        if not self.revealed:
            # 未揭露：神秘紫色墊子 + 問號
            pygame.draw.rect(surface, PURPLE, (x - w // 2, y - h // 2, w, h), border_radius=8)
            pygame.draw.rect(surface, WHITE, (x - w // 2, y - h // 2, w, h), 2, border_radius=8)
            # 問號
            text = font_medium.render("?", True, WHITE)
            surface.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
        else:
            if self.is_safe:
                # 安全墊子：綠色/藍色 + 笑臉
                color = SAFE_GREEN if self.index % 2 == 0 else SAFE_BLUE
                pygame.draw.rect(surface, color, (x - w // 2, y - h // 2, w, h), border_radius=8)
                pygame.draw.rect(surface, WHITE, (x - w // 2, y - h // 2, w, h), 2, border_radius=8)
                # 笑臉
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
                pygame.draw.arc(surface, BLACK, (x - 8, y - 2, 16, 10), math.pi, 2 * math.pi, 2)
            else:
                # 彈跳墊子：粉色/黃色 + 彈簧圖案
                color = BOUNCE_PINK if self.index % 2 == 0 else BOUNCE_YELLOW
                pygame.draw.rect(surface, color, (x - w // 2, y - h // 2, w, h), border_radius=8)
                pygame.draw.rect(surface, WHITE, (x - w // 2, y - h // 2, w, h), 2, border_radius=8)

                # 彈簧圖案（波浪線）
                spring_pts = []
                for i in range(8):
                    sx = x - 12 + i * 3.5
                    sy = y + math.sin(i * 1.5 + self.bounce_anim * 0.3) * 4
                    spring_pts.append((int(sx), int(sy)))
                if len(spring_pts) >= 2:
                    pygame.draw.lines(surface, ORANGE, False, spring_pts, 2)

                # 星星
                draw_star(surface, x, y - 8, 6, GOLD)


# ============================================================
# 背景雲朵
# ============================================================
class BackgroundCloud:
    def __init__(self):
        self.x = random.randint(-100, SCREEN_WIDTH + 100)
        self.y = random.randint(20, 200)
        self.speed = random.uniform(0.2, 0.6)
        self.size = random.randint(25, 50)

    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 150:
            self.x = -150
            self.y = random.randint(20, 200)

    def draw(self, surface):
        draw_cloud(surface, int(self.x), int(self.y), self.size)


# ============================================================
# 遊戲主類別
# ============================================================
class Game:
    """魔法跳跳橋遊戲"""

    # 遊戲狀態
    STATE_TITLE = 'title'
    STATE_PLAYING = 'playing'
    STATE_FALLING = 'falling'
    STATE_MESSAGE = 'message'
    STATE_VICTORY = 'victory'

    # 鼓勵訊息（超正向！）
    ENCOURAGE_MESSAGES = [
        "Oops~ Ha ha~ Let's jump again!",
        "Wow! A bouncy pad! So fun~",
        "No worries! We're the best!",
        "Haha~ Bounced back! Try again!",
        "Magic spring! Boing boing~",
        "Almost there! You can do it!",
        "That was fun! One more try~",
        "Wheee~ Bouncy bounce!",
    ]

    # 嘗試中文鼓勵訊息
    ENCOURAGE_MESSAGES_CN = [
        "哎呀～掉下去啦！哈哈～沒關係！",
        "哇！彈跳墊子！好好玩～",
        "沒事沒事～我們是最強的！",
        "哈哈～彈回來了！再跳一次！",
        "魔法彈簧～啵啵啵～",
        "快到了！你可以的！加油喔～",
        "好好玩！再試一次吧～",
        "咻～飛起來了！哈哈～",
    ]

    def __init__(self):
        self.state = self.STATE_TITLE
        self.total_wins = 0
        self.clouds = [BackgroundCloud() for _ in range(6)]
        self.shake_x = 0
        self.shake_y = 0
        self.shake_intensity = 0
        self.message_timer = 0
        self.message_text = ""
        self.message_text_sub = ""
        self.firework_timer = 0
        self.title_frame = 0
        # 檢測是否有中文字體可用
        self.has_chinese = self._check_chinese_font()
        self.reset_game()

    def _check_chinese_font(self):
        """檢查中文字體是否可用"""
        try:
            test_surface = font_medium.render("測試", True, BLACK)
            # 如果渲染出來的寬度很小，可能是方框字
            return test_surface.get_width() > 10
        except Exception:
            return False

    def get_encourage_msg(self):
        """取得鼓勵訊息"""
        if self.has_chinese:
            return random.choice(self.ENCOURAGE_MESSAGES_CN)
        return random.choice(self.ENCOURAGE_MESSAGES)

    def reset_game(self):
        """重設遊戲（新的一關）"""
        global particles
        particles = []

        # 產生墊子序列
        self.current_step = 0
        self.pads = []
        self.pad_pairs = []  # 每一格有左右兩個墊子

        # 橋的佈局
        bridge_start_x = 80
        bridge_end_x = SCREEN_WIDTH - 100
        step_width = (bridge_end_x - bridge_start_x) / NUM_STEPS
        bridge_y = 340  # 墊子的 y 位置

        for i in range(NUM_STEPS):
            x = bridge_start_x + step_width * i + step_width / 2
            y_top = bridge_y - 30   # 上面的墊子
            y_bot = bridge_y + 30   # 下面的墊子

            # 隨機決定哪個是安全的
            if random.random() < BOUNCE_CHANCE:
                # 有彈跳墊子（但總是一安全一彈跳）
                if random.random() < 0.5:
                    pad_left = Pad(x, y_top, i, True, 'left')
                    pad_right = Pad(x, y_bot, i, False, 'right')
                else:
                    pad_left = Pad(x, y_top, i, False, 'left')
                    pad_right = Pad(x, y_bot, i, True, 'right')
            else:
                # 兩個都安全（讓小孩容易過！）
                pad_left = Pad(x, y_top, i, True, 'left')
                pad_right = Pad(x, y_bot, i, True, 'right')

            self.pad_pairs.append((pad_left, pad_right))
            self.pads.extend([pad_left, pad_right])

        # 小恐龍
        self.dino = Dino(40, bridge_y)
        self.dino.base_y = bridge_y

        # 遊戲狀態
        self.state = self.STATE_PLAYING
        self.waiting_for_input = True
        self.selected_pad = None
        self.fall_return_step = 0

    def handle_input(self, event):
        """處理玩家輸入"""
        if self.state == self.STATE_TITLE:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                play_sound(snd_click)
                self.reset_game()
            return

        if self.state == self.STATE_VICTORY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                play_sound(snd_click)
                self.reset_game()
            return

        if self.state == self.STATE_MESSAGE:
            return  # 等訊息顯示完畢

        if self.state != self.STATE_PLAYING or not self.waiting_for_input:
            return

        if self.current_step >= NUM_STEPS:
            return

        chosen_side = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 滑鼠點擊：上半邊=左墊子，下半邊=右墊子
            mouse_y = event.pos[1]
            if mouse_y < SCREEN_HEIGHT / 2:
                chosen_side = 'left'   # 上面
            else:
                chosen_side = 'right'  # 下面
            play_sound(snd_click)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_LEFT:
                chosen_side = 'left'
                play_sound(snd_click)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT:
                chosen_side = 'right'
                play_sound(snd_click)

        if chosen_side and self.current_step < NUM_STEPS:
            pad_left, pad_right = self.pad_pairs[self.current_step]
            if chosen_side == 'left':
                self.selected_pad = pad_left
            else:
                self.selected_pad = pad_right

            # 揭露墊子
            pad_left.revealed = True
            pad_right.revealed = True

            self.waiting_for_input = False

            # 開始跳躍動畫
            target_x = self.selected_pad.x
            self.dino.jump_target_x = target_x
            self.dino.start_jump(target_x)

            # 墊子彈簧效果
            self.selected_pad.trigger_spring()

    def update(self):
        """每幀更新遊戲"""
        self.title_frame += 1

        # 更新背景雲朵
        for cloud in self.clouds:
            cloud.update()

        # 更新粒子
        global particles
        particles = [p for p in particles if p.update()]

        # 更新墊子
        for pad in self.pads:
            pad.update()

        # 畫面抖動衰減
        if self.shake_intensity > 0:
            self.shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity *= 0.9
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0
                self.shake_x = 0
                self.shake_y = 0

        if self.state == self.STATE_TITLE:
            return

        if self.state == self.STATE_MESSAGE:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.state = self.STATE_PLAYING
                self.waiting_for_input = True
            return

        if self.state == self.STATE_VICTORY:
            self.firework_timer += 1
            # 持續放煙火
            if self.firework_timer % 20 == 0:
                fx = random.randint(100, SCREEN_WIDTH - 100)
                fy = random.randint(50, 300)
                spawn_particles(fx, fy, 'firework', 20)
                spawn_particles(fx, fy, 'star', 5)
            self.dino.update()
            return

        # 更新小恐龍
        self.dino.update()

        # 檢查跳躍結果
        if not self.waiting_for_input and self.selected_pad:
            if self.dino.state == 'idle' and self.state == self.STATE_PLAYING:
                if self.selected_pad.is_safe:
                    # 安全！前進一步
                    self.current_step += 1
                    spawn_particles(self.dino.x, self.dino.y, 'star', 12)
                    spawn_particles(self.dino.x, self.dino.y, 'confetti', 5)

                    if self.current_step >= NUM_STEPS:
                        # 全部過完！勝利！
                        self.trigger_victory()
                    else:
                        self.waiting_for_input = True
                        self.selected_pad = None
                else:
                    # 彈跳墊子！觸發墜落動畫
                    self.state = self.STATE_FALLING
                    self.fall_return_step = max(0, self.current_step - 1)
                    self.shake_intensity = 5  # 輕微畫面抖動
                    self.dino.start_fall()

            elif self.dino.state == 'idle' and self.state == self.STATE_FALLING:
                # 墜落動畫完成，彈回了！
                self.state = self.STATE_MESSAGE

                # 回到前一格
                if self.fall_return_step > 0:
                    prev_left, prev_right = self.pad_pairs[self.fall_return_step - 1]
                    # 回到安全的那個墊子
                    if prev_left.is_safe:
                        self.dino.x = prev_left.x
                    else:
                        self.dino.x = prev_right.x
                else:
                    self.dino.x = 40

                self.dino.y = self.dino.base_y
                self.current_step = self.fall_return_step

                # 顯示鼓勵訊息
                self.message_text = self.get_encourage_msg()
                if self.has_chinese:
                    self.message_text_sub = "再跳一次！加油喔～"
                else:
                    self.message_text_sub = "Let's try again! You got this~"
                self.message_timer = 120  # 顯示 2 秒
                self.selected_pad = None

                spawn_particles(self.dino.x, self.dino.y, 'heart', 10)

    def trigger_victory(self):
        """觸發勝利慶祝！"""
        self.state = self.STATE_VICTORY
        self.total_wins += 1
        self.dino.state = 'celebrating'
        self.firework_timer = 0
        play_sound(snd_victory)

        # 大量煙火！
        for _ in range(5):
            fx = random.randint(100, SCREEN_WIDTH - 100)
            fy = random.randint(50, 250)
            spawn_particles(fx, fy, 'firework', 25)
            spawn_particles(fx, fy, 'star', 10)
            spawn_particles(fx, fy, 'confetti', 15)

    def draw(self):
        """繪製遊戲畫面"""
        # 背景漸層天空
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(135 + (200 - 135) * ratio)
            g = int(206 + (230 - 206) * ratio)
            b = int(250 + (255 - 250) * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 背景雲朵
        for cloud in self.clouds:
            cloud.draw(screen)

        sx = int(self.shake_x)
        sy = int(self.shake_y)

        if self.state == self.STATE_TITLE:
            self._draw_title()
            return

        # 草地
        pygame.draw.rect(screen, GRASS_GREEN,
                         (0 + sx, SCREEN_HEIGHT - 80 + sy, SCREEN_WIDTH, 80))
        # 草地花紋
        for i in range(0, SCREEN_WIDTH, 20):
            h = random.randint(5, 15) if self.title_frame == 1 else 10
            pygame.draw.line(screen, (90, 190, 90),
                             (i + sx, SCREEN_HEIGHT - 80 + sy),
                             (i + 3 + sx, SCREEN_HEIGHT - 80 - h + sy), 2)

        # 橋面（支撐結構）
        bridge_y = 340
        pygame.draw.rect(screen, (180, 140, 100),
                         (50 + sx, bridge_y + 50 + sy, SCREEN_WIDTH - 120, 8), border_radius=4)
        # 橋柱
        for px in [60, SCREEN_WIDTH - 80]:
            pygame.draw.rect(screen, (160, 120, 80),
                             (px + sx, bridge_y + 30 + sy, 12, SCREEN_HEIGHT - bridge_y - 90))

        # 終點裝飾（彩虹 + 蛋糕 + 星星）
        end_x = SCREEN_WIDTH - 50
        draw_rainbow(screen, end_x - 40 + sx, bridge_y - 80 + sy, 60)
        draw_cake(screen, end_x + sx, bridge_y - 10 + sy, 25)
        # 閃亮星星
        star_pulse = math.sin(self.title_frame * 0.05) * 3
        draw_star(screen, end_x - 20 + sx, bridge_y - 100 + sy, int(10 + star_pulse), GOLD)
        draw_star(screen, end_x + 20 + sx, bridge_y - 90 + sy, int(8 + star_pulse), BOUNCE_YELLOW)

        # 畫墊子
        for pad in self.pads:
            pad.draw(screen, sx, sy)

        # 墊子選擇提示
        if self.state == self.STATE_PLAYING and self.waiting_for_input and self.current_step < NUM_STEPS:
            pad_left, pad_right = self.pad_pairs[self.current_step]
            # 閃爍邊框提示
            flash = abs(math.sin(self.title_frame * 0.08)) * 255
            flash_color = (int(flash), int(flash * 0.8), 0)

            for pad in [pad_left, pad_right]:
                pygame.draw.rect(screen, flash_color,
                                 (int(pad.x - pad.width // 2 - 3 + sx),
                                  int(pad.y - pad.height // 2 - 3 + sy),
                                  pad.width + 6, pad.height + 6), 3, border_radius=10)

            # 操作提示
            if self.has_chinese:
                hint1 = font_tiny.render("點上面 或 按 ↑ = 選上面的墊子", True, BLACK)
                hint2 = font_tiny.render("點下面 或 按 ↓ = 選下面的墊子", True, BLACK)
            else:
                hint1 = font_tiny.render("Click top / Press UP = Top pad", True, BLACK)
                hint2 = font_tiny.render("Click bottom / Press DOWN = Bottom pad", True, BLACK)
            screen.blit(hint1, (SCREEN_WIDTH // 2 - hint1.get_width() // 2, 10))
            screen.blit(hint2, (SCREEN_WIDTH // 2 - hint2.get_width() // 2, 32))

            # 進度
            if self.has_chinese:
                progress = font_small.render(f"第 {self.current_step + 1}/{NUM_STEPS} 格", True, PURPLE)
            else:
                progress = font_small.render(f"Step {self.current_step + 1}/{NUM_STEPS}", True, PURPLE)
            screen.blit(progress, (SCREEN_WIDTH // 2 - progress.get_width() // 2, 55))

        # 墜落時的特效
        if self.state == self.STATE_FALLING:
            # 氣球接住效果
            if self.dino.bounce_phase == 1:
                # 畫氣球在小恐龍下方接住
                balloon_colors = [BALLOON_RED, BALLOON_BLUE, BALLOON_YELLOW, BALLOON_PINK]
                for i, bc in enumerate(balloon_colors):
                    bx = int(self.dino.x - 30 + i * 20 + sx)
                    by = int(self.dino.y + 20 + sy)
                    draw_balloon(screen, bx, by, bc, 12)

                # 顯示對話泡泡
                if self.has_chinese:
                    bubble_text = "氣球救你啦～飛上來！"
                else:
                    bubble_text = "Balloons to the rescue~!"
                self._draw_speech_bubble(self.dino.x + 50 + sx, self.dino.y - 40 + sy, bubble_text)

            elif self.dino.bounce_phase == 2:
                # 彈回中：氣球跟著往上
                balloon_colors = [BALLOON_RED, BALLOON_BLUE, BALLOON_YELLOW]
                for i, bc in enumerate(balloon_colors):
                    bx = int(self.dino.x - 20 + i * 20 + sx)
                    by = int(self.dino.y - 40 - i * 10 + sy)
                    draw_balloon(screen, bx, by, bc, 10)

            elif self.dino.bounce_phase == 0:
                # 墜落中：對話泡泡
                if self.has_chinese:
                    bubble_text = "哇哦～飛起來了！哈哈～"
                else:
                    bubble_text = "Wheeee~ I'm flying! Haha~"
                if self.dino.fall_time % 60 < 40:
                    self._draw_speech_bubble(self.dino.x + 50 + sx, self.dino.y - 50 + sy, bubble_text)

        # 畫小恐龍
        self.dino.draw(screen, sx, sy)

        # 畫粒子
        for p in particles:
            p.draw(screen, sx, sy)

        # 訊息顯示（鼓勵語句）
        if self.state == self.STATE_MESSAGE:
            self._draw_message_box()

        # 勝利畫面
        if self.state == self.STATE_VICTORY:
            self._draw_victory()

    def _draw_speech_bubble(self, x, y, text):
        """畫對話泡泡"""
        rendered = font_tiny.render(text, True, BLACK)
        tw, th = rendered.get_width(), rendered.get_height()
        bw, bh = tw + 20, th + 16

        # 確保不超出畫面
        x = max(bw // 2 + 5, min(SCREEN_WIDTH - bw // 2 - 5, x))
        y = max(bh // 2 + 5, min(SCREEN_HEIGHT - bh - 20, y))

        # 泡泡背景
        pygame.draw.rect(screen, WHITE, (int(x - bw // 2), int(y - bh // 2), bw, bh), border_radius=12)
        pygame.draw.rect(screen, PURPLE, (int(x - bw // 2), int(y - bh // 2), bw, bh), 2, border_radius=12)
        # 三角形尖頭
        points = [(int(x - 5), int(y + bh // 2)), (int(x + 5), int(y + bh // 2)), (int(x), int(y + bh // 2 + 8))]
        pygame.draw.polygon(screen, WHITE, points)
        pygame.draw.lines(screen, PURPLE, False, points, 2)
        # 文字
        screen.blit(rendered, (int(x - tw // 2), int(y - th // 2)))

    def _draw_message_box(self):
        """畫鼓勵訊息框"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 255, 255, 150), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(overlay, (0, 0))

        # 訊息框
        box_w, box_h = 500, 180
        box_x = SCREEN_WIDTH // 2 - box_w // 2
        box_y = SCREEN_HEIGHT // 2 - box_h // 2

        # 彩色邊框
        pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), border_radius=20)
        for i, c in enumerate(RAINBOW_COLORS):
            pygame.draw.rect(screen, c, (box_x - 3 + i, box_y - 3 + i, box_w + 6 - i * 2, box_h + 6 - i * 2), 3, border_radius=20)

        pygame.draw.rect(screen, WHITE, (box_x + 3, box_y + 3, box_w - 6, box_h - 6), border_radius=18)

        # 主訊息
        text1 = font_medium.render(self.message_text, True, PURPLE)
        screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, box_y + 30))

        # 副訊息
        text2 = font_small.render(self.message_text_sub, True, ORANGE)
        screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, box_y + 75))

        # 愛心裝飾
        for i in range(5):
            hx = box_x + 30 + i * (box_w - 60) // 4
            hy = box_y + box_h - 35
            draw_heart(screen, hx, hy, 8, random.choice([HEART_PINK, RED_SOFT, BOUNCE_PINK]))

        # 星星裝飾
        for i in range(4):
            star_x = box_x + 50 + i * (box_w - 100) // 3
            star_y = box_y + 15
            pulse = math.sin(self.title_frame * 0.1 + i) * 2
            draw_star(screen, star_x, star_y, int(8 + pulse), GOLD)

    def _draw_title(self):
        """畫標題畫面"""
        # 標題
        bounce = math.sin(self.title_frame * 0.05) * 8
        if self.has_chinese:
            title = font_huge.render("魔法跳跳橋", True, PURPLE)
        else:
            title = font_huge.render("Magic Bouncy Bridge", True, PURPLE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                            100 + int(bounce)))

        # 副標題
        if self.has_chinese:
            sub = font_medium.render("超可愛的跳跳冒險！", True, ORANGE)
        else:
            sub = font_medium.render("A Super Cute Jumping Adventure!", True, ORANGE)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 170))

        # 小恐龍預覽
        preview_dino = Dino(SCREEN_WIDTH // 2, 300)
        preview_dino.frame = self.title_frame
        preview_dino.blink_timer = self.title_frame
        if self.title_frame % 200 < 10:
            preview_dino.is_blinking = True
        preview_dino.size = 40
        preview_dino.draw(screen)

        # 星星裝飾
        for i in range(8):
            angle = self.title_frame * 0.02 + i * math.pi / 4
            sx = SCREEN_WIDTH // 2 + int(math.cos(angle) * 120)
            sy = 280 + int(math.sin(angle) * 40)
            pulse = math.sin(self.title_frame * 0.08 + i) * 3
            draw_star(screen, sx, sy, int(8 + pulse), random.choice(RAINBOW_COLORS))

        # 開始提示
        flash = abs(math.sin(self.title_frame * 0.06))
        alpha = int(100 + flash * 155)
        if self.has_chinese:
            start_text = font_medium.render("按空格鍵開始魔法跳跳橋～", True,
                                            (alpha, int(alpha * 0.5), 0))
        else:
            start_text = font_medium.render("Press SPACE to start the adventure~", True,
                                            (alpha, int(alpha * 0.5), 0))
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 420))

        # 歷史分數
        if self.total_wins > 0:
            if self.has_chinese:
                wins = font_small.render(f"你已經過了 {self.total_wins} 次橋！最棒寶貝！", True, GOLD)
            else:
                wins = font_small.render(f"You've crossed {self.total_wins} bridges! Amazing!", True, GOLD)
            screen.blit(wins, (SCREEN_WIDTH // 2 - wins.get_width() // 2, 480))

        # 彩虹裝飾
        draw_rainbow(screen, 100, 80, 50)
        draw_rainbow(screen, SCREEN_WIDTH - 160, 80, 50)

    def _draw_victory(self):
        """畫勝利畫面"""
        # 半透明金色背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 255, 200, 100), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(overlay, (0, 0))

        # 勝利文字
        bounce = math.sin(self.title_frame * 0.08) * 5
        if self.has_chinese:
            text1 = font_huge.render("太厲害了！", True, GOLD)
            text2 = font_large.render("你過了魔法橋！超勇敢！耶～", True, PURPLE)
            text3 = font_medium.render(f"你已經過了 {self.total_wins} 次橋！最棒寶貝！", True, ORANGE)
            text4 = font_small.render("按 R 再玩一次！", True, BLACK)
            text5 = font_tiny.render("謝謝玩遊戲！你是最可愛的小冒險家！", True, HEART_PINK)
        else:
            text1 = font_huge.render("Amazing!", True, GOLD)
            text2 = font_large.render("You crossed the Magic Bridge! So brave!", True, PURPLE)
            text3 = font_medium.render(f"Bridges crossed: {self.total_wins} times! Best kid ever!", True, ORANGE)
            text4 = font_small.render("Press R to play again!", True, BLACK)
            text5 = font_tiny.render("Thanks for playing! You are the cutest adventurer!", True, HEART_PINK)

        y_offset = 80
        for i, text in enumerate([text1, text2, text3, text4, text5]):
            bonce = math.sin(self.title_frame * 0.06 + i * 0.5) * 3
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                               y_offset + int(bonce)))
            y_offset += text.get_height() + 15

        # 大量星星和愛心裝飾
        for i in range(12):
            angle = self.title_frame * 0.03 + i * math.pi / 6
            sx = SCREEN_WIDTH // 2 + int(math.cos(angle) * 200)
            sy = 300 + int(math.sin(angle) * 80)
            pulse = math.sin(self.title_frame * 0.1 + i) * 4
            if i % 2 == 0:
                draw_star(screen, sx, sy, int(10 + pulse), random.choice(RAINBOW_COLORS))
            else:
                draw_heart(screen, sx, sy, int(8 + pulse), HEART_PINK)


# ============================================================
# 主程式入口
# ============================================================
def main():
    """遊戲主迴圈"""
    game = Game()

    running = True
    while running:
        # 事件處理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    if game.state == game.STATE_VICTORY:
                        game.state = game.STATE_TITLE
                        play_sound(snd_click)
                    elif game.state == game.STATE_TITLE:
                        pass
                    else:
                        game.state = game.STATE_TITLE
                        play_sound(snd_click)
            game.handle_input(event)

        # 更新
        game.update()

        # 繪製
        game.draw()

        # 更新畫面
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
