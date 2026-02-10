#!/usr/bin/env python3
"""
🌈 魔法跳繩橋 - 兒童版魷魚遊戲跳繩關卡 🌈
Magic Jump Rope Bridge - A Kid-Friendly Squid Game Jump Rope Level

適合 5 歲小朋友玩的超可愛跳繩遊戲！
靈感來自魷魚遊戲 Season 3 的 Jump Rope，
但完全沒有任何可怕元素，只有可愛跳跳、搞笑躲繩子、正向鼓勵！

安裝：pip install pygame          （macOS 請用 pip3 或在 venv 內）
執行：python3 magic_jumprope_game.py

操作方式：
  - 空格鍵 或 滑鼠左鍵 = 跳躍（超簡單，5 歲就能玩！）
  - R 鍵 = 重新開始
  - ESC = 離開遊戲

跳繩邏輯說明：
  - 繩子用角度 (rope_angle) 旋轉，0~360 度循環
  - 繩子接近地面時 (angle 在 danger zone)，若小動物沒跳就被碰到
  - 跳躍用 velocity_y += GRAVITY 做拋物線
  - 被碰到 → 可愛墜落 + 彈回（sin wave 左右搖擺 + 粒子特效）
  - 成功跳過 → 前進一小步 + 星星彩帶

墜落動畫說明：
  - velocity_y += GRAVITY 模擬重力
  - x 偏移 = sin(fall_time * SWING_SPEED) * SWING_AMP 做左右搖擺
  - 掉到 FALL_MAX_Y 後被雲朵接住 → velocity 反轉彈回
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

# 音效初始化（環境不支援也不會崩潰）
SOUND_ENABLED = False
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    SOUND_ENABLED = True
except Exception:
    pass

# ============================================================
# 遊戲常數設定（全部集中，方便調整！）
# ============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 跳繩參數
ROPE_BASE_SPEED = 1.8       # 繩子基礎旋轉速度（度/幀）
ROPE_MAX_SPEED = 3.5         # 繩子最高速度
ROPE_SPEED_INCREASE = 0.03   # 每次成功跳過，繩速增加
ROPE_DANGER_START = 340      # 繩子「危險區」起始角度（接近地面）
ROPE_DANGER_END = 380        # 繩子「危險區」結束角度
ROPE_SAFE_WINDOW = 40        # 繩子轉過後的安全角度窗口

# 跳躍參數
JUMP_VELOCITY = -11.0        # 跳躍初始速度（負值 = 往上）
GRAVITY = 0.55               # 重力加速度
GROUND_Y = 400               # 地面 y 座標

# 墜落動畫參數
FALL_GRAVITY = 0.35          # 墜落時的重力（比較慢，可愛感）
FALL_MAX_Y = SCREEN_HEIGHT * 0.72   # 墜落到 72% 高度觸發彈回
BOUNCE_VELOCITY = -8.5       # 彈回速度
SWING_AMP = 35               # 左右搖擺幅度
SWING_SPEED = 7              # 搖擺速度

# 遊戲進度
BRIDGE_LENGTH = 14           # 橋的總步數（走幾步到終點）
GAME_TIME = 90               # 遊戲時間（秒），設長一點不給壓力

# 顏色 🎨
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_TOP = (135, 200, 255)
SKY_BOT = (210, 235, 255)
BRIDGE_BROWN = (180, 140, 100)
BRIDGE_DARK = (150, 115, 80)
BRIDGE_RAIL = (200, 160, 120)
CLOUD_WHITE = (245, 248, 255)
CLOUD_SHADOW = (220, 230, 245)
GRASS_GREEN = (130, 210, 130)
SAFE_GREEN = (100, 215, 130)
GOLD = (255, 215, 0)
ORANGE = (255, 180, 80)
PURPLE = (170, 120, 255)
DEEP_PURPLE = (130, 80, 200)
PINK = (255, 150, 190)
HOT_PINK = (255, 100, 160)
SOFT_RED = (255, 120, 120)
LIGHT_BLUE = (170, 215, 255)
BABY_BLUE = (200, 230, 255)
YELLOW = (255, 240, 100)
BRIGHT_YELLOW = (255, 255, 130)
HEART_PINK = (255, 130, 175)
ROPE_PINK = (255, 100, 170)
ROPE_SHINE = (255, 180, 220)
DOLL_SKIN = (255, 220, 195)
DOLL_DRESS_ORANGE = (255, 165, 80)
DOLL_DRESS_BLUE = (100, 160, 240)
FOX_ORANGE = (240, 160, 70)
FOX_BELLY = (255, 230, 200)
FOX_DARK = (200, 120, 50)
RAINBOW = [
    (255, 100, 100), (255, 180, 80), (255, 255, 100),
    (100, 220, 100), (100, 180, 255), (150, 100, 255), (255, 150, 220),
]
BALLOON_COLORS = [(255, 100, 100), (100, 180, 255), (255, 240, 100),
                  (255, 160, 200), (130, 220, 130)]

# ============================================================
# 畫面
# ============================================================
try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.HWSURFACE | pygame.DOUBLEBUF)
except Exception:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🌈 魔法跳繩橋 - Magic Jump Rope Bridge 🌈")
clock = pygame.time.Clock()

# ============================================================
# 字體（自動偵測中文字體）
# ============================================================
def get_font(size):
    """嘗試載入支援中文的字體"""
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                continue
    return pygame.font.Font(None, size)


font_huge = get_font(52)
font_large = get_font(38)
font_medium = get_font(26)
font_small = get_font(20)
font_tiny = get_font(16)

# 偵測中文支援
def _check_chinese():
    try:
        s = font_medium.render("測試中文", True, BLACK)
        return s.get_width() > 20
    except Exception:
        return False

HAS_CN = _check_chinese()

# ============================================================
# 程式碼生成音效（不需外部檔案）
# ============================================================
def make_sound(freq, dur_ms, vol=0.25, kind='sine'):
    if not SOUND_ENABLED:
        return None
    try:
        sr = 22050
        n = int(sr * dur_ms / 1000)
        buf = bytearray(n * 2)
        for i in range(n):
            t = i / sr
            env = max(0.0, 1.0 - i / n * 0.8)
            if kind == 'sine':
                v = math.sin(2 * math.pi * freq * t) * vol * env
            elif kind == 'bounce':
                f = freq + (i / n) * 500
                v = math.sin(2 * math.pi * f * t) * vol * env
            elif kind == 'fall':
                f = max(80, freq - (i / n) * 350)
                v = math.sin(2 * math.pi * f * t) * vol * env
            elif kind == 'victory':
                v = (math.sin(2 * math.pi * freq * t)
                     + math.sin(2 * math.pi * freq * 1.25 * t)
                     + math.sin(2 * math.pi * freq * 1.5 * t)) / 3 * vol * env
            else:
                v = math.sin(2 * math.pi * freq * t) * vol * env
            s = max(-32768, min(32767, int(v * 32767)))
            buf[i * 2] = s & 0xFF
            buf[i * 2 + 1] = (s >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


snd_jump = make_sound(650, 150, 0.2, 'bounce')
snd_success = make_sound(800, 200, 0.2, 'bounce')
snd_fall = make_sound(480, 400, 0.15, 'fall')
snd_bounce_back = make_sound(420, 300, 0.25, 'bounce')
snd_victory = make_sound(523, 900, 0.2, 'victory')
snd_click = make_sound(900, 60, 0.12, 'sine')


def play(snd):
    if snd and SOUND_ENABLED:
        try:
            snd.play()
        except Exception:
            pass


# ============================================================
# 粒子系統 ✨
# ============================================================
particles = []


class Particle:
    def __init__(self, x, y, kind='star'):
        self.x, self.y = x, y
        self.kind = kind
        self.age = 0
        self.max_age = random.randint(25, 65)
        self.color = random.choice(RAINBOW)
        self.size = random.randint(3, 8)
        if kind == 'star':
            self.vx = random.uniform(-2.5, 2.5)
            self.vy = random.uniform(-3.5, -0.5)
        elif kind == 'bubble':
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-2.2, -0.3)
            self.size = random.randint(5, 13)
            self.color = random.choice([LIGHT_BLUE, CLOUD_WHITE, PINK, YELLOW])
        elif kind == 'confetti':
            self.vx = random.uniform(-4.5, 4.5)
            self.vy = random.uniform(-5.5, -1)
            self.rot = random.uniform(0, 360)
            self.rot_spd = random.uniform(-12, 12)
        elif kind == 'heart':
            self.vx = random.uniform(-1.5, 1.5)
            self.vy = random.uniform(-2.8, -0.5)
            self.color = random.choice([HEART_PINK, SOFT_RED, PINK])
        elif kind == 'firework':
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(2, 7)
            self.vx = math.cos(a) * sp
            self.vy = math.sin(a) * sp
            self.size = random.randint(2, 5)
            self.max_age = random.randint(18, 48)
        elif kind == 'rope_spark':
            self.vx = random.uniform(-1.5, 1.5)
            self.vy = random.uniform(-1, 1)
            self.size = random.randint(2, 4)
            self.max_age = random.randint(10, 25)
            self.color = random.choice([ROPE_SHINE, YELLOW, WHITE])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1
        if self.kind in ('star', 'confetti', 'firework', 'heart'):
            self.vy += 0.06
        if self.kind == 'confetti':
            self.rot += self.rot_spd
        return self.age < self.max_age

    def draw(self, surf, ox=0, oy=0):
        alpha = max(0.0, 1.0 - self.age / self.max_age)
        ix, iy = int(self.x + ox), int(self.y + oy)
        sz = max(1, int(self.size * alpha))
        if self.kind == 'star':
            _draw_star(surf, ix, iy, sz, self.color)
        elif self.kind == 'bubble':
            pygame.draw.circle(surf, self.color, (ix, iy), sz, 1)
            pygame.draw.circle(surf, WHITE, (ix - sz // 3, iy - sz // 3), max(1, sz // 4))
        elif self.kind == 'confetti':
            s2 = pygame.Surface((sz * 2, sz), pygame.SRCALPHA)
            pygame.draw.rect(s2, (*self.color, int(255 * alpha)), (0, 0, sz * 2, sz))
            r2 = pygame.transform.rotate(s2, self.rot)
            surf.blit(r2, (ix - r2.get_width() // 2, iy - r2.get_height() // 2))
        elif self.kind == 'heart':
            _draw_heart(surf, ix, iy, sz, self.color)
        elif self.kind in ('firework', 'rope_spark'):
            pygame.draw.circle(surf, self.color, (ix, iy), sz)


def _draw_star(surf, x, y, sz, col):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = sz if i % 2 == 0 else sz * 0.4
        pts.append((x + int(math.cos(a) * r), y - int(math.sin(a) * r)))
    if len(pts) >= 3:
        pygame.draw.polygon(surf, col, pts)


def _draw_heart(surf, x, y, sz, col):
    s = max(2, sz)
    pygame.draw.circle(surf, col, (x - s // 3, y - s // 4), s // 2)
    pygame.draw.circle(surf, col, (x + s // 3, y - s // 4), s // 2)
    pygame.draw.polygon(surf, col, [(x - s, y), (x, y + s), (x + s, y)])


def spawn(x, y, kind='star', n=10):
    for _ in range(n):
        particles.append(Particle(x, y, kind))


# ============================================================
# 繪圖輔助函式
# ============================================================
def draw_cloud(surf, x, y, sz=40, col=CLOUD_WHITE):
    pygame.draw.ellipse(surf, col, (x, y, sz * 2, sz))
    pygame.draw.ellipse(surf, col, (x + sz * 0.3, y - sz * 0.4, sz * 1.4, sz))
    pygame.draw.ellipse(surf, col, (x - sz * 0.3, y - sz * 0.1, sz, sz * 0.8))
    pygame.draw.ellipse(surf, col, (x + sz * 1.1, y - sz * 0.1, sz, sz * 0.8))


def draw_balloon(surf, x, y, col, sz=18):
    pygame.draw.ellipse(surf, col, (x - sz, y - sz * 1.3, sz * 2, sz * 2.6))
    pygame.draw.ellipse(surf, WHITE, (x - sz * 0.35, y - sz * 0.7, sz * 0.45, sz * 0.7))
    pygame.draw.line(surf, BLACK, (x, y + sz * 1.3), (x + 2, y + sz * 2), 2)
    pygame.draw.polygon(surf, col, [(x - 3, y + sz * 1.3), (x + 3, y + sz * 1.3), (x, y + sz * 1.5)])


def draw_rainbow_arch(surf, x, y, r=90):
    cols = [(255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 200, 0), (0, 150, 255), (75, 0, 130), (148, 0, 211)]
    for i, c in enumerate(cols):
        ri = r - i * 7
        if ri > 0:
            pygame.draw.arc(surf, c, (x - ri, y - ri, ri * 2, ri * 2), 0, math.pi, 5)


def draw_gift_box(surf, x, y, sz=35):
    """畫一個大禮物盒"""
    # 盒子
    pygame.draw.rect(surf, SOFT_RED, (x - sz, y - sz * 0.7, sz * 2, sz * 1.4), border_radius=4)
    # 蝴蝶結橫條
    pygame.draw.rect(surf, GOLD, (x - sz, y - 3, sz * 2, 6))
    pygame.draw.rect(surf, GOLD, (x - 3, y - sz * 0.7, 6, sz * 1.4))
    # 蝴蝶結
    pygame.draw.ellipse(surf, GOLD, (x - 14, y - sz * 0.7 - 12, 14, 14))
    pygame.draw.ellipse(surf, GOLD, (x + 2, y - sz * 0.7 - 12, 14, 14))
    pygame.draw.circle(surf, ORANGE, (x, y - sz * 0.7 - 5), 4)


# ============================================================
# 可愛娃娃（英熙姐姐 & 哲秀哥哥 — 超可愛版）
# ============================================================
class CuteDoll:
    """巨型可愛娃娃，站在橋兩邊轉繩子"""

    def __init__(self, x, y, facing_right, dress_color, name):
        self.x = x
        self.y = y
        self.facing = 1 if facing_right else -1
        self.dress_color = dress_color
        self.name = name
        self.frame = 0
        self.arm_angle = 0  # 手臂角度，跟繩子同步

    def update(self, rope_angle):
        self.frame += 1
        # 手臂跟著繩子旋轉的頻率微微晃動
        self.arm_angle = math.sin(math.radians(rope_angle) * 2) * 15

    def draw(self, surf, ox=0, oy=0):
        x = int(self.x + ox)
        y = int(self.y + oy)
        f = self.facing

        # 身體（洋裝）
        body_w, body_h = 50, 70
        pygame.draw.ellipse(surf, self.dress_color,
                            (x - body_w // 2, y - 10, body_w, body_h))
        # 白色領口
        pygame.draw.ellipse(surf, WHITE, (x - 12, y - 8, 24, 16))

        # 頭
        head_r = 30
        pygame.draw.circle(surf, DOLL_SKIN, (x, y - 30), head_r)

        # 頭髮
        hair_col = (60, 40, 30)
        pygame.draw.ellipse(surf, hair_col, (x - 32, y - 62, 64, 40))
        if self.dress_color == DOLL_DRESS_ORANGE:
            # 英熙：雙馬尾
            pygame.draw.ellipse(surf, hair_col, (x - 40, y - 50, 22, 35))
            pygame.draw.ellipse(surf, hair_col, (x + 18, y - 50, 22, 35))
            # 髮飾
            pygame.draw.circle(surf, SOFT_RED, (x - 30, y - 55), 5)
            pygame.draw.circle(surf, SOFT_RED, (x + 30, y - 55), 5)
        else:
            # 哲秀：短髮
            pygame.draw.ellipse(surf, hair_col, (x - 30, y - 58, 60, 30))

        # 眼睛（大大圓圓超可愛）
        for ex_off in [-10, 10]:
            pygame.draw.circle(surf, WHITE, (x + ex_off, y - 32), 8)
            pygame.draw.circle(surf, BLACK, (x + ex_off, y - 31), 5)
            pygame.draw.circle(surf, WHITE, (x + ex_off - 2, y - 33), 2)

        # 腮紅
        pygame.draw.circle(surf, PINK, (x - 18, y - 24), 6)
        pygame.draw.circle(surf, PINK, (x + 18, y - 24), 6)

        # 微笑
        smile_bounce = math.sin(self.frame * 0.08) * 2
        pygame.draw.arc(surf, SOFT_RED,
                        (x - 10, y - 26 + int(smile_bounce), 20, 14),
                        math.pi, 2 * math.pi, 2)

        # 手臂（晃動，轉繩子的感覺）
        arm_y_off = math.sin(self.frame * 0.1) * 5 + self.arm_angle
        # 外側手（持繩子）
        arm_end_x = x + f * 35
        arm_end_y = int(y + 10 + arm_y_off)
        pygame.draw.line(surf, DOLL_SKIN, (x + f * 20, y + 5),
                         (arm_end_x, arm_end_y), 6)
        # 手掌
        pygame.draw.circle(surf, DOLL_SKIN, (arm_end_x, arm_end_y), 5)

        # 內側手揮手打招呼
        wave = math.sin(self.frame * 0.12) * 20
        inner_arm_x = x - f * 30
        inner_arm_y = int(y - 20 + wave)
        pygame.draw.line(surf, DOLL_SKIN, (x - f * 18, y + 5),
                         (inner_arm_x, inner_arm_y), 5)
        pygame.draw.circle(surf, DOLL_SKIN, (inner_arm_x, inner_arm_y), 5)

        # 腳
        pygame.draw.ellipse(surf, BLACK, (x - 15, y + 55, 14, 8))
        pygame.draw.ellipse(surf, BLACK, (x + 2, y + 55, 14, 8))

        # 名字
        name_surf = font_tiny.render(self.name, True, DEEP_PURPLE)
        surf.blit(name_surf, (x - name_surf.get_width() // 2, y + 65))


# ============================================================
# 小狐狸角色 🦊
# ============================================================
class Fox:
    """超可愛的小狐狸主角"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.vy = 0               # y 速度
        self.on_ground = True
        self.state = 'idle'       # idle / jumping / falling / bouncing / celebrating
        self.frame = 0
        self.fall_time = 0
        self.bounce_phase = 0     # 0=墜落, 1=接住, 2=彈回, 3=完成
        self.rotation = 0
        self.blink_timer = 0
        self.is_blinking = False
        self.walk_anim = 0
        self.size = 22

    def jump(self):
        """跳躍！"""
        if self.on_ground and self.state in ('idle',):
            self.state = 'jumping'
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            play(snd_jump)

    def start_fall(self):
        """開始可愛墜落動畫"""
        self.state = 'falling'
        self.vy = 0
        self.fall_time = 0
        self.bounce_phase = 0
        self.rotation = 0
        play(snd_fall)

    def advance(self, new_x):
        """前進一步"""
        self.base_x = new_x
        self.x = new_x
        self.walk_anim = 15
        play(snd_success)
        spawn(self.x, self.y - 10, 'star', 8)
        spawn(self.x, self.y - 10, 'confetti', 5)

    def update(self):
        self.frame += 1

        # 眨眼
        self.blink_timer += 1
        if self.blink_timer > random.randint(100, 220):
            self.is_blinking = True
            self.blink_timer = 0
        if self.is_blinking and self.blink_timer > 8:
            self.is_blinking = False
            self.blink_timer = 0

        # 走路動畫遞減
        if self.walk_anim > 0:
            self.walk_anim -= 1

        if self.state == 'jumping':
            # 跳躍：拋物線
            self.vy += GRAVITY
            self.y += self.vy
            if self.y >= self.base_y:
                self.y = self.base_y
                self.vy = 0
                self.on_ground = True
                self.state = 'idle'

        elif self.state == 'falling':
            self.fall_time += 1

            if self.bounce_phase == 0:
                # 墜落中：重力 + 左右搖擺
                self.vy += FALL_GRAVITY
                self.y += self.vy
                swing = math.sin(self.fall_time * SWING_SPEED * 0.1) * SWING_AMP
                self.x = self.base_x + swing
                self.rotation += 6
                if self.frame % 4 == 0:
                    spawn(self.x, self.y, 'star', 2)
                    spawn(self.x, self.y, 'bubble', 1)
                if self.y >= FALL_MAX_Y:
                    self.y = FALL_MAX_Y
                    self.bounce_phase = 1
                    self.vy = 0
                    self.fall_time = 0
                    play(snd_bounce_back)
                    spawn(self.x, self.y, 'star', 12)
                    spawn(self.x, self.y, 'bubble', 8)

            elif self.bounce_phase == 1:
                # 被雲朵接住，短暫停留
                self.rotation *= 0.88
                self.fall_time += 1
                if self.fall_time > 18:
                    self.bounce_phase = 2
                    self.vy = BOUNCE_VELOCITY

            elif self.bounce_phase == 2:
                # 彈回！
                self.vy += FALL_GRAVITY * 0.5
                self.y += self.vy
                self.rotation *= 0.93
                swing = math.sin(self.fall_time * 0.25) * SWING_AMP * 0.25
                self.x = self.base_x + swing
                if self.frame % 3 == 0:
                    spawn(self.x, self.y, 'confetti', 2)
                    spawn(self.x, self.y, 'heart', 1)
                if self.y <= self.base_y:
                    self.y = self.base_y
                    self.x = self.base_x
                    self.rotation = 0
                    self.on_ground = True
                    self.bounce_phase = 3
                    self.state = 'idle'
                    spawn(self.x, self.y - 10, 'heart', 8)
                    spawn(self.x, self.y - 10, 'star', 6)

        elif self.state == 'celebrating':
            b = math.sin(self.frame * 0.15) * 12
            self.y = self.base_y + b
            if self.frame % 12 == 0:
                spawn(self.x, self.y - 25, 'star', 3)
                spawn(self.x, self.y - 25, 'confetti', 3)

    def draw(self, surf, ox=0, oy=0):
        s = pygame.Surface((70, 70), pygame.SRCALPHA)
        cx, cy = 35, 35

        if self.state == 'falling' and self.bounce_phase == 0:
            self._body(s, cx, cy, 'surprised')
        elif self.state == 'falling' and self.bounce_phase >= 1:
            self._body(s, cx, cy, 'happy')
        elif self.state == 'celebrating':
            self._body(s, cx, cy, 'celebrating')
        elif self.state == 'jumping':
            self._body(s, cx, cy, 'jumping')
        else:
            expr = 'blink' if self.is_blinking else 'normal'
            self._body(s, cx, cy, expr)

        if abs(self.rotation) > 0.5:
            s = pygame.transform.rotate(s, -self.rotation)

        rect = s.get_rect(center=(int(self.x + ox), int(self.y - 18 + oy)))
        surf.blit(s, rect)

    def _body(self, surf, cx, cy, expr):
        sz = self.size

        # 尾巴（先畫，在身體後面）
        tail_wave = math.sin(self.frame * 0.12) * 8
        tail_pts = [
            (cx + sz + 2, cy + sz * 0.2),
            (cx + sz + 15 + int(tail_wave), cy),
            (cx + sz + 18 + int(tail_wave * 0.5), cy + 8),
        ]
        pygame.draw.polygon(surf, FOX_ORANGE, tail_pts)
        # 尾巴白色尖端
        pygame.draw.circle(surf, WHITE, (int(cx + sz + 16 + tail_wave * 0.7), cy + 3), 5)

        # 身體
        pygame.draw.ellipse(surf, FOX_ORANGE, (cx - sz, cy - sz * 0.3, sz * 2, sz * 1.6))
        pygame.draw.ellipse(surf, FOX_BELLY, (cx - sz * 0.55, cy + sz * 0.1, sz * 1.1, sz * 1.0))

        # 頭
        pygame.draw.circle(surf, FOX_ORANGE, (cx, cy - sz * 0.4), int(sz * 0.85))
        # 白色臉頰
        pygame.draw.ellipse(surf, WHITE, (cx - sz * 0.6, cy - sz * 0.5, sz * 1.2, sz * 0.8))

        # 耳朵（三角形）
        for ear_x in [-10, 10]:
            pts = [
                (cx + ear_x - 5, cy - sz * 0.6),
                (cx + ear_x + 5, cy - sz * 0.6),
                (cx + ear_x, cy - sz * 1.3),
            ]
            pygame.draw.polygon(surf, FOX_ORANGE, pts)
            # 耳朵內部粉色
            pts2 = [
                (cx + ear_x - 3, cy - sz * 0.65),
                (cx + ear_x + 3, cy - sz * 0.65),
                (cx + ear_x, cy - sz * 1.15),
            ]
            pygame.draw.polygon(surf, PINK, pts2)

        # 表情
        if expr == 'surprised':
            pygame.draw.circle(surf, WHITE, (cx - 6, cy - sz * 0.5), 7)
            pygame.draw.circle(surf, WHITE, (cx + 6, cy - sz * 0.5), 7)
            pygame.draw.circle(surf, BLACK, (cx - 6, cy - sz * 0.5), 4)
            pygame.draw.circle(surf, BLACK, (cx + 6, cy - sz * 0.5), 4)
            _draw_star(surf, cx - 6, cy - sz * 0.5, 3, GOLD)
            _draw_star(surf, cx + 6, cy - sz * 0.5, 3, GOLD)
            pygame.draw.ellipse(surf, SOFT_RED, (cx - 5, cy - sz * 0.2, 10, 8))
            w = math.sin(self.frame * 0.3) * 12
            pygame.draw.line(surf, FOX_ORANGE, (cx - sz, cy + 3),
                             (cx - sz - 10, cy - 5 + int(w)), 3)
            pygame.draw.line(surf, FOX_ORANGE, (cx + sz, cy + 3),
                             (cx + sz + 10, cy - 5 - int(w)), 3)

        elif expr == 'happy':
            pygame.draw.circle(surf, WHITE, (cx - 6, cy - sz * 0.5), 5)
            pygame.draw.circle(surf, WHITE, (cx + 6, cy - sz * 0.5), 5)
            pygame.draw.circle(surf, BLACK, (cx - 6, cy - sz * 0.5), 3)
            pygame.draw.circle(surf, BLACK, (cx + 6, cy - sz * 0.5), 3)
            pygame.draw.arc(surf, SOFT_RED, (cx - 7, cy - sz * 0.3, 14, 10),
                            math.pi, 2 * math.pi, 2)
            pygame.draw.circle(surf, PINK, (cx - 12, cy - sz * 0.25), 4)
            pygame.draw.circle(surf, PINK, (cx + 12, cy - sz * 0.25), 4)

        elif expr == 'celebrating':
            pygame.draw.arc(surf, BLACK, (cx - 10, cy - sz * 0.7, 8, 7), 0, math.pi, 2)
            pygame.draw.arc(surf, BLACK, (cx + 2, cy - sz * 0.7, 8, 7), 0, math.pi, 2)
            pygame.draw.arc(surf, SOFT_RED, (cx - 9, cy - sz * 0.3, 18, 12),
                            math.pi, 2 * math.pi, 3)
            pygame.draw.circle(surf, PINK, (cx - 13, cy - sz * 0.25), 5)
            pygame.draw.circle(surf, PINK, (cx + 13, cy - sz * 0.25), 5)
            w = math.sin(self.frame * 0.2) * 12
            pygame.draw.line(surf, FOX_ORANGE, (cx - sz, cy + 3),
                             (cx - sz - 14, cy - 18 + int(w)), 3)
            pygame.draw.line(surf, FOX_ORANGE, (cx + sz, cy + 3),
                             (cx + sz + 14, cy - 18 - int(w)), 3)

        elif expr == 'jumping':
            pygame.draw.circle(surf, WHITE, (cx - 6, cy - sz * 0.5), 6)
            pygame.draw.circle(surf, WHITE, (cx + 6, cy - sz * 0.5), 6)
            pygame.draw.circle(surf, BLACK, (cx - 6, cy - sz * 0.48), 3)
            pygame.draw.circle(surf, BLACK, (cx + 6, cy - sz * 0.48), 3)
            pygame.draw.arc(surf, BLACK, (cx - 5, cy - sz * 0.3, 10, 7),
                            math.pi, 2 * math.pi, 2)
            # 腳縮起來（跳躍姿勢）
            pygame.draw.ellipse(surf, FOX_ORANGE, (cx - 8, cy + sz * 0.6, 8, 5))
            pygame.draw.ellipse(surf, FOX_ORANGE, (cx + 1, cy + sz * 0.6, 8, 5))

        elif expr == 'blink':
            pygame.draw.line(surf, BLACK, (cx - 10, cy - sz * 0.5), (cx - 2, cy - sz * 0.5), 2)
            pygame.draw.line(surf, BLACK, (cx + 2, cy - sz * 0.5), (cx + 10, cy - sz * 0.5), 2)
            pygame.draw.arc(surf, BLACK, (cx - 5, cy - sz * 0.25, 10, 7),
                            math.pi, 2 * math.pi, 2)

        else:  # normal
            pygame.draw.circle(surf, WHITE, (cx - 6, cy - sz * 0.5), 5)
            pygame.draw.circle(surf, WHITE, (cx + 6, cy - sz * 0.5), 5)
            pygame.draw.circle(surf, BLACK, (cx - 6, cy - sz * 0.5), 3)
            pygame.draw.circle(surf, BLACK, (cx + 6, cy - sz * 0.5), 3)
            pygame.draw.arc(surf, BLACK, (cx - 5, cy - sz * 0.3, 10, 6),
                            math.pi, 2 * math.pi, 2)
            pygame.draw.circle(surf, PINK, (cx - 12, cy - sz * 0.25), 3)
            pygame.draw.circle(surf, PINK, (cx + 12, cy - sz * 0.25), 3)

        # 鼻子
        pygame.draw.circle(surf, BLACK, (cx, cy - sz * 0.35), 2)

        # 腳（非跳躍時）
        if expr != 'jumping':
            bob = math.sin(self.frame * 0.2) * 2 if self.walk_anim > 0 else 0
            pygame.draw.ellipse(surf, FOX_DARK,
                                (cx - sz * 0.6, cy + sz * 0.8 + int(bob), 10, 6))
            pygame.draw.ellipse(surf, FOX_DARK,
                                (cx + sz * 0.15, cy + sz * 0.8 - int(bob), 10, 6))


