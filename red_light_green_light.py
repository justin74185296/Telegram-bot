#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 兒童版魷魚遊戲 —— 一二三木頭人 (Red Light, Green Light)
適合 5 歲小朋友玩的超可愛版本！

安裝方式：
    pip install pygame

執行方式：
    python red_light_green_light.py

操作說明：
    - 按「空格鍵」或「滑鼠左鍵」讓小兔子往前跑
    - 綠燈時可以跑，紅燈時要停下來喔！
    - 跑到終點就贏啦！🎉

作者：AI Assistant
"""

# ==================== 匯入模組 ====================
import pygame
import random
import math
import sys
import io
import struct
import wave
import array

# ==================== 音效可用性檢查 ====================
# 某些系統（例如 macOS + Python 3.14）可能沒有 pygame.mixer
# 遊戲會自動偵測，沒有音效一樣可以正常玩！
SOUND_AVAILABLE = False  # 稍後在 Game.__init__ 中嘗試初始化


class DummySound:
    """當音效模組不可用時，使用這個假的 Sound 物件（不會出錯）"""
    def play(self):
        pass

    def stop(self):
        pass

# ==================== 遊戲設定（可以自由修改！）====================

# 畫面大小
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# 顏色定義（RGB）
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 80, 80)
GREEN = (80, 200, 80)
BLUE = (100, 150, 255)
YELLOW = (255, 220, 50)
PINK = (255, 180, 200)
ORANGE = (255, 160, 50)
PURPLE = (180, 100, 255)
LIGHT_GREEN = (180, 255, 180)
LIGHT_RED = (255, 200, 200)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (100, 180, 60)
DARK_GREEN = (60, 130, 40)
BROWN = (139, 90, 43)
LIGHT_BROWN = (200, 150, 100)
PEACH = (255, 218, 185)
DARK_PINK = (255, 105, 140)
GOLD = (255, 215, 0)
CONFETTI_COLORS = [RED, GREEN, BLUE, YELLOW, PINK, ORANGE, PURPLE, GOLD]

# 角色設定
PLAYER_START_X = 60       # 角色起始 X 位置
PLAYER_Y = 420             # 角色 Y 位置（地面上）
PLAYER_STEP = 18           # 每次按鍵前進的距離（可調整難度）
FINISH_LINE_X = 720        # 終點線 X 位置

# 紅綠燈切換時間範圍（秒）
LIGHT_MIN_TIME = 3.0
LIGHT_MAX_TIME = 8.0

# 幀率
FPS = 60

# ==================== 音效生成（使用程式產生簡單音效）====================

def generate_wav_bytes(frequency, duration_ms, volume=0.5, wave_type='sine'):
    """產生 WAV 格式的音效位元組資料（需要 mixer 可用才有意義）"""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_ms / 1000)

    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        if wave_type == 'sine':
            value = math.sin(2 * math.pi * frequency * t)
        elif wave_type == 'square':
            value = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
        else:
            value = math.sin(2 * math.pi * frequency * t)

        # 淡入淡出效果，避免爆音
        fade_samples = min(500, num_samples // 4)
        if i < fade_samples:
            value *= i / fade_samples
        elif i > num_samples - fade_samples:
            value *= (num_samples - i) / fade_samples

        samples.append(int(value * volume * 32767))

    # 建立 WAV 資料
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(array.array('h', samples).tobytes())
    buf.seek(0)
    return buf


def create_sound_go():
    """產生綠燈「GO!」快樂音效 —— 三聲快速上升嗶嗶嗶"""
    if not SOUND_AVAILABLE:
        return DummySound()
    sample_rate = 22050
    total_samples = int(sample_rate * 0.6)
    samples = []

    for i in range(total_samples):
        t = i / sample_rate
        # 三段不同頻率
        if t < 0.15:
            freq = 523  # C5
        elif t < 0.3:
            freq = 659  # E5
        elif t < 0.5:
            freq = 784  # G5
        else:
            freq = 1047  # C6

        value = math.sin(2 * math.pi * freq * t)

        # 每段音符之間有短暫靜音
        beat_pos = t % 0.15
        if beat_pos > 0.12:
            value *= 0.1

        # 淡入淡出
        fade = min(200, total_samples // 6)
        if i < fade:
            value *= i / fade
        elif i > total_samples - fade:
            value *= (total_samples - i) / fade

        samples.append(int(value * 0.4 * 32767))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(array.array('h', samples).tobytes())
    buf.seek(0)
    return pygame.mixer.Sound(buf)


def create_sound_stop():
    """產生紅燈「停～」溫柔叮聲"""
    if not SOUND_AVAILABLE:
        return DummySound()
    buf = generate_wav_bytes(880, 400, volume=0.3, wave_type='sine')
    return pygame.mixer.Sound(buf)


def create_sound_win():
    """產生勝利「叮叮叮～」開心音樂"""
    if not SOUND_AVAILABLE:
        return DummySound()
    sample_rate = 22050
    total_duration = 1.2
    total_samples = int(sample_rate * total_duration)
    samples = []

    notes = [
        (523, 0.0, 0.15),    # C5
        (659, 0.15, 0.30),   # E5
        (784, 0.30, 0.45),   # G5
        (1047, 0.45, 0.70),  # C6 (長一點)
        (1175, 0.70, 0.85),  # D6
        (1047, 0.85, 1.15),  # C6 (結尾)
    ]

    for i in range(total_samples):
        t = i / sample_rate
        value = 0.0
        for freq, start, end in notes:
            if start <= t < end:
                local_t = t - start
                dur = end - start
                env = 1.0
                # 短淡入
                if local_t < 0.02:
                    env = local_t / 0.02
                # 淡出
                if local_t > dur - 0.05:
                    env = (dur - local_t) / 0.05
                value = math.sin(2 * math.pi * freq * t) * env
                # 加一點泛音讓聲音更亮
                value += 0.3 * math.sin(2 * math.pi * freq * 2 * t) * env
                break

        # 全域淡出
        if i > total_samples - 500:
            value *= (total_samples - i) / 500

        samples.append(int(value * 0.35 * 32767))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(array.array('h', samples).tobytes())
    buf.seek(0)
    return pygame.mixer.Sound(buf)


def create_sound_fall():
    """產生跌倒「哇～」可愛下滑音效"""
    if not SOUND_AVAILABLE:
        return DummySound()
    sample_rate = 22050
    duration = 0.5
    total_samples = int(sample_rate * duration)
    samples = []

    for i in range(total_samples):
        t = i / sample_rate
        # 頻率從高滑到低
        freq = 600 - 400 * (t / duration)
        value = math.sin(2 * math.pi * freq * t)

        # 加一點顫音
        value *= 1.0 + 0.3 * math.sin(2 * math.pi * 8 * t)

        # 淡出
        env = 1.0 - (t / duration) * 0.7
        if i > total_samples - 300:
            env *= (total_samples - i) / 300

        samples.append(int(value * env * 0.35 * 32767))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(array.array('h', samples).tobytes())
    buf.seek(0)
    return pygame.mixer.Sound(buf)


def create_sound_step():
    """產生走路「噠」小腳步聲"""
    if not SOUND_AVAILABLE:
        return DummySound()
    buf = generate_wav_bytes(350, 80, volume=0.2, wave_type='square')
    return pygame.mixer.Sound(buf)


# ==================== 繪圖工具函式 ====================

def draw_rounded_rect(surface, color, rect, radius=10):
    """繪製圓角矩形"""
    x, y, w, h = rect
    # 確保 radius 不超過矩形一半
    radius = min(radius, w // 2, h // 2)
    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)


def draw_bunny(surface, x, y, facing_right=True, bouncing=False, fallen=False):
    """
    繪製可愛的小兔子角色 🐰
    x, y: 兔子的中心底部位置
    facing_right: 是否面向右邊
    bouncing: 是否在跳躍動畫中
    fallen: 是否跌倒了
    """
    # 跌倒的兔子（側躺）
    if fallen:
        # 身體（橫躺的橢圓）
        pygame.draw.ellipse(surface, WHITE, (x - 25, y - 25, 50, 30))
        pygame.draw.ellipse(surface, (220, 220, 220), (x - 25, y - 25, 50, 30), 2)
        # 頭
        pygame.draw.circle(surface, WHITE, (x + 20, y - 25), 15)
        # 耳朵（倒下的）
        pygame.draw.ellipse(surface, WHITE, (x + 15, y - 50, 8, 22))
        pygame.draw.ellipse(surface, PINK, (x + 17, y - 47, 4, 16))
        pygame.draw.ellipse(surface, WHITE, (x + 25, y - 48, 8, 22))
        pygame.draw.ellipse(surface, PINK, (x + 27, y - 45, 4, 16))
        # 眼睛（X_X 暈倒）
        pygame.draw.line(surface, BLACK, (x + 16, y - 29), (x + 22, y - 23), 2)
        pygame.draw.line(surface, BLACK, (x + 22, y - 29), (x + 16, y - 23), 2)
        pygame.draw.line(surface, BLACK, (x + 26, y - 29), (x + 32, y - 23), 2)
        pygame.draw.line(surface, BLACK, (x + 32, y - 29), (x + 26, y - 23), 2)
        # 嘴巴（波浪線）
        pygame.draw.arc(surface, DARK_PINK, (x + 18, y - 20, 12, 8), 0, math.pi, 2)
        # 小星星表示暈眩
        for angle_offset in [0, 72, 144, 216, 288]:
            angle = math.radians(angle_offset)
            sx = x + 35 + 8 * math.cos(angle)
            sy = y - 40 + 8 * math.sin(angle)
            pygame.draw.circle(surface, YELLOW, (int(sx), int(sy)), 2)
        return

    # 跳躍偏移
    bounce_offset = -8 if bouncing else 0

    # 身體
    body_y = y - 35 + bounce_offset
    pygame.draw.ellipse(surface, WHITE, (x - 18, body_y, 36, 35))
    pygame.draw.ellipse(surface, (230, 230, 230), (x - 18, body_y, 36, 35), 2)

    # 肚子（淺粉色）
    pygame.draw.ellipse(surface, (255, 240, 240), (x - 10, body_y + 10, 20, 18))

    # 頭
    head_y = body_y - 22
    pygame.draw.circle(surface, WHITE, (x, head_y), 20)
    pygame.draw.circle(surface, (230, 230, 230), (x, head_y), 20, 2)

    # 耳朵
    ear_offset = 8
    # 左耳
    pygame.draw.ellipse(surface, WHITE, (x - ear_offset - 6, head_y - 38, 12, 30))
    pygame.draw.ellipse(surface, PINK, (x - ear_offset - 3, head_y - 33, 6, 20))
    # 右耳
    pygame.draw.ellipse(surface, WHITE, (x + ear_offset - 6, head_y - 38, 12, 30))
    pygame.draw.ellipse(surface, PINK, (x + ear_offset - 3, head_y - 33, 6, 20))

    # 眼睛（大大圓圓的）
    eye_x_offset = 8 if facing_right else -8
    # 左眼
    pygame.draw.circle(surface, BLACK, (x - 7, head_y - 3), 5)
    pygame.draw.circle(surface, WHITE, (x - 6, head_y - 5), 2)  # 眼睛高光
    # 右眼
    pygame.draw.circle(surface, BLACK, (x + 7, head_y - 3), 5)
    pygame.draw.circle(surface, WHITE, (x + 8, head_y - 5), 2)  # 眼睛高光

    # 腮紅
    pygame.draw.circle(surface, (255, 180, 180), (x - 15, head_y + 5), 5)
    pygame.draw.circle(surface, (255, 180, 180), (x + 15, head_y + 5), 5)

    # 鼻子
    pygame.draw.circle(surface, PINK, (x, head_y + 2), 3)

    # 嘴巴（微笑）
    pygame.draw.arc(surface, DARK_PINK, (x - 6, head_y + 2, 12, 8), math.pi + 0.3, 2 * math.pi - 0.3, 2)

    # 小腳
    foot_y = y - 5 + bounce_offset
    pygame.draw.ellipse(surface, WHITE, (x - 14, foot_y, 12, 8))
    pygame.draw.ellipse(surface, WHITE, (x + 2, foot_y, 12, 8))

    # 小尾巴（圓球）
    tail_x = x - 16 if facing_right else x + 16
    pygame.draw.circle(surface, WHITE, (tail_x, body_y + 15), 6)
    pygame.draw.circle(surface, (230, 230, 230), (tail_x, body_y + 15), 6, 1)


def draw_doll(surface, x, y, is_red_light, time_val):
    """
    繪製娃娃姐姐（可愛卡通女孩）🎀
    is_red_light: True 時轉身（背面），False 時面向玩家
    """
    # 身體（漂亮的洋裝）
    dress_color = ORANGE if not is_red_light else (255, 130, 60)

    # 洋裝形狀（梯形）
    dress_points = [
        (x - 20, y - 50),
        (x + 20, y - 50),
        (x + 35, y + 10),
        (x - 35, y + 10),
    ]
    pygame.draw.polygon(surface, dress_color, dress_points)
    pygame.draw.polygon(surface, (200, 120, 40), dress_points, 2)

    # 洋裝裝飾（小花紋）
    pygame.draw.circle(surface, YELLOW, (x - 8, y - 30), 4)
    pygame.draw.circle(surface, YELLOW, (x + 8, y - 25), 4)
    pygame.draw.circle(surface, YELLOW, (x, y - 10), 4)

    # 腿
    pygame.draw.rect(surface, PEACH, (x - 12, y + 10, 8, 20))
    pygame.draw.rect(surface, PEACH, (x + 4, y + 10, 8, 20))
    # 鞋子
    pygame.draw.ellipse(surface, RED, (x - 15, y + 27, 14, 8))
    pygame.draw.ellipse(surface, RED, (x + 1, y + 27, 14, 8))

    # 頭
    head_y = y - 70
    pygame.draw.circle(surface, PEACH, (x, head_y), 25)

    # 頭髮
    pygame.draw.circle(surface, (80, 50, 30), (x, head_y - 5), 27)
    # 瀏海
    pygame.draw.ellipse(surface, (80, 50, 30), (x - 28, head_y - 20, 56, 20))
    # 兩側頭髮（雙馬尾）
    # 左馬尾
    pygame.draw.ellipse(surface, (80, 50, 30), (x - 38, head_y - 10, 16, 40))
    pygame.draw.circle(surface, RED, (x - 30, head_y - 8), 5)  # 髮飾
    # 右馬尾
    pygame.draw.ellipse(surface, (80, 50, 30), (x + 22, head_y - 10, 16, 40))
    pygame.draw.circle(surface, RED, (x + 30, head_y - 8), 5)  # 髮飾

    # 臉部朝前（綠燈時面對玩家，笑臉）
    if not is_red_light:
        # 前額露出
        pygame.draw.ellipse(surface, PEACH, (x - 18, head_y - 5, 36, 30))

        # 眼睛（大大可愛的）
        # 左眼
        pygame.draw.circle(surface, WHITE, (x - 10, head_y + 2), 8)
        pygame.draw.circle(surface, (60, 30, 10), (x - 10, head_y + 2), 5)
        pygame.draw.circle(surface, BLACK, (x - 10, head_y + 2), 3)
        pygame.draw.circle(surface, WHITE, (x - 8, head_y), 2)  # 高光
        # 右眼
        pygame.draw.circle(surface, WHITE, (x + 10, head_y + 2), 8)
        pygame.draw.circle(surface, (60, 30, 10), (x + 10, head_y + 2), 5)
        pygame.draw.circle(surface, BLACK, (x + 10, head_y + 2), 3)
        pygame.draw.circle(surface, WHITE, (x + 12, head_y), 2)  # 高光

        # 腮紅
        pygame.draw.circle(surface, (255, 170, 170), (x - 18, head_y + 10), 5)
        pygame.draw.circle(surface, (255, 170, 170), (x + 18, head_y + 10), 5)

        # 嘴巴（開心大笑）
        pygame.draw.arc(surface, DARK_PINK, (x - 8, head_y + 8, 16, 12),
                        math.pi + 0.2, 2 * math.pi - 0.2, 2)

        # 手（張開歡迎）
        # 左手
        pygame.draw.line(surface, PEACH, (x - 20, y - 45), (x - 45, y - 65), 5)
        pygame.draw.circle(surface, PEACH, (x - 45, y - 65), 6)
        # 右手
        pygame.draw.line(surface, PEACH, (x + 20, y - 45), (x + 45, y - 65), 5)
        pygame.draw.circle(surface, PEACH, (x + 45, y - 65), 6)

    else:
        # 背面（紅燈轉身）
        # 後腦勺 - 頭髮
        pygame.draw.circle(surface, (80, 50, 30), (x, head_y + 2), 22)

        # 頭髮細節
        for angle in range(-40, 41, 15):
            rad = math.radians(angle)
            hx = x + int(20 * math.sin(rad))
            hy = head_y - 5 + int(20 * math.cos(rad))
            pygame.draw.line(surface, (60, 35, 20), (x, head_y - 10), (hx, hy), 1)

        # 手放後面
        pygame.draw.line(surface, PEACH, (x - 18, y - 45), (x - 8, y - 30), 5)
        pygame.draw.line(surface, PEACH, (x + 18, y - 45), (x + 8, y - 30), 5)

    # 頭頂蝴蝶結
    bow_y = head_y - 25
    pygame.draw.polygon(surface, RED, [
        (x, bow_y), (x - 12, bow_y - 8), (x - 4, bow_y)
    ])
    pygame.draw.polygon(surface, RED, [
        (x, bow_y), (x + 12, bow_y - 8), (x + 4, bow_y)
    ])
    pygame.draw.circle(surface, DARK_PINK, (x, bow_y), 3)


def draw_background(surface, is_green):
    """繪製可愛的背景（天空 + 草地 + 雲朵 + 花朵）"""
    # 天空漸層（上淺藍到下方）
    if is_green:
        top_color = (180, 230, 255)
        bottom_color = LIGHT_GREEN
    else:
        top_color = (255, 200, 200)
        bottom_color = (255, 230, 220)

    for y_pos in range(SCREEN_HEIGHT):
        ratio = y_pos / SCREEN_HEIGHT
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y_pos), (SCREEN_WIDTH, y_pos))

    # 草地
    pygame.draw.rect(surface, GRASS_GREEN, (0, 460, SCREEN_WIDTH, 140))
    # 草地上的小花紋
    for gx in range(0, SCREEN_WIDTH, 30):
        height = random.randint(5, 15)
        pygame.draw.line(surface, DARK_GREEN, (gx, 460), (gx + 3, 460 - height), 2)

    # 道路
    pygame.draw.rect(surface, (210, 190, 160), (0, 440, SCREEN_WIDTH, 50))
    # 道路虛線
    for lx in range(0, SCREEN_WIDTH, 40):
        pygame.draw.rect(surface, WHITE, (lx, 462, 20, 4))

    # 雲朵
    draw_cloud(surface, 120, 60)
    draw_cloud(surface, 350, 40)
    draw_cloud(surface, 600, 70)
    draw_cloud(surface, 750, 30)

    # 小花朵裝飾
    flower_positions = [(50, 475), (150, 485), (280, 478), (420, 482),
                        (550, 476), (650, 488), (730, 479)]
    flower_colors = [RED, YELLOW, PINK, PURPLE, ORANGE, BLUE, DARK_PINK]
    for i, (fx, fy) in enumerate(flower_positions):
        color = flower_colors[i % len(flower_colors)]
        draw_flower(surface, fx, fy, color)


def draw_cloud(surface, x, y):
    """繪製可愛的雲朵 ☁️"""
    pygame.draw.circle(surface, WHITE, (x, y), 20)
    pygame.draw.circle(surface, WHITE, (x + 18, y - 5), 25)
    pygame.draw.circle(surface, WHITE, (x + 40, y), 20)
    pygame.draw.circle(surface, WHITE, (x + 20, y + 5), 22)


def draw_flower(surface, x, y, color):
    """繪製小花朵 🌸"""
    # 花瓣
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        px = x + int(6 * math.cos(rad))
        py = y + int(6 * math.sin(rad))
        pygame.draw.circle(surface, color, (px, py), 4)
    # 花心
    pygame.draw.circle(surface, YELLOW, (x, y), 3)
    # 莖
    pygame.draw.line(surface, DARK_GREEN, (x, y + 5), (x, y + 15), 2)


def draw_finish_line(surface, x):
    """繪製終點線（彩色旗幟）🏁"""
    # 旗桿
    pygame.draw.line(surface, BROWN, (x, 350), (x, 490), 4)

    # 棋盤格旗幟
    flag_w = 40
    flag_h = 50
    cell_size = 10
    for row in range(flag_h // cell_size):
        for col in range(flag_w // cell_size):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(surface, color,
                             (x + 2 + col * cell_size, 350 + row * cell_size,
                              cell_size, cell_size))

    # 「終點」文字
    pygame.draw.rect(surface, GOLD, (x - 15, 340, 70, 20), border_radius=5)
    return (x - 15, 340, 70, 20)  # 回傳位置供文字使用


def draw_start_line(surface, x):
    """繪製起跑線"""
    pygame.draw.line(surface, WHITE, (x, 440), (x, 490), 3)
    # 虛線裝飾
    for dy in range(440, 490, 8):
        pygame.draw.rect(surface, YELLOW, (x - 1, dy, 3, 4))


# ==================== 粒子效果（煙火、彩帶）====================

class Particle:
    """彩帶/煙火粒子"""
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color or random.choice(CONFETTI_COLORS)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-8, -2)
        self.gravity = 0.15
        self.life = random.randint(40, 80)
        self.size = random.randint(3, 7)
        self.shape = random.choice(['circle', 'rect', 'star'])
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.rotation += self.rot_speed

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = min(255, self.life * 4)
        if self.shape == 'circle':
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        elif self.shape == 'rect':
            rect_surf = pygame.Surface((self.size * 2, self.size), pygame.SRCALPHA)
            rect_surf.fill((*self.color, alpha))
            rotated = pygame.transform.rotate(rect_surf, self.rotation)
            surface.blit(rotated, (int(self.x) - rotated.get_width() // 2,
                                   int(self.y) - rotated.get_height() // 2))
        else:  # star
            draw_star(surface, self.color, int(self.x), int(self.y), self.size)

    @property
    def alive(self):
        return self.life > 0


def draw_star(surface, color, x, y, size):
    """繪製小星星 ⭐"""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = size if i % 2 == 0 else size // 2
        points.append((x + int(r * math.cos(angle)), y + int(r * math.sin(angle))))
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, points)


# ==================== 主遊戲類別 ====================

class Game:
    """兒童版一二三木頭人遊戲主類別"""

    def __init__(self):
        """初始化遊戲"""
        global SOUND_AVAILABLE
        pygame.init()

        # 嘗試初始化音效模組（某些系統可能不支援）
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            SOUND_AVAILABLE = True
            print("🔊 音效模組載入成功！")
        except Exception as e:
            SOUND_AVAILABLE = False
            print(f"🔇 音效模組無法載入（{e}），遊戲將以靜音模式執行")
            print("   （不影響遊玩，一樣很好玩喔！）")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🐰 一二三木頭人！Red Light Green Light 🚦")
        self.clock = pygame.time.Clock()

        # 字型設定（嘗試使用系統字型，找不到就用預設）
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_tiny = None
        self._setup_fonts()

        # 音效（如果 mixer 不可用，會自動使用 DummySound）
        self.sound_go = create_sound_go()
        self.sound_stop = create_sound_stop()
        self.sound_win = create_sound_win()
        self.sound_fall = create_sound_fall()
        self.sound_step = create_sound_step()

        # 遊戲狀態
        self.state = "START"  # START, PLAYING, FALLEN, WIN
        self.score = 0        # 勝利次數

        # 角色位置
        self.player_x = PLAYER_START_X
        self.player_bouncing = False
        self.bounce_timer = 0
        self.player_fallen = False

        # 紅綠燈
        self.is_green_light = True      # True = 綠燈, False = 紅燈
        self.light_timer = 0.0          # 計時器
        self.light_duration = 5.0       # 目前這輪的持續時間
        self.moved_during_red = False   # 紅燈時是否移動了

        # 粒子效果
        self.particles = []

        # 動畫計時器
        self.anim_timer = 0
        self.message_timer = 0
        self.message_text = ""

        # 預先繪製靜態背景（節省效能）
        self.bg_green = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bg_red = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # 因為背景有隨機元素，先設定種子讓兩張背景的花草位置一樣
        random.seed(42)
        draw_background(self.bg_green, True)
        random.seed(42)
        draw_background(self.bg_red, False)
        random.seed()  # 恢復隨機

    def _setup_fonts(self):
        """設定字型 —— 嘗試找到支援中文的字型"""
        # 嘗試常見的中文字型
        chinese_fonts = [
            "notosanscjk", "notosanstc", "notosanssc",
            "wenquanyimicrohei", "wenquanyizenhei",
            "droidsansfallback", "arplumingcn",
            "microsoftjhenghei", "microsoftyahei",
            "pingfang", "heiti", "simhei", "simsun",
            "noto sans cjk tc", "noto sans cjk sc",
        ]

        font_name = None
        available = pygame.font.get_fonts()
        for f in chinese_fonts:
            for af in available:
                if f.replace(" ", "") in af.replace(" ", ""):
                    font_name = af
                    break
            if font_name:
                break

        if font_name:
            try:
                self.font_large = pygame.font.SysFont(font_name, 52, bold=True)
                self.font_medium = pygame.font.SysFont(font_name, 36, bold=True)
                self.font_small = pygame.font.SysFont(font_name, 26)
                self.font_tiny = pygame.font.SysFont(font_name, 20)
            except Exception:
                font_name = None

        if not font_name:
            # 使用預設字型
            self.font_large = pygame.font.Font(None, 60)
            self.font_medium = pygame.font.Font(None, 42)
            self.font_small = pygame.font.Font(None, 30)
            self.font_tiny = pygame.font.Font(None, 24)

    def reset_round(self):
        """重置一輪遊戲（角色回到起點）"""
        self.player_x = PLAYER_START_X
        self.player_bouncing = False
        self.player_fallen = False
        self.is_green_light = True
        self.light_timer = 0.0
        self.light_duration = random.uniform(LIGHT_MIN_TIME, LIGHT_MAX_TIME)
        self.moved_during_red = False
        self.particles = []
        self.state = "PLAYING"

    def handle_move(self):
        """處理玩家按下前進鍵"""
        if self.state != "PLAYING":
            return

        if self.is_green_light:
            # 綠燈：可以前進！
            self.player_x += PLAYER_STEP
            self.player_bouncing = True
            self.bounce_timer = 8
            self.sound_step.play()

            # 檢查是否到達終點
            if self.player_x >= FINISH_LINE_X:
                self.player_x = FINISH_LINE_X
                self.state = "WIN"
                self.score += 1
                self.sound_win.play()
                self.anim_timer = 0
                # 產生大量慶祝粒子
                for _ in range(80):
                    self.particles.append(
                        Particle(
                            random.randint(100, 700),
                            random.randint(50, 300)
                        )
                    )
        else:
            # 紅燈：不可以動！被抓到了！
            self.moved_during_red = True
            self.player_fallen = True
            self.state = "FALLEN"
            self.sound_fall.play()
            self.message_timer = 150  # 顯示訊息的幀數
            self.message_text = ""

    def update_lights(self, dt):
        """更新紅綠燈計時"""
        if self.state != "PLAYING":
            return

        self.light_timer += dt

        if self.light_timer >= self.light_duration:
            # 切換紅綠燈
            self.is_green_light = not self.is_green_light
            self.light_timer = 0.0
            self.light_duration = random.uniform(LIGHT_MIN_TIME, LIGHT_MAX_TIME)

            if self.is_green_light:
                self.sound_go.play()
            else:
                self.sound_stop.play()

    def update_particles(self):
        """更新所有粒子"""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def update(self, dt):
        """每幀更新遊戲邏輯"""
        self.anim_timer += 1

        # 更新彈跳動畫
        if self.bounce_timer > 0:
            self.bounce_timer -= 1
        else:
            self.player_bouncing = False

        # 更新粒子
        self.update_particles()

        if self.state == "PLAYING":
            self.update_lights(dt)

        elif self.state == "FALLEN":
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.reset_round()

        elif self.state == "WIN":
            # 持續產生慶祝粒子
            if self.anim_timer % 5 == 0:
                self.particles.append(
                    Particle(
                        random.randint(50, 750),
                        random.randint(0, 200)
                    )
                )

    def draw_text_with_shadow(self, text, font, color, x, y, shadow_color=BLACK, center=True):
        """繪製帶陰影的文字"""
        # 陰影
        shadow = font.render(text, True, shadow_color)
        # 主文字
        main = font.render(text, True, color)

        if center:
            shadow_rect = shadow.get_rect(center=(x + 2, y + 2))
            main_rect = main.get_rect(center=(x, y))
        else:
            shadow_rect = shadow.get_rect(topleft=(x + 2, y + 2))
            main_rect = main.get_rect(topleft=(x, y))

        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(main, main_rect)

    def draw_start_screen(self):
        """繪製開始畫面"""
        # 漸層背景
        for y_pos in range(SCREEN_HEIGHT):
            ratio = y_pos / SCREEN_HEIGHT
            r = int(255 - 80 * ratio)
            g = int(220 - 40 * ratio)
            b = int(255 - 20 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y_pos), (SCREEN_WIDTH, y_pos))

        # 標題裝飾 —— 大彩虹圓弧
        colors_rainbow = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK]
        for i, c in enumerate(colors_rainbow):
            pygame.draw.arc(self.screen, c,
                            (150, 20 + i * 8, 500, 200 - i * 8),
                            0.1, math.pi - 0.1, 4)

        # 遊戲標題
        self.draw_text_with_shadow("一二三 木頭人！", self.font_large,
                                   YELLOW, 400, 150, (180, 120, 0))
        self.draw_text_with_shadow("Red Light, Green Light", self.font_small,
                                   WHITE, 400, 200, (100, 100, 100))

        # 可愛的兔子
        draw_bunny(self.screen, 300, 380)

        # 可愛的娃娃
        draw_doll(self.screen, 500, 370, False, self.anim_timer)

        # 閃爍的開始提示
        if (self.anim_timer // 30) % 2 == 0:
            self.draw_text_with_shadow("Press SPACE to Start!",
                                       self.font_medium, WHITE, 400, 460,
                                       (80, 80, 80))
            self.draw_text_with_shadow("按空格鍵開始玩喔～",
                                       self.font_small, PINK, 400, 510,
                                       (150, 80, 100))

        # 操作說明
        self.draw_text_with_shadow("Space / Click = Move Forward",
                                   self.font_tiny, (180, 180, 220), 400, 560)

        # 裝飾星星
        for i in range(8):
            angle = self.anim_timer * 0.02 + i * math.pi / 4
            sx = 400 + int(250 * math.cos(angle))
            sy = 300 + int(150 * math.sin(angle))
            star_color = CONFETTI_COLORS[i % len(CONFETTI_COLORS)]
            draw_star(self.screen, star_color, sx, sy, 6)

    def draw_playing_screen(self):
        """繪製遊戲進行中的畫面"""
        # 背景
        if self.is_green_light:
            self.screen.blit(self.bg_green, (0, 0))
        else:
            self.screen.blit(self.bg_red, (0, 0))

        # 起跑線
        draw_start_line(self.screen, PLAYER_START_X)

        # 終點線
        finish_rect = draw_finish_line(self.screen, FINISH_LINE_X)
        self.draw_text_with_shadow("GOAL!", self.font_tiny, WHITE,
                                   finish_rect[0] + finish_rect[2] // 2,
                                   finish_rect[1] + finish_rect[3] // 2)

        # 娃娃姐姐（位於畫面中間偏右上方）
        doll_x = 550
        doll_y = 400
        draw_doll(self.screen, doll_x, doll_y, not self.is_green_light, self.anim_timer)

        # 兔子角色
        draw_bunny(self.screen, int(self.player_x), PLAYER_Y,
                   facing_right=True, bouncing=self.player_bouncing,
                   fallen=self.player_fallen)

        # 上方狀態列
        status_height = 80
        if self.is_green_light:
            status_color = (50, 180, 50, 200)
            status_text = "GO GO GO!"
            status_chinese = "綠燈！快跑呀～"
            text_color = WHITE
        else:
            status_color = (220, 60, 60, 200)
            status_text = "STOP!"
            status_chinese = "紅燈！停下來～"
            text_color = WHITE

        # 半透明狀態列
        status_surf = pygame.Surface((SCREEN_WIDTH, status_height), pygame.SRCALPHA)
        s_color = (50, 180, 50) if self.is_green_light else (220, 60, 60)
        status_surf.fill((*s_color, 180))
        self.screen.blit(status_surf, (0, 0))

        # 紅綠燈圖示
        light_x = 50
        light_y = 40
        # 燈座
        pygame.draw.rect(self.screen, (60, 60, 60), (light_x - 15, light_y - 25, 30, 50),
                         border_radius=8)
        # 綠燈
        green_on = (0, 255, 0) if self.is_green_light else (0, 80, 0)
        pygame.draw.circle(self.screen, green_on, (light_x, light_y - 10), 8)
        # 紅燈
        red_on = (255, 0, 0) if not self.is_green_light else (80, 0, 0)
        pygame.draw.circle(self.screen, red_on, (light_x, light_y + 10), 8)

        # 狀態文字
        self.draw_text_with_shadow(status_text, self.font_large, text_color,
                                   SCREEN_WIDTH // 2, 28, (0, 0, 0))
        self.draw_text_with_shadow(status_chinese, self.font_small, YELLOW,
                                   SCREEN_WIDTH // 2, 60, (100, 80, 0))

        # 進度條
        progress = (self.player_x - PLAYER_START_X) / (FINISH_LINE_X - PLAYER_START_X)
        progress = max(0, min(1, progress))
        bar_x = 100
        bar_y = SCREEN_HEIGHT - 30
        bar_w = SCREEN_WIDTH - 200
        bar_h = 16
        # 背景
        pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=8)
        # 進度
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            rainbow_color = (
                int(100 + 155 * progress),
                int(200 - 100 * progress),
                int(50 + 200 * (1 - progress))
            )
            pygame.draw.rect(self.screen, rainbow_color, (bar_x, bar_y, fill_w, bar_h),
                             border_radius=8)
        # 進度文字
        percent_text = f"{int(progress * 100)}%"
        self.draw_text_with_shadow(percent_text, self.font_tiny, WHITE,
                                   bar_x + bar_w // 2, bar_y + bar_h // 2)

        # 分數顯示
        score_text = f"Score: {self.score}"
        self.draw_text_with_shadow(score_text, self.font_tiny, GOLD,
                                   SCREEN_WIDTH - 60, SCREEN_HEIGHT - 25)

    def draw_fallen_screen(self):
        """繪製跌倒畫面"""
        # 先畫遊戲畫面
        self.screen.blit(self.bg_red, (0, 0))
        draw_start_line(self.screen, PLAYER_START_X)
        draw_finish_line(self.screen, FINISH_LINE_X)
        draw_doll(self.screen, 550, 400, True, self.anim_timer)

        # 跌倒的兔子
        draw_bunny(self.screen, int(self.player_x), PLAYER_Y,
                   fallen=True)

        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 200, 200, 120))
        self.screen.blit(overlay, (0, 0))

        # 可愛的失敗訊息（鼓勵性質）
        # 訊息框
        msg_rect = (150, 150, 500, 250)
        draw_rounded_rect(self.screen, WHITE, msg_rect, 20)
        pygame.draw.rect(self.screen, PINK,
                         (msg_rect[0], msg_rect[1], msg_rect[2], msg_rect[3]),
                         3, border_radius=20)

        self.draw_text_with_shadow("Oops!", self.font_large, ORANGE, 400, 210, BROWN)
        self.draw_text_with_shadow("哎呀～ 被發現了！", self.font_medium, DARK_PINK, 400, 270)
        self.draw_text_with_shadow("沒關係，再試一次！加油喔～",
                                   self.font_small, (100, 100, 150), 400, 320)

        # 可愛表情符號裝飾
        draw_star(self.screen, YELLOW, 200, 180, 12)
        draw_star(self.screen, PINK, 600, 180, 12)
        draw_star(self.screen, ORANGE, 180, 350, 10)
        draw_star(self.screen, PURPLE, 620, 350, 10)

    def draw_win_screen(self):
        """繪製勝利畫面"""
        # 繽紛背景
        for y_pos in range(SCREEN_HEIGHT):
            ratio = y_pos / SCREEN_HEIGHT
            r = int(255 - 60 * ratio)
            g = int(250 - 30 * ratio)
            b = int(200 + 55 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y_pos), (SCREEN_WIDTH, y_pos))

        # 草地
        pygame.draw.rect(self.screen, GRASS_GREEN, (0, 460, SCREEN_WIDTH, 140))

        # 跳舞的兔子（使用動畫效果）
        bunny_y = PLAYER_Y + int(10 * math.sin(self.anim_timer * 0.1))
        bounce = (self.anim_timer // 10) % 2 == 0
        draw_bunny(self.screen, FINISH_LINE_X - 30, bunny_y,
                   facing_right=True, bouncing=bounce)

        # 粒子效果（彩帶煙火）
        for p in self.particles:
            p.draw(self.screen)

        # 勝利訊息框
        msg_rect = (100, 80, 600, 300)
        draw_rounded_rect(self.screen, (255, 255, 255), msg_rect, 25)
        pygame.draw.rect(self.screen, GOLD,
                         (msg_rect[0], msg_rect[1], msg_rect[2], msg_rect[3]),
                         4, border_radius=25)

        # 勝利文字
        self.draw_text_with_shadow("YOU WIN!", self.font_large, GOLD, 400, 140, BROWN)
        self.draw_text_with_shadow("太棒了！你贏啦！耶～",
                                   self.font_medium, DARK_PINK, 400, 200)

        # 分數
        score_msg = f"You won {self.score} time(s)! Amazing!"
        self.draw_text_with_shadow(score_msg, self.font_small, PURPLE, 400, 260)
        score_chinese = f"你已經贏了 {self.score} 次！超厲害！"
        self.draw_text_with_shadow(score_chinese, self.font_small, ORANGE, 400, 300)

        # 重玩提示（閃爍）
        if (self.anim_timer // 25) % 2 == 0:
            self.draw_text_with_shadow("Press R to Play Again!",
                                       self.font_medium, WHITE, 400, 420, (80, 80, 80))
            self.draw_text_with_shadow("按 R 再玩一次！",
                                       self.font_small, PINK, 400, 470)

        # 裝飾的大星星
        for i in range(12):
            angle = self.anim_timer * 0.03 + i * math.pi / 6
            dist = 200 + 50 * math.sin(self.anim_timer * 0.05 + i)
            sx = 400 + int(dist * math.cos(angle))
            sy = 300 + int(dist * 0.6 * math.sin(angle))
            if 0 < sx < SCREEN_WIDTH and 0 < sy < SCREEN_HEIGHT:
                star_color = CONFETTI_COLORS[i % len(CONFETTI_COLORS)]
                size = 5 + int(3 * math.sin(self.anim_timer * 0.08 + i))
                draw_star(self.screen, star_color, sx, sy, size)

    def draw(self):
        """主繪圖函式 —— 根據遊戲狀態繪製不同畫面"""
        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PLAYING":
            self.draw_playing_screen()
        elif self.state == "FALLEN":
            self.draw_fallen_screen()
        elif self.state == "WIN":
            self.draw_win_screen()

        pygame.display.flip()

    def run(self):
        """遊戲主迴圈"""
        running = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0  # 取得每幀間隔（秒）

            # ===== 事件處理 =====
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_SPACE:
                        if self.state == "START":
                            self.reset_round()
                            self.sound_go.play()
                        elif self.state == "PLAYING":
                            self.handle_move()

                    elif event.key == pygame.K_r:
                        if self.state == "WIN":
                            self.reset_round()
                            self.sound_go.play()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左鍵
                        if self.state == "START":
                            self.reset_round()
                            self.sound_go.play()
                        elif self.state == "PLAYING":
                            self.handle_move()

            # ===== 更新 =====
            self.update(dt)

            # ===== 繪圖 =====
            self.draw()

        pygame.quit()
        sys.exit()


# ==================== 程式進入點 ====================

if __name__ == "__main__":
    print("🐰 歡迎來到「一二三木頭人」兒童版！")
    print("🎮 操作方式：按空格鍵或滑鼠左鍵讓小兔子往前跑")
    print("🟢 綠燈時可以跑，🔴 紅燈時要停下來喔！")
    print("🏁 跑到終點就贏啦！加油～")
    print("=" * 50)

    game = Game()
    game.run()