# ============================================================
# 背景雲朵
# ============================================================
class BgCloud:
    def __init__(self):
        self.x = random.randint(-120, SCREEN_WIDTH + 120)
        self.y = random.randint(15, 180)
        self.spd = random.uniform(0.15, 0.5)
        self.sz = random.randint(25, 55)

    def update(self):
        self.x += self.spd
        if self.x > SCREEN_WIDTH + 160:
            self.x = -160
            self.y = random.randint(15, 180)

    def draw(self, surf):
        draw_cloud(surf, int(self.x), int(self.y), self.sz)


# ============================================================
# 遊戲主類別
# ============================================================
class Game:
    ST_TITLE = 'title'
    ST_PLAY = 'playing'
    ST_FALL = 'falling'
    ST_MSG = 'message'
    ST_WIN = 'victory'

    MSGS_CN = [
        "哎呀～繩子好調皮！哈哈～",
        "沒關係～我們是最強跳繩隊！",
        "哇哦～飛高高！哈哈再來！",
        "繩子太快了！但你更快！",
        "啵～彈回來了！繼續加油！",
        "好好玩的繩子！再跳一次～",
        "沒事沒事～我們超厲害的！",
        "哈哈～差一點點！下次一定行！",
    ]
    MSGS_EN = [
        "Oops~ Naughty rope! Haha~",
        "No worries! We're the best jumpers!",
        "Wheee~ Bounced back! Try again!",
        "That rope is fast! But you're faster!",
        "Boing~ Back up! Keep going!",
        "So fun! Let's jump again~",
        "Almost! You'll get it next time!",
        "Haha~ One more try! You got this!",
    ]

    SONGS_CN = ["跳～跳～跳繩繩～", "一起來跳繩～好開心！",
                "轉呀轉～跳呀跳～", "魔法繩子轉轉轉～"]
    SONGS_EN = ["Jump~ jump~ rope~", "Let's jump together~",
                "Spin and jump~", "Magic rope go round~"]

    def __init__(self):
        self.state = self.ST_TITLE
        self.total_wins = 0
        self.clouds = [BgCloud() for _ in range(7)]
        self.shake_x = 0
        self.shake_y = 0
        self.shake_int = 0
        self.msg_timer = 0
        self.msg_text = ""
        self.msg_sub = ""
        self.fw_timer = 0
        self.gframe = 0
        self.song_timer = 0
        self.song_text = ""
        self._reset()

    def _get_msg(self):
        return random.choice(self.MSGS_CN if HAS_CN else self.MSGS_EN)

    def _get_song(self):
        return random.choice(self.SONGS_CN if HAS_CN else self.SONGS_EN)

    def _reset(self):
        global particles
        particles = []

        # 橋的起點和終點 x
        self.bridge_x_start = 110
        self.bridge_x_end = SCREEN_WIDTH - 110
        self.bridge_y = GROUND_Y

        # 繩子
        self.rope_angle = 0.0         # 繩子當前角度（0~360）
        self.rope_speed = ROPE_BASE_SPEED
        self.rope_speed_target = ROPE_BASE_SPEED
        self.rope_speed_change_cd = 120  # 幾幀後改變速度
        self.rope_center_x = (self.bridge_x_start + self.bridge_x_end) / 2
        self.rope_center_y = self.bridge_y - 10
        self.rope_radius_h = 70       # 繩子水平半徑
        self.rope_radius_v = 100      # 繩子垂直半徑

        # 娃娃
        doll_y = self.bridge_y - 60
        name_l = "英熙姐姐" if HAS_CN else "Younghee"
        name_r = "哲秀哥哥" if HAS_CN else "Cheolsu"
        self.doll_left = CuteDoll(self.rope_center_x - self.rope_radius_h - 50,
                                  doll_y, True, DOLL_DRESS_ORANGE, name_l)
        self.doll_right = CuteDoll(self.rope_center_x + self.rope_radius_h + 50,
                                   doll_y, False, DOLL_DRESS_BLUE, name_r)

        # 小狐狸
        self.fox = Fox(self.bridge_x_start, self.bridge_y)
        self.fox.base_y = self.bridge_y

        # 遊戲進度
        self.steps_done = 0
        self.step_size = (self.bridge_x_end - self.bridge_x_start) / BRIDGE_LENGTH

        # 繩子通過次數（跳過的次數）
        self.jumps_cleared = 0
        self.rope_was_danger = False   # 上一幀繩子是否在危險區
        self.jump_scored = False       # 這次危險區是否已判定

        # 計時
        self.time_left = GAME_TIME * FPS  # 幀數
        self.stars_earned = 0

        self.state = self.ST_PLAY

    def handle(self, ev):
        if self.state == self.ST_TITLE:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                play(snd_click)
                self._reset()
            return

        if self.state == self.ST_WIN:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                play(snd_click)
                self.state = self.ST_TITLE
            return

        if self.state == self.ST_MSG:
            return

        if self.state == self.ST_FALL:
            return

        if self.state == self.ST_PLAY:
            jumped = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                jumped = True
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                jumped = True
            if jumped:
                self.fox.jump()

    def update(self):
        self.gframe += 1

        for c in self.clouds:
            c.update()

        global particles
        particles = [p for p in particles if p.update()]

        # 畫面抖動
        if self.shake_int > 0:
            self.shake_x = random.uniform(-self.shake_int, self.shake_int)
            self.shake_y = random.uniform(-self.shake_int, self.shake_int)
            self.shake_int *= 0.88
            if self.shake_int < 0.4:
                self.shake_int = 0
                self.shake_x = self.shake_y = 0

        if self.state == self.ST_TITLE:
            return

        if self.state == self.ST_MSG:
            self.msg_timer -= 1
            if self.msg_timer <= 0:
                self.state = self.ST_PLAY
            return

        if self.state == self.ST_WIN:
            self.fw_timer += 1
            if self.fw_timer % 18 == 0:
                fx = random.randint(80, SCREEN_WIDTH - 80)
                fy = random.randint(40, 280)
                spawn(fx, fy, 'firework', 22)
                spawn(fx, fy, 'star', 5)
            self.fox.update()
            self.doll_left.update(self.rope_angle)
            self.doll_right.update(self.rope_angle)
            return

        # --- 遊戲進行中 ---

        # 計時
        if self.time_left > 0:
            self.time_left -= 1

        # 繩子旋轉
        self.rope_angle += self.rope_speed
        if self.rope_angle >= 360:
            self.rope_angle -= 360

        # 繩子速度變化（快慢交替，但不太快）
        self.rope_speed_change_cd -= 1
        if self.rope_speed_change_cd <= 0:
            # 隨機決定新速度（有慢有快）
            if random.random() < 0.4:
                self.rope_speed_target = ROPE_BASE_SPEED * random.uniform(0.5, 0.8)
            else:
                max_spd = min(ROPE_MAX_SPEED, ROPE_BASE_SPEED + self.jumps_cleared * ROPE_SPEED_INCREASE)
                self.rope_speed_target = random.uniform(ROPE_BASE_SPEED, max_spd)
            self.rope_speed_change_cd = random.randint(100, 250)

        # 平滑過渡繩速
        self.rope_speed += (self.rope_speed_target - self.rope_speed) * 0.02

        # 繩子發光粒子
        if self.gframe % 8 == 0:
            ra = math.radians(self.rope_angle)
            rx = self.rope_center_x + math.cos(ra) * self.rope_radius_h
            ry = self.rope_center_y - math.sin(ra) * self.rope_radius_v * 0.5
            spawn(rx, ry, 'rope_spark', 2)

        # 娃娃唱歌文字
        self.song_timer -= 1
        if self.song_timer <= 0:
            self.song_text = self._get_song()
            self.song_timer = random.randint(150, 300)

        # 娃娃更新
        self.doll_left.update(self.rope_angle)
        self.doll_right.update(self.rope_angle)

        # 小狐狸更新
        self.fox.update()

        # --- 繩子碰撞判定 ---
        # 繩子在「危險區」= 接近地面的角度
        in_danger = ROPE_DANGER_START <= (self.rope_angle % 360) <= ROPE_DANGER_END

        if in_danger and not self.rope_was_danger:
            # 進入危險區：判定是否跳過
            self.jump_scored = False

        if in_danger and not self.jump_scored:
            fox_is_jumping = (not self.fox.on_ground) and self.fox.state == 'jumping'
            if fox_is_jumping:
                # 跳過了！成功！
                self.jump_scored = True
                self.jumps_cleared += 1
                self.stars_earned += 1
                self.steps_done += 1
                new_x = self.bridge_x_start + self.steps_done * self.step_size
                new_x = min(new_x, self.bridge_x_end)
                self.fox.advance(new_x)

                if self.steps_done >= BRIDGE_LENGTH:
                    self._trigger_win()

        # 危險區結束：如果還沒跳過，就被繩子打到了
        if self.rope_was_danger and not in_danger and not self.jump_scored:
            if self.fox.state not in ('falling',):
                # 被繩子碰到！觸發墜落
                self.state = self.ST_FALL
                self.shake_int = 6
                self.fox.start_fall()

        self.rope_was_danger = in_danger

        # 墜落結束判定
        if self.state == self.ST_FALL and self.fox.state == 'idle':
            self.state = self.ST_MSG
            # 回退一步（但不低於 0）
            self.steps_done = max(0, self.steps_done - 1)
            new_x = self.bridge_x_start + self.steps_done * self.step_size
            self.fox.x = new_x
            self.fox.base_x = new_x
            self.fox.y = self.fox.base_y

            self.msg_text = self._get_msg()
            self.msg_sub = "再跳一次！加油喔～" if HAS_CN else "Try again! You got this~"
            self.msg_timer = 110
            spawn(self.fox.x, self.fox.y - 10, 'heart', 8)

        # 時間到也算勝利（鼓勵版 — 不會輸！）
        if self.time_left <= 0 and self.state == self.ST_PLAY:
            self._trigger_win()

    def _trigger_win(self):
        self.state = self.ST_WIN
        self.total_wins += 1
        self.fox.state = 'celebrating'
        self.fw_timer = 0
        play(snd_victory)
        for _ in range(6):
            spawn(random.randint(80, SCREEN_WIDTH - 80),
                  random.randint(40, 250), 'firework', 25)
            spawn(random.randint(80, SCREEN_WIDTH - 80),
                  random.randint(40, 250), 'star', 10)

    # ============================================================
    # 繪製
    # ============================================================
    def draw(self):
        # 天空漸層
        for y in range(SCREEN_HEIGHT):
            r = y / SCREEN_HEIGHT
            cr = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * r)
            cg = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * r)
            cb = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * r)
            pygame.draw.line(screen, (cr, cg, cb), (0, y), (SCREEN_WIDTH, y))

        # 背景雲
        for c in self.clouds:
            c.draw(screen)

        sx, sy = int(self.shake_x), int(self.shake_y)

        if self.state == self.ST_TITLE:
            self._draw_title()
            return

        # 深淵 → 彩虹雲朵（橋下方）
        self._draw_abyss_clouds(sx, sy)

        # 橋
        self._draw_bridge(sx, sy)

        # 終點裝飾
        self._draw_goal(sx, sy)

        # 娃娃（在繩子後面）
        self.doll_left.draw(screen, sx, sy)
        self.doll_right.draw(screen, sx, sy)

        # 繩子
        self._draw_rope(sx, sy)

        # 唱歌文字
        if self.song_timer > 0 and self.state == self.ST_PLAY:
            alpha = min(1.0, self.song_timer / 30) if self.song_timer < 30 else 1.0
            col = (int(DEEP_PURPLE[0] * alpha), int(DEEP_PURPLE[1] * alpha), int(DEEP_PURPLE[2] * alpha))
            st = font_tiny.render(self.song_text, True, col)
            screen.blit(st, (self.rope_center_x - st.get_width() // 2 + sx,
                             self.rope_center_y - self.rope_radius_v - 30 + sy))

        # 墜落特效
        if self.state == self.ST_FALL:
            self._draw_fall_fx(sx, sy)

        # 小狐狸
        self.fox.draw(screen, sx, sy)

        # 粒子
        for p in particles:
            p.draw(screen, sx, sy)

        # HUD
        self._draw_hud(sx, sy)

        # 訊息框
        if self.state == self.ST_MSG:
            self._draw_msg_box()

        # 勝利
        if self.state == self.ST_WIN:
            self._draw_victory()

    def _draw_abyss_clouds(self, sx, sy):
        """橋下方的彩虹雲海（代替深淵）"""
        cloud_y_base = self.bridge_y + 80
        for i in range(10):
            cx = (i * 100 + int(self.gframe * 0.2 + i * 30)) % (SCREEN_WIDTH + 200) - 100
            cy = cloud_y_base + math.sin(self.gframe * 0.01 + i) * 10
            col = RAINBOW[i % len(RAINBOW)]
            light_col = (min(255, col[0] + 100), min(255, col[1] + 100), min(255, col[2] + 100))
            draw_cloud(screen, cx + sx, int(cy + sy), 45, light_col)

        # 底部彩色漸層
        for y2 in range(int(cloud_y_base + 30), SCREEN_HEIGHT):
            r = (y2 - cloud_y_base - 30) / max(1, SCREEN_HEIGHT - cloud_y_base - 30)
            col_idx = r * (len(RAINBOW) - 1)
            i1 = int(col_idx)
            i2 = min(len(RAINBOW) - 1, i1 + 1)
            f = col_idx - i1
            c = tuple(int(RAINBOW[i1][j] * (1 - f) + RAINBOW[i2][j] * f) for j in range(3))
            light = tuple(min(255, v + 80) for v in c)
            pygame.draw.line(screen, light, (0 + sx, y2 + sy), (SCREEN_WIDTH + sx, y2 + sy))

    def _draw_bridge(self, sx, sy):
        """畫狹窄的橋"""
        bx1 = self.bridge_x_start - 30
        bx2 = self.bridge_x_end + 30
        by = self.bridge_y
        bw = bx2 - bx1
        bh = 20

        # 橋面
        pygame.draw.rect(screen, BRIDGE_BROWN,
                         (bx1 + sx, by + 15 + sy, bw, bh), border_radius=3)
        # 木紋
        for i in range(bx1, bx2, 30):
            pygame.draw.line(screen, BRIDGE_DARK,
                             (i + sx, by + 15 + sy), (i + sx, by + 35 + sy), 1)

        # 欄杆
        pygame.draw.line(screen, BRIDGE_RAIL,
                         (bx1 + sx, by - 15 + sy), (bx2 + sx, by - 15 + sy), 3)
        pygame.draw.line(screen, BRIDGE_RAIL,
                         (bx1 + sx, by + 50 + sy), (bx2 + sx, by + 50 + sy), 3)
        # 欄杆柱
        for i in range(bx1, bx2 + 1, 50):
            pygame.draw.line(screen, BRIDGE_RAIL,
                             (i + sx, by - 15 + sy), (i + sx, by + 50 + sy), 2)

        # 進度格子（小狐狸走了多少步）
        for i in range(BRIDGE_LENGTH + 1):
            gx = self.bridge_x_start + i * self.step_size
            if i < self.steps_done:
                col = SAFE_GREEN
            elif i == self.steps_done:
                # 當前位置閃爍
                flash = abs(math.sin(self.gframe * 0.08)) * 0.5 + 0.5
                col = (int(255 * flash), int(240 * flash), int(100 * flash))
            else:
                col = BABY_BLUE
            pygame.draw.circle(screen, col, (int(gx + sx), by + 25 + sy), 5)

    def _draw_goal(self, sx, sy):
        """終點裝飾"""
        gx = self.bridge_x_end + 20
        gy = self.bridge_y

        # 彩虹拱門
        draw_rainbow_arch(screen, gx + sx, gy - 40 + sy, 55)

        # 禮物盒
        draw_gift_box(screen, gx + sx, gy + sy, 22)

        # 氣球
        for i, bc in enumerate(BALLOON_COLORS[:3]):
            bx = gx - 15 + i * 15
            bob = math.sin(self.gframe * 0.04 + i) * 5
            draw_balloon(screen, bx + sx, int(gy - 60 + bob + sy), bc, 10)

        # 閃星
        pulse = math.sin(self.gframe * 0.06) * 3
        _draw_star(screen, gx - 10 + sx, gy - 80 + sy, int(8 + pulse), GOLD)
        _draw_star(screen, gx + 15 + sx, gy - 70 + sy, int(6 + pulse), YELLOW)

    def _draw_rope(self, sx, sy):
        """
        畫旋轉的魔法繩子 🎀

        繩子旋轉用角度 rope_angle（0~360 度）：
        - 用 cos(angle) 決定繩子在水平方向的位置
        - 用 sin(angle) 決定繩子的高度
        - 角度在 340~380 度時繩子最接近地面（危險區）
        - 用粗線段 + 星星圖案 + 金屬粉色漸層呈現
        """
        cx = self.rope_center_x
        cy = self.rope_center_y
        rh = self.rope_radius_h
        rv = self.rope_radius_v

        # 繩子用多個點串連成弧線
        angle_rad = math.radians(self.rope_angle)

        # 繩子的端點（連接兩個娃娃的手）
        rope_points = []
        num_segs = 20
        for i in range(num_segs + 1):
            t = i / num_segs  # 0 ~ 1
            # 弧線插值：從左娃娃手 → 繩子弧線中點 → 右娃娃手
            seg_x = cx - rh + t * rh * 2

            # 繩子的弧度受 rope_angle 影響
            sag = math.sin(t * math.pi)  # 中間下垂最多
            height = math.sin(angle_rad) * rv * sag
            seg_y = cy - height

            rope_points.append((int(seg_x + sx), int(seg_y + sy)))

        # 畫繩子陰影
        if len(rope_points) >= 2:
            shadow_pts = [(p[0] + 2, p[1] + 3) for p in rope_points]
            pygame.draw.lines(screen, (200, 100, 140), False, shadow_pts, 6)

        # 畫繩子本體（粉色金屬感）
        if len(rope_points) >= 2:
            pygame.draw.lines(screen, ROPE_PINK, False, rope_points, 5)
            # 亮面
            pygame.draw.lines(screen, ROPE_SHINE, False, rope_points, 2)

        # 繩子上的星星裝飾
        for i in range(0, num_segs + 1, 4):
            if i < len(rope_points):
                px, py = rope_points[i]
                pulse = math.sin(self.gframe * 0.1 + i) * 2
                _draw_star(screen, px, py, int(4 + pulse),
                           GOLD if i % 8 == 0 else YELLOW)

        # 危險指示（繩子接近地面時閃紅光...其實是可愛的粉色閃光）
        if ROPE_DANGER_START - 30 <= (self.rope_angle % 360) <= ROPE_DANGER_END + 10:
            for pt in rope_points[8:13]:
                pygame.draw.circle(screen, (*HOT_PINK, ), pt, 4)

    def _draw_fall_fx(self, sx, sy):
        """墜落時的特效"""
        if self.fox.bounce_phase == 1:
            # 雲朵接住
            draw_cloud(screen, int(self.fox.x - 40 + sx), int(self.fox.y + 10 + sy), 35, CLOUD_WHITE)
            draw_cloud(screen, int(self.fox.x + 5 + sx), int(self.fox.y + 15 + sy), 30, BABY_BLUE)
            # 氣球
            for i, bc in enumerate([BALLOON_COLORS[0], BALLOON_COLORS[1], BALLOON_COLORS[3]]):
                bx = int(self.fox.x - 25 + i * 25 + sx)
                by = int(self.fox.y + 20 + sy)
                draw_balloon(screen, bx, by, bc, 10)

            txt = "氣球救你啦～飛上來！" if HAS_CN else "Balloons to the rescue~!"
            self._bubble(self.fox.x + 55 + sx, self.fox.y - 35 + sy, txt)

        elif self.fox.bounce_phase == 2:
            for i, bc in enumerate(BALLOON_COLORS[:3]):
                bx = int(self.fox.x - 20 + i * 20 + sx)
                by = int(self.fox.y - 35 - i * 8 + sy)
                draw_balloon(screen, bx, by, bc, 9)

        elif self.fox.bounce_phase == 0:
            txt = "哇哦～飛高高！哈哈～" if HAS_CN else "Wheeee~ I'm flying! Haha~"
            if self.fox.fall_time % 50 < 35:
                self._bubble(self.fox.x + 50 + sx, self.fox.y - 45 + sy, txt)

    def _bubble(self, x, y, text):
        """對話泡泡"""
        r = font_tiny.render(text, True, BLACK)
        tw, th = r.get_width(), r.get_height()
        bw, bh = tw + 18, th + 14
        x = max(bw // 2 + 5, min(SCREEN_WIDTH - bw // 2 - 5, x))
        y = max(bh // 2 + 5, min(SCREEN_HEIGHT - bh - 15, y))
        pygame.draw.rect(screen, WHITE,
                         (int(x - bw // 2), int(y - bh // 2), bw, bh), border_radius=10)
        pygame.draw.rect(screen, PURPLE,
                         (int(x - bw // 2), int(y - bh // 2), bw, bh), 2, border_radius=10)
        tri = [(int(x - 4), int(y + bh // 2)),
               (int(x + 4), int(y + bh // 2)),
               (int(x), int(y + bh // 2 + 7))]
        pygame.draw.polygon(screen, WHITE, tri)
        pygame.draw.lines(screen, PURPLE, False, tri, 2)
        screen.blit(r, (int(x - tw // 2), int(y - th // 2)))

    def _draw_hud(self, sx, sy):
        """遊戲 HUD"""
        if self.state not in (self.ST_PLAY, self.ST_FALL, self.ST_MSG):
            return

        # 進度
        prog = f"Step {self.steps_done}/{BRIDGE_LENGTH}" if not HAS_CN else f"第 {self.steps_done}/{BRIDGE_LENGTH} 步"
        t = font_small.render(prog, True, DEEP_PURPLE)
        screen.blit(t, (10, 10))

        # 星星
        star_txt = f"Stars: {self.stars_earned}" if not HAS_CN else f"星星: {self.stars_earned}"
        t2 = font_small.render(star_txt, True, GOLD)
        screen.blit(t2, (10, 35))
        _draw_star(screen, 10 + t2.get_width() + 12, 44, 8, GOLD)

        # 時間
        secs = max(0, self.time_left // FPS)
        time_txt = f"Time: {secs}s" if not HAS_CN else f"時間: {secs}秒"
        t3 = font_small.render(time_txt, True, ORANGE if secs > 15 else SOFT_RED)
        screen.blit(t3, (SCREEN_WIDTH - t3.get_width() - 10, 10))

        # 跳躍提示
        if self.state == self.ST_PLAY:
            hint = "Press SPACE or Click to JUMP!" if not HAS_CN else "按空格鍵 或 點滑鼠 = 跳！"
            flash = abs(math.sin(self.gframe * 0.06))
            col = (int(100 + flash * 100), int(50 + flash * 80), int(150 + flash * 100))
            ht = font_tiny.render(hint, True, col)
            screen.blit(ht, (SCREEN_WIDTH // 2 - ht.get_width() // 2, SCREEN_HEIGHT - 30))

    def _draw_msg_box(self):
        """鼓勵訊息框"""
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(ov, (255, 255, 255, 140), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(ov, (0, 0))

        bw, bh = 480, 170
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = SCREEN_HEIGHT // 2 - bh // 2

        pygame.draw.rect(screen, WHITE, (bx, by, bw, bh), border_radius=18)
        for i, c in enumerate(RAINBOW):
            pygame.draw.rect(screen, c,
                             (bx - 3 + i, by - 3 + i, bw + 6 - i * 2, bh + 6 - i * 2),
                             3, border_radius=18)
        pygame.draw.rect(screen, WHITE, (bx + 4, by + 4, bw - 8, bh - 8), border_radius=16)

        t1 = font_medium.render(self.msg_text, True, PURPLE)
        screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, by + 28))

        t2 = font_small.render(self.msg_sub, True, ORANGE)
        screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, by + 70))

        for i in range(5):
            hx = bx + 30 + i * (bw - 60) // 4
            _draw_heart(screen, hx, by + bh - 32, 7, random.choice([HEART_PINK, SOFT_RED]))

        for i in range(4):
            stx = bx + 45 + i * (bw - 90) // 3
            p2 = math.sin(self.gframe * 0.1 + i) * 2
            _draw_star(screen, stx, by + 12, int(7 + p2), GOLD)

    def _draw_title(self):
        """標題畫面"""
        bob = math.sin(self.gframe * 0.05) * 8

        if HAS_CN:
            t = font_huge.render("魔法跳繩橋", True, DEEP_PURPLE)
        else:
            t = font_huge.render("Magic Jump Rope Bridge", True, DEEP_PURPLE)
        screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 75 + int(bob)))

        if HAS_CN:
            sub = font_medium.render("和英熙姐姐、哲秀哥哥一起跳繩吧！", True, ORANGE)
        else:
            sub = font_medium.render("Jump rope with Younghee & Cheolsu!", True, ORANGE)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 140))

        # 預覽小狐狸
        pf = Fox(SCREEN_WIDTH // 2, 290)
        pf.frame = self.gframe
        pf.blink_timer = self.gframe
        if self.gframe % 180 < 10:
            pf.is_blinking = True
        pf.size = 28
        pf.draw(screen)

        # 預覽娃娃
        dl = CuteDoll(180, 300, True, DOLL_DRESS_ORANGE, "")
        dr = CuteDoll(SCREEN_WIDTH - 180, 300, False, DOLL_DRESS_BLUE, "")
        dl.frame = self.gframe
        dr.frame = self.gframe
        dl.draw(screen)
        dr.draw(screen)

        # 星星圈
        for i in range(10):
            a = self.gframe * 0.02 + i * math.pi / 5
            stx = SCREEN_WIDTH // 2 + int(math.cos(a) * 140)
            sty = 275 + int(math.sin(a) * 40)
            p = math.sin(self.gframe * 0.08 + i) * 3
            _draw_star(screen, stx, sty, int(7 + p), random.choice(RAINBOW))

        # 開始提示
        fl = abs(math.sin(self.gframe * 0.06))
        al = int(100 + fl * 155)
        if HAS_CN:
            st = font_medium.render("按空格鍵開始魔法跳繩橋～", True, (al, int(al * 0.4), 0))
        else:
            st = font_medium.render("Press SPACE to start~", True, (al, int(al * 0.4), 0))
        screen.blit(st, (SCREEN_WIDTH // 2 - st.get_width() // 2, 400))

        if self.total_wins > 0:
            if HAS_CN:
                w = font_small.render(f"你已經過關 {self.total_wins} 次！超厲害的小英雄！", True, GOLD)
            else:
                w = font_small.render(f"Cleared {self.total_wins} times! Amazing hero!", True, GOLD)
            screen.blit(w, (SCREEN_WIDTH // 2 - w.get_width() // 2, 450))

        draw_rainbow_arch(screen, 80, 65, 45)
        draw_rainbow_arch(screen, SCREEN_WIDTH - 140, 65, 45)

    def _draw_victory(self):
        """勝利畫面"""
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(ov, (255, 255, 210, 90), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(ov, (0, 0))

        bob = math.sin(self.gframe * 0.08) * 5

        if HAS_CN:
            lines = [
                (font_huge, "太棒啦！", GOLD),
                (font_large, "你躲過魔法繩子了！超勇敢！耶～", PURPLE),
                (font_medium, f"收集了 {self.stars_earned} 顆星星！你已經過關 {self.total_wins} 次！", ORANGE),
                (font_small, "按 R 再玩一次！", BLACK),
                (font_tiny, "謝謝玩遊戲！你是最會跳的小寶貝！", HEART_PINK),
            ]
        else:
            lines = [
                (font_huge, "Amazing!", GOLD),
                (font_large, "You dodged the magic rope! So brave!", PURPLE),
                (font_medium, f"{self.stars_earned} stars! Cleared {self.total_wins} times!", ORANGE),
                (font_small, "Press R to play again!", BLACK),
                (font_tiny, "Thanks for playing! You're the best jumper!", HEART_PINK),
            ]

        y_off = 70
        for i, (fnt, txt, col) in enumerate(lines):
            r = fnt.render(txt, True, col)
            b = math.sin(self.gframe * 0.06 + i * 0.5) * 3
            screen.blit(r, (SCREEN_WIDTH // 2 - r.get_width() // 2, y_off + int(b)))
            y_off += r.get_height() + 14

        for i in range(14):
            a = self.gframe * 0.03 + i * math.pi / 7
            stx = SCREEN_WIDTH // 2 + int(math.cos(a) * 220)
            sty = 320 + int(math.sin(a) * 90)
            p = math.sin(self.gframe * 0.1 + i) * 4
            if i % 2 == 0:
                _draw_star(screen, stx, sty, int(10 + p), random.choice(RAINBOW))
            else:
                _draw_heart(screen, stx, sty, int(8 + p), HEART_PINK)


# ============================================================
# 主迴圈
# ============================================================
def main():
    game = Game()
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r:
                    if game.state in (game.ST_WIN,):
                        game.state = game.ST_TITLE
                        play(snd_click)
                    elif game.state not in (game.ST_TITLE,):
                        game.state = game.ST_TITLE
                        play(snd_click)
            game.handle(ev)

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
